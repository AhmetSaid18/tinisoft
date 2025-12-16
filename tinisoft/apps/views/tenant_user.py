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
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_tenant_user(request, tenant_slug=None):
    """
    Tenant'ın sitesinde müşteri kaydı.
    
    URL: /api/tenant/{tenant_slug}/users/register/
    
    Request body:
    {
        "email": "customer@example.com",
        "password": "password123",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+905551234567"
    }
    """
    # Tenant'ı slug'dan bul
    if tenant_slug:
        try:
            tenant = Tenant.objects.get(slug=tenant_slug, status='active')
        except Tenant.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Mağaza bulunamadı.',
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        # Header'dan veya subdomain'den tenant bulunabilir
        # Şimdilik tenant_slug zorunlu
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
            result = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Kayıt başarılı!',
                'user': UserSerializer(result['user']).data,
                'tenant': TenantSerializer(result['tenant']).data,
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
            tenant = Tenant.objects.get(slug=tenant_slug, status='active')
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
            return Response({
                'success': True,
                'message': 'Giriş başarılı!',
                'user': UserSerializer(serializer.validated_data['user']).data,
                'tenant': TenantSerializer(serializer.validated_data['tenant']).data,
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

