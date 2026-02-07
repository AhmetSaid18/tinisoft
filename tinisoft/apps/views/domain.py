"""
Domain management views.
Domain doğrulama ve yönetim işlemleri.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from apps.models import Domain, Tenant
from apps.services.domain_service import DomainService
from apps.tasks.domain_task import verify_domain_dns_task, deploy_domain_task
from apps.permissions import IsTenantOwnerOfObject, IsOwnerOrTenantOwner
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsOwnerOrTenantOwner])
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
    
    Sadece Owner veya TenantOwner erişebilir.
    TenantOwner sadece kendi tenant'ının domain'lerine erişebilir.
    """
    try:
        domain = Domain.objects.get(id=domain_id)
    except Domain.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Domain bulunamadı.',
            'error_code': 'DOMAIN_NOT_FOUND',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Object-level permission kontrolü
    # Owner her şeye erişebilir, TenantOwner sadece kendi tenant'ının domain'ine
    if request.user.is_tenant_owner and domain.tenant != request.user.tenant:
        raise PermissionDenied('Bu domain\'e erişim yetkiniz yok. Sadece kendi tenant\'ınızın domain\'lerine erişebilirsiniz.')
    
    # Verification code yoksa oluştur
    if not domain.verification_code:
        domain.verification_code = DomainService.generate_verification_code()
        domain.save()
    
    # DNS doğrulamasını başlat (async task)
    verify_domain_dns_task.delay(str(domain.id))
    
    return Response({
        'success': True,
        'message': 'Domain doğrulaması başlatıldı. DNS kayıtlarınızı eklediyseniz birkaç dakika içinde kontrol edilecek.',
        'domain': {
            'id': str(domain.id),
            'domain_name': domain.domain_name,
            'verification_status': 'verifying',
            'verification_code': domain.verification_code,
            'verification_instructions': DomainService.get_verification_instructions(domain),
        },
        'tenant': {
            'id': str(domain.tenant.id),
            'name': domain.tenant.name,
            'template': domain.tenant.template,  # Frontend template adı
        },
        'next_steps': [
            'DNS kayıtlarınızı eklediyseniz birkaç dakika bekleyin.',
            'Doğrulama tamamlandıktan sonra /api/domains/{domain_id}/deploy/ endpoint\'ini çağırarak yayınlama yapabilirsiniz.',
        ]
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsOwnerOrTenantOwner])
def domain_status(request, domain_id):
    """
    Domain durumunu kontrol et.
    
    URL: /api/domains/{domain_id}/status/
    
    Sadece Owner veya TenantOwner erişebilir.
    TenantOwner sadece kendi tenant'ının domain'lerine erişebilir.
    """
    try:
        domain = Domain.objects.get(id=domain_id)
    except Domain.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Domain bulunamadı.',
            'error_code': 'DOMAIN_NOT_FOUND',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Object-level permission kontrolü
    # Owner her şeye erişebilir, TenantOwner sadece kendi tenant'ının domain'ine
    if request.user.is_tenant_owner and domain.tenant != request.user.tenant:
        raise PermissionDenied('Bu domain\'e erişim yetkiniz yok. Sadece kendi tenant\'ınızın domain\'lerine erişebilirsiniz.')
    
    # Deployment durumunu kontrol et
    is_deployed = (
        domain.verification_status == 'verified' and
        domain.tenant.status == 'active' and
        bool(domain.traefik_router_name)
    )
    
    # Hata mesajları
    error_messages = []
    if domain.verification_status == 'pending':
        error_messages.append('Domain doğrulaması bekleniyor. DNS kayıtlarınızı ekleyin ve doğrulamayı başlatın.')
    elif domain.verification_status == 'verifying':
        error_messages.append('Domain doğrulaması devam ediyor. Birkaç dakika bekleyin.')
    elif domain.verification_status == 'failed':
        error_messages.append('Domain doğrulaması başarısız oldu. DNS kayıtlarınızı kontrol edin ve tekrar deneyin.')
    elif domain.verification_status == 'verified' and domain.tenant.status != 'active':
        error_messages.append('Domain doğrulandı ancak tenant aktif değil. Deployment işlemini başlatın.')
    elif domain.verification_status == 'verified' and not domain.traefik_router_name:
        error_messages.append('Domain doğrulandı ancak routing yapılandırılmamış. Deployment işlemini başlatın.')
    
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
            'verification_code': domain.verification_code if domain.verification_status in ['pending', 'failed'] else None,
            'verification_instructions': DomainService.get_verification_instructions(domain) if domain.verification_status in ['pending', 'failed'] else None,
        },
        'tenant': {
            'id': str(domain.tenant.id),
            'name': domain.tenant.name,
            'status': domain.tenant.status,
            'template': domain.tenant.template,  # Frontend template adı
        },
        'deployment': {
            'template': domain.tenant.template,  # Frontend build için template
            'frontend_url': f"https://{domain.domain_name}" if is_deployed else None,
            'ready': is_deployed,
            'traefik_router_name': domain.traefik_router_name,
            'traefik_service_name': domain.traefik_service_name,
        },
        'errors': error_messages,
        'actions': {
            'can_verify': domain.verification_status in ['pending', 'failed'],
            'can_retry_verification': domain.verification_status in ['pending', 'failed'],
            'can_deploy': domain.verification_status == 'verified' and not is_deployed,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_domain_by_code(request):
    """
    Domain DNS doğrulamasını verification_code ile başlat (public endpoint).
    
    URL: /api/domains/verify-by-code/
    
    Request body:
    {
        "domain_name": "influencermarket.com.tr",
        "verification_code": "dL74afpW2Y2afvAIZaujW2R0MNGsB82N"
    }
    """
    domain_name = request.data.get('domain_name')
    verification_code = request.data.get('verification_code')
    
    if not domain_name or not verification_code:
        return Response({
            'success': False,
            'message': 'domain_name ve verification_code gereklidir.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        domain = Domain.objects.get(
            domain_name=domain_name,
            verification_code=verification_code,
            verification_status='pending'
        )
    except Domain.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Domain bulunamadı veya verification code hatalı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verification code yoksa oluştur
    if not domain.verification_code:
        domain.verification_code = DomainService.generate_verification_code()
        domain.save()
    
    # DNS doğrulamasını başlat (async task)
    verify_domain_dns_task.delay(str(domain.id))
    
    return Response({
        'success': True,
        'message': 'Domain doğrulaması başlatıldı. DNS kayıtlarınızı eklediyseniz birkaç dakika içinde kontrol edilecek.',
        'domain': {
            'id': str(domain.id),
            'domain_name': domain.domain_name,
            'verification_status': 'verifying',
            'verification_code': domain.verification_code,
            'verification_instructions': DomainService.get_verification_instructions(domain),
        },
        'tenant': {
            'id': str(domain.tenant.id),
            'name': domain.tenant.name,
            'template': domain.tenant.template,
        },
        'next_steps': [
            'DNS kayıtlarınızı eklediyseniz birkaç dakika bekleyin.',
            'Doğrulama tamamlandıktan sonra /api/domains/{domain_id}/deploy/ endpoint\'ini çağırarak yayınlama yapabilirsiniz.',
        ]
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsOwnerOrTenantOwner])
def deploy_domain(request, domain_id):
    """
    Domain doğrulandıktan sonra manuel olarak yayınlama/deployment yap.
    
    URL: /api/domains/{domain_id}/deploy/
    
    Bu endpoint, domain doğrulandıktan sonra deployment işlemlerini başlatır:
    1. Tenant'ı aktif eder (eğer pending ise)
    2. Traefik routing ekler
    3. SSL sertifikası alır
    4. Frontend deploy eder
    
    Domain'in verification_status'u 'verified' olmalıdır.
    
    Sadece Owner veya TenantOwner erişebilir.
    TenantOwner sadece kendi tenant'ının domain'lerine erişebilir.
    """
    try:
        domain = Domain.objects.get(id=domain_id)
    except Domain.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Domain bulunamadı.',
            'error_code': 'DOMAIN_NOT_FOUND',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Object-level permission kontrolü
    # Owner her şeye erişebilir, TenantOwner sadece kendi tenant'ının domain'ine
    if request.user.is_tenant_owner and domain.tenant != request.user.tenant:
        raise PermissionDenied('Bu domain\'e erişim yetkiniz yok. Sadece kendi tenant\'ınızın domain\'lerine erişebilirsiniz.')
    
    # Domain doğrulanmış olmalı
    if domain.verification_status != 'verified':
        return Response({
            'success': False,
            'message': f'Domain henüz doğrulanmamış. Mevcut durum: {domain.verification_status}. Önce domain doğrulamasını tamamlayın.',
            'domain': {
                'id': str(domain.id),
                'domain_name': domain.domain_name,
                'verification_status': domain.verification_status,
                'verification_code': domain.verification_code,
                'verification_instructions': DomainService.get_verification_instructions(domain),
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Deployment işlemlerini başlat (async task)
    deploy_domain_task.delay(str(domain.id))
    
    return Response({
        'success': True,
        'message': 'Domain yayınlama işlemi başlatıldı. Birkaç dakika içinde tamamlanacak.',
        'domain': {
            'id': str(domain.id),
            'domain_name': domain.domain_name,
            'verification_status': domain.verification_status,
        },
        'tenant': {
            'id': str(domain.tenant.id),
            'name': domain.tenant.name,
            'status': domain.tenant.status,
            'template': domain.tenant.template,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsOwnerOrTenantOwner])
def retry_verification(request, domain_id):
    """
    Domain doğrulamasını tekrar dene.
    
    URL: /api/domains/{domain_id}/retry-verification/
    
    Domain'in verification_status'u 'pending' veya 'failed' olmalıdır.
    
    Sadece Owner veya TenantOwner erişebilir.
    TenantOwner sadece kendi tenant'ının domain'lerine erişebilir.
    """
    try:
        domain = Domain.objects.get(id=domain_id)
    except Domain.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Domain bulunamadı.',
            'error_code': 'DOMAIN_NOT_FOUND',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Object-level permission kontrolü
    # Owner her şeye erişebilir, TenantOwner sadece kendi tenant'ının domain'ine
    if request.user.is_tenant_owner and domain.tenant != request.user.tenant:
        raise PermissionDenied('Bu domain\'e erişim yetkiniz yok. Sadece kendi tenant\'ınızın domain\'lerine erişebilirsiniz.')
    
    # Sadece pending veya failed durumlarında retry yapılabilir
    if domain.verification_status not in ['pending', 'failed']:
        return Response({
            'success': False,
            'message': f'Domain zaten {domain.verification_status} durumunda. Retry yapılamaz.',
            'domain': {
                'id': str(domain.id),
                'domain_name': domain.domain_name,
                'verification_status': domain.verification_status,
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verification code yoksa oluştur
    if not domain.verification_code:
        domain.verification_code = DomainService.generate_verification_code()
        domain.save()
    
    # DNS doğrulamasını başlat (async task)
    verify_domain_dns_task.delay(str(domain.id))
    
    return Response({
        'success': True,
        'message': 'Domain doğrulaması tekrar başlatıldı. DNS kayıtlarınızı kontrol edin.',
        'domain': {
            'id': str(domain.id),
            'domain_name': domain.domain_name,
            'verification_status': 'verifying',
            'verification_code': domain.verification_code,
            'verification_instructions': DomainService.get_verification_instructions(domain),
        }
    }, status=status.HTTP_200_OK)


def create_domain(request):
    """
    Yeni domain ekle.
    
    URL: /api/domains/
    Method: POST
    
    Request body:
    {
        "domain_name": "example.com",
        "is_primary": false,
        "ssl_enabled": true
    }
    
    Owner: Herhangi bir tenant'a domain ekleyebilir.
    TenantOwner: Sadece kendi tenant'ına domain ekleyebilir.
    """
    domain_name = request.data.get('domain_name')
    tenant_id = request.data.get('tenant_id')
    is_primary = request.data.get('is_primary', False)
    ssl_enabled = request.data.get('ssl_enabled', True)
    
    if not domain_name:
        return Response({
            'success': False,
            'message': 'domain_name gereklidir.',
            'error_code': 'VALIDATION_ERROR',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Tenant belirleme
    if request.user.is_owner:
        # Owner ise tenant_id gerekli
        if not tenant_id:
            return Response({
                'success': False,
                'message': 'Owner için tenant_id gereklidir.',
                'error_code': 'VALIDATION_ERROR',
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Tenant bulunamadı.',
                'error_code': 'TENANT_NOT_FOUND',
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        # TenantOwner ise kendi tenant'ını kullan
        if not request.user.tenant:
            return Response({
                'success': False,
                'message': 'Tenant bilginiz bulunamadı.',
                'error_code': 'TENANT_NOT_FOUND',
            }, status=status.HTTP_400_BAD_REQUEST)
        tenant = request.user.tenant
    
    # Domain zaten var mı kontrol et
    if Domain.objects.filter(domain_name=domain_name).exists():
        return Response({
            'success': False,
            'message': 'Bu domain zaten kayıtlı.',
            'error_code': 'DOMAIN_EXISTS',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Primary domain kontrolü
    if is_primary:
        # Mevcut primary domain'i kaldır
        Domain.objects.filter(tenant=tenant, is_primary=True).update(is_primary=False)
    
    # Domain oluştur
    domain = Domain.objects.create(
        tenant=tenant,
        domain_name=domain_name,
        is_primary=is_primary,
        is_custom=True,  # Custom domain
        verification_status='pending',
        ssl_enabled=ssl_enabled,
    )
    
    # Verification code oluştur
    domain.verification_code = DomainService.generate_verification_code()
    domain.save()
    
    logger.info(f"Domain created: {domain.domain_name} for tenant: {tenant.name}")
    
    return Response({
        'success': True,
        'message': 'Domain başarıyla oluşturuldu. DNS kayıtlarınızı ekleyin ve doğrulamayı başlatın.',
        'domain': {
            'id': str(domain.id),
            'domain_name': domain.domain_name,
            'verification_status': domain.verification_status,
            'verification_code': domain.verification_code,
            'verification_instructions': DomainService.get_verification_instructions(domain),
        },
        'tenant': {
            'id': str(tenant.id),
            'name': tenant.name,
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsOwnerOrTenantOwner])
def list_domains(request):
    """
    Domain listele veya oluştur.
    
    GET /api/domains/ - Domain'leri listele
    POST /api/domains/ - Yeni domain oluştur
    
    Owner: Tüm domain'leri görebilir, herhangi bir tenant'a domain ekleyebilir.
    TenantOwner: Sadece kendi tenant'ının domain'lerini görebilir, sadece kendi tenant'ına domain ekleyebilir.
    """
    if request.method == 'POST':
        # Domain oluştur
        return create_domain(request)
    
    # GET: Domain'leri listele
    # Owner ise tüm domain'leri göster
    if request.user.is_owner:
        domains = Domain.objects.all().select_related('tenant')
    # TenantOwner ise sadece kendi tenant'ının domain'lerini göster
    elif request.user.is_tenant_owner:
        if not request.user.tenant:
            return Response({
                'success': False,
                'message': 'Tenant bilginiz bulunamadı.',
                'error_code': 'TENANT_NOT_FOUND',
            }, status=status.HTTP_400_BAD_REQUEST)
        domains = Domain.objects.filter(tenant=request.user.tenant).select_related('tenant')
    else:
        # Permission class zaten kontrol ediyor, buraya gelmemeli
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
            'error_code': 'PERMISSION_DENIED',
        }, status=status.HTTP_403_FORBIDDEN)
    
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
                'verified_at': domain.verified_at.isoformat() if domain.verified_at else None,
                'verification_code': domain.verification_code if domain.verification_status == 'pending' else None,
            }
            for domain in domains
        ]
    }, status=status.HTTP_200_OK)

