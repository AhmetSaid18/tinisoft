"""
Authentication views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from apps.serializers.auth import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    TenantSerializer,
)
from apps.services.auth_service import AuthService
from apps.models import Tenant
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Kullanıcı ve mağaza kaydı.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "password123",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+905551234567",
        "store_name": "My Store",
        "store_slug": "my-store",
        "custom_domain": "example.com",  # Opsiyonel
        "template": "modern"  # Sadece custom_domain varsa seçilebilir
    }
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        try:
            result = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Kayıt başarılı! Mağazanız oluşturuldu.',
                'user': UserSerializer(result['user']).data,
                'tenant': TenantSerializer(result['tenant']).data,
                'subdomain_url': result['subdomain_url'],
                'custom_domain': result['custom_domain'],
                'custom_domain_id': result.get('custom_domain_id'),  # Domain ID (verify için)
                'verification_code': result.get('verification_code'),
                'template': result.get('template', 'default'),  # Frontend template adı (custom domain varsa seçilen, yoksa 'default')
                'template_note': (
                    'Custom domain ile seçilen template kullanılacak.'
                    if result.get('custom_domain') else
                    'Subdomain bizim template (default) ile yayınlanacak.'
                ),
                'verification_instructions': (
                    f"Custom domain için DNS kaydı ekleyin:\n"
                    f"TXT: tinisoft-verify={result.get('verification_code', '')}\n"
                    f"veya CNAME: tinisoft-verify.{result.get('custom_domain', '')} → verify.tinisoft.com.tr"
                ) if result.get('custom_domain') else None,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            return Response({
                'success': False,
                'message': 'Kayıt sırasında bir hata oluştu.',
                'error': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': False,
        'errors': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Kullanıcı girişi.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    # Request body kontrolü
    if not request.data:
        return Response({
            'success': False,
            'message': 'Email ve şifre gereklidir.',
            'error_code': 'VALIDATION_ERROR',
            'errors': {
                'email': ['Bu alan gereklidir.'],
                'password': ['Bu alan gereklidir.'],
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        try:
            result = AuthService.login(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
            )
            
            return Response({
                'success': True,
                'message': 'Giriş başarılı!',
                'token': result.get('token'),
                'user': UserSerializer(result['user']).data,
                'tenant': TenantSerializer(result['tenant']).data if result['tenant'] else None,
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({
                'success': False,
                'message': str(e),
                'error_code': 'AUTHENTICATION_FAILED',
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return Response({
                'success': False,
                'message': 'Giriş sırasında bir hata oluştu.',
                'error_code': 'INTERNAL_ERROR',
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Serializer validation errors
    return Response({
        'success': False,
        'message': 'Geçersiz giriş bilgileri.',
        'error_code': 'VALIDATION_ERROR',
        'errors': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def tenant_detail(request):
    """
    Tenant bilgilerini getir (GET) veya güncelle (PATCH).
    
    GET: /api/tenant/
    PATCH: /api/tenant/
    
    Request body (PATCH):
    {
        "custom_domain": "example.com",  # Custom domain güncelle (doğrulama gerektirmez)
        "name": "Mağaza Adı",  # Opsiyonel
        "template": "modern"  # Opsiyonel
    }
    
    Owner: Kendi tenant'ını görebilir/güncelleyebilir.
    TenantOwner: Kendi tenant'ını görebilir/güncelleyebilir.
    """
    # Tenant'ı bul
    if request.user.is_owner:
        # Owner ise owned_tenants'dan ilkini al (genelde bir tane olur)
        tenant = request.user.owned_tenants.filter(is_deleted=False).first()
        if not tenant:
            return Response({
                'success': False,
                'message': 'Tenant bulunamadı.',
                'error_code': 'TENANT_NOT_FOUND',
            }, status=status.HTTP_404_NOT_FOUND)
    elif request.user.is_tenant_owner:
        tenant = request.user.tenant
        if not tenant:
            return Response({
                'success': False,
                'message': 'Tenant bilginiz bulunamadı.',
                'error_code': 'TENANT_NOT_FOUND',
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
            'error_code': 'PERMISSION_DENIED',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = TenantSerializer(tenant)
        return Response({
            'success': True,
            'tenant': serializer.data,
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        serializer = TenantSerializer(
            tenant,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            
            logger.info(f"Tenant updated: {tenant.slug} by user {request.user.email}")
            
            return Response({
                'success': True,
                'message': 'Tenant bilgileri güncellendi.',
                'tenant': serializer.data,
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Tenant güncellenemedi.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Giriş yapmış kullanıcının kendi profil bilgilerini getirmesi veya güncellemesi.
    
    GET: /api/auth/profile/
    PATCH: /api/auth/profile/
    
    Request body (PATCH):
    {
        "first_name": "Yeni Ad",
        "last_name": "Yeni Soyad",
        "phone": "+90555...",
        "password": "yeni-guclu-sifre"  # Opsiyonel
    }
    """
    user = request.user
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response({
            'success': True,
            'user': serializer.data
        })
    
    elif request.method == 'PATCH':
        # Şifre güncelleme kontrolü
        password = request.data.get('password')
        if password:
            if len(password) < 8:
                return Response({
                    'success': False,
                    'message': 'Şifre en az 8 karakter olmalıdır.'
                }, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(password)
            user.save()
            
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            logger.info(f"User profile updated: {user.email}")
            
            return Response({
                'success': True,
                'message': 'Profil bilgileriniz güncellendi.',
                'user': serializer.data
            })
            
        return Response({
            'success': False,
            'message': 'Profil güncellenemedi.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
