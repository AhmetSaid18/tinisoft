"""
Authentication views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.serializers.auth import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    TenantSerializer,
)
from apps.services.auth_service import AuthService
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

