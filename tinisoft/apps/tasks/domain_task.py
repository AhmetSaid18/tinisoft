"""
Celery tasks for domain verification and deployment.
"""
from celery import shared_task
from apps.models import Domain, Tenant
from apps.services.domain_service import DomainService
from apps.services.traefik_service import TraefikService
from apps.services.ssl_service import SSLService
from apps.tasks.build_task import trigger_frontend_build
import logging

logger = logging.getLogger(__name__)


@shared_task
def verify_domain_dns_task(domain_id: str):
    """
    Domain DNS doğrulamasını yapar.
    Doğrulandıktan sonra deployment işlemlerini başlatır.
    """
    try:
        domain = Domain.objects.get(id=domain_id)
    except Domain.DoesNotExist:
        logger.error(f"Domain not found: {domain_id}")
        return
    
    # Sadece custom domain'ler için DNS doğrulama gerekli
    if not domain.is_custom:
        logger.info(f"Domain is subdomain, skipping DNS verification: {domain.domain_name}")
        return
    
    # DNS doğrulaması
    domain.verification_status = 'verifying'
    domain.save()
    
    is_verified = DomainService.verify_domain_dns(
        domain.domain_name,
        domain.verification_code
    )
    
    if is_verified:
        # Domain doğrulandı
        domain.verify()
        logger.info(f"Domain verified: {domain.domain_name}")
        
        # Deployment işlemlerini başlat
        deploy_domain_task.delay(str(domain.id))
    else:
        # Doğrulama başarısız
        domain.verification_status = 'failed'
        domain.save()
        logger.warning(f"Domain verification failed: {domain.domain_name}")
    
    return {
        'domain_id': domain_id,
        'domain_name': domain.domain_name,
        'verified': is_verified,
    }


@shared_task
def deploy_domain_task(domain_id: str):
    """
    Domain doğrulandıktan sonra deployment işlemlerini yapar:
    1. Tenant'ı aktif et (eğer ilk domain ise)
    2. Traefik routing ekle
    3. SSL sertifikası al
    4. Frontend deploy et
    """
    try:
        domain = Domain.objects.get(id=domain_id)
    except Domain.DoesNotExist:
        logger.error(f"Domain not found: {domain_id}")
        return
    
    tenant = domain.tenant
    
    # 1. Tenant'ı aktif et (eğer pending ise)
    if tenant.status == 'pending':
        tenant.activate()
        logger.info(f"Tenant activated: {tenant.name}")
    
    # 2. Traefik routing ekle
    try:
        TraefikService.add_domain_route(domain)
        logger.info(f"Traefik route added for: {domain.domain_name}")
    except Exception as e:
        logger.error(f"Failed to add Traefik route: {str(e)}")
    
    # 3. SSL sertifikası al (Let's Encrypt)
    if domain.ssl_enabled:
        try:
            SSLService.obtain_certificate(domain)
            logger.info(f"SSL certificate obtained for: {domain.domain_name}")
        except Exception as e:
            logger.error(f"Failed to obtain SSL certificate: {str(e)}")
    
    # 4. Frontend deploy et (template ile)
    try:
        trigger_frontend_build.delay(
            str(tenant.id),
            domain.domain_name,
            tenant.template  # Tenant'ın template'ini kullan
        )
        logger.info(f"Frontend build triggered for: {domain.domain_name} with template: {tenant.template}")
    except Exception as e:
        logger.error(f"Failed to trigger frontend build: {str(e)}")
    
    return {
        'domain_id': domain_id,
        'domain_name': domain.domain_name,
        'tenant_id': str(tenant.id),
        'deployed': True,
    }

