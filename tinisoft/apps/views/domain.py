"""
Domain management views.
Domain doğrulama ve yönetim işlemleri.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.models import Domain, Tenant
from apps.services.domain_service import DomainService
from apps.tasks.domain_task import verify_domain_dns_task, deploy_domain_task
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_domain(request, domain_id):
    """
    Domain DNS doğrulamasını başlat.
    
    URL: /api/domains/{domain_id}/verify/
    
    Domain'in DNS kayıtlarını kontrol eder ve doğrularsa:
    1. Domain status'u verified yapar
    2. Tenant'ı aktif eder (eğer ilk domain ise)
    3. Traefik routing ekler
    4. SSL sertifikası alır
    5. Frontend deploy eder
    """
    try:
        domain = Domain.objects.get(id=domain_id, tenant__owner=request.user)
    except Domain.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Domain bulunamadı veya yetkiniz yok.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # DNS doğrulamasını başlat (async task)
    verify_domain_dns_task.delay(str(domain.id))
    
    return Response({
        'success': True,
        'message': 'Domain doğrulaması başlatıldı. Birkaç dakika içinde kontrol edilecek.',
        'domain': {
            'id': str(domain.id),
            'domain_name': domain.domain_name,
            'verification_status': domain.verification_status,
            'verification_code': domain.verification_code,
            'verification_instructions': DomainService.get_verification_instructions(domain),
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def domain_status(request, domain_id):
    """
    Domain durumunu kontrol et.
    
    URL: /api/domains/{domain_id}/status/
    """
    try:
        domain = Domain.objects.get(id=domain_id, tenant__owner=request.user)
    except Domain.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Domain bulunamadı veya yetkiniz yok.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'success': True,
        'domain': {
            'id': str(domain.id),
            'domain_name': domain.domain_name,
            'verification_status': domain.verification_status,
            'is_primary': domain.is_primary,
            'is_custom': domain.is_custom,
            'ssl_enabled': domain.ssl_enabled,
            'verified_at': domain.verified_at.isoformat() if domain.verified_at else None,
            'last_checked_at': domain.last_checked_at.isoformat() if domain.last_checked_at else None,
        },
        'tenant': {
            'id': str(domain.tenant.id),
            'name': domain.tenant.name,
            'status': domain.tenant.status,
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_domains(request):
    """
    Kullanıcının tenant'larına ait domain'leri listele.
    
    URL: /api/domains/
    """
    # Owner ise owned_tenants, TenantUser ise tenant
    if request.user.is_owner:
        tenants = Tenant.objects.filter(owner=request.user)
    else:
        tenants = Tenant.objects.filter(id=request.user.tenant_id) if request.user.tenant else []
    
    domains = Domain.objects.filter(tenant__in=tenants).select_related('tenant')
    
    return Response({
        'success': True,
        'domains': [
            {
                'id': str(domain.id),
                'domain_name': domain.domain_name,
                'tenant_name': domain.tenant.name,
                'is_primary': domain.is_primary,
                'is_custom': domain.is_custom,
                'verification_status': domain.verification_status,
                'ssl_enabled': domain.ssl_enabled,
            }
            for domain in domains
        ]
    }, status=status.HTTP_200_OK)

