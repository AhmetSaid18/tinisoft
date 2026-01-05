"""
TenantUser views.
Tenant'ın sitesinde kayıt olan müşteriler için.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.serializers.tenant_user import (
    TenantUserRegisterSerializer,
    TenantUserLoginSerializer,
)
from apps.serializers.auth import UserSerializer, TenantSerializer
from apps.models import Tenant
from apps.services.tenant_user_service import TenantUserService
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_verification_code_tenant_user(request, tenant_slug=None):
    """
    Kayıt öncesi email doğrulama kodu gönder.
    
    URL: /api/tenant/{tenant_slug}/users/send-code/
    
    Request body:
    {
        "email": "customer@example.com"
    }
    """
    email = request.data.get('email')
    if not email:
        return Response({
            'success': False,
            'message': 'Email adresi gereklidir.',
        }, status=status.HTTP_400_BAD_REQUEST)

    # Tenant'ı bul
    try:
        tenant = Tenant.objects.get(slug=tenant_slug)
    except Tenant.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Mağaza bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)

    # Kod gönder
    result = TenantUserService.send_registration_code(tenant, email)
    
    if result.get('success'):
        return Response({
            'success': True,
            'message': 'Doğrulama kodu e-posta adresinize gönderildi.',
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': 'Kod gönderilirken bir hata oluştu.',
            'error': result.get('message'),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_tenant_user(request, tenant_slug=None):
    """
    Tenant'ın sitesinde müşteri kaydı.
    """
    # Tenant'ı slug'dan bul
    if tenant_slug:
        try:
            tenant = Tenant.objects.get(slug=tenant_slug)
        except Tenant.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Mağaza bulunamadı.',
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({
            'success': False,
            'message': 'Tenant slug gerekli.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = TenantUserRegisterSerializer(
        data=request.data,
        context={'tenant_id': str(tenant.id)}
    )
    
    if serializer.is_valid():
        try:
            serializer.save()
            return Response({
                'success': True,
                'message': 'Kayıt alındı. Lütfen e-posta adresinize gönderilen kodu girerek hesabınızı onaylayın.',
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"TenantUser registration failed: {str(e)}")
            return Response({
                'success': False,
                'message': 'Kayıt sırasında bir hata oluştu.',
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'errors': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_registration_tenant_user(request, tenant_slug=None):
    """
    Kayıt sonrası e-posta doğrulama.
    
    URL: /api/tenant/{tenant_slug}/users/verify/
    
    Request body:
    {
        "email": "customer@example.com",
        "code": "123456"
    }
    """
    email = request.data.get('email')
    code = request.data.get('code')
    
    if not email or not code:
        return Response({
            'success': False,
            'message': 'Email ve kod gereklidir.',
        }, status=status.HTTP_400_BAD_REQUEST)

    # Tenant'ı bul
    try:
        tenant = Tenant.objects.get(slug=tenant_slug)
    except Tenant.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Mağaza bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)

    # Kod doğrula
    is_valid, msg = TenantUserService.verify_registration_code(tenant, email, code)
    
    if not is_valid:
        return Response({
            'success': False,
            'message': msg,
        }, status=status.HTTP_400_BAD_REQUEST)

    # Kullanıcıyı bul ve aktif et
    try:
        user = User.objects.get(email=email, tenant=tenant)
        user.is_active = True
        user.save()
        
        # Giriş yap ve token üret
        from apps.utils.jwt_utils import generate_jwt_token
        token = generate_jwt_token(user)
        
        return Response({
            'success': True,
            'message': 'Hesabınız başarıyla doğrulandı!',
            'token': token,
            'user': UserSerializer(user).data,
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Kullanıcı bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_tenant_user(request, tenant_slug=None):
    """
    TenantUser girişi.
    
    URL: /api/tenant/{tenant_slug}/users/login/
    
    Request body:
    {
        "email": "customer@example.com",
        "password": "password123"
    }
    """
    # Tenant'ı slug'dan bul
    tenant_id = None
    if tenant_slug:
        try:
            # Müşteri girişi için de status'e göre filtreleme yapmıyoruz.
            tenant = Tenant.objects.get(slug=tenant_slug)
            tenant_id = str(tenant.id)
        except Tenant.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Mağaza bulunamadı.',
            }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = TenantUserLoginSerializer(
        data=request.data,
        context={'tenant_id': tenant_id}
    )
    
    if serializer.is_valid():
        try:
            from apps.utils.jwt_utils import generate_jwt_token
            
            user = serializer.validated_data['user']
            tenant = serializer.validated_data['tenant']
            
            # JWT token oluştur
            token = generate_jwt_token(user)
            
            return Response({
                'success': True,
                'message': 'Giriş başarılı!',
                'token': token,
                'user': UserSerializer(user).data,
                'tenant': TenantSerializer(tenant).data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"TenantUser login failed: {str(e)}")
            return Response({
                'success': False,
                'message': 'Giriş sırasında bir hata oluştu.',
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'errors': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)

