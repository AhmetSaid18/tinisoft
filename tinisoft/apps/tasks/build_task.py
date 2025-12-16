"""
Celery tasks for frontend build automation.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def trigger_frontend_build(tenant_id: str, domain_name: str, template: str = 'default'):
    """
    Frontend build'i tetikle.
    
    Args:
        tenant_id: Tenant ID
        domain_name: Domain adı
        template: Frontend template adı (default, modern, classic, vb.)
    """
    from apps.models import Tenant
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        template = template or tenant.template  # Tenant'tan template al
    except Tenant.DoesNotExist:
        logger.error(f"Tenant not found: {tenant_id}")
        return
    
    logger.info(f"Frontend build triggered for tenant: {tenant_id}, domain: {domain_name}, template: {template}")
    
    # TODO: Implement build logic
    # 1. Frontend repo'yu clone et
    # 2. Template'i seç (template klasöründen)
    # 3. Environment variables oluştur (tenant-specific):
    #    - REACT_APP_API_URL=https://api.tinisoft.com.tr
    #    - REACT_APP_TENANT_ID={tenant_id}
    #    - REACT_APP_TENANT_DOMAIN={domain_name}
    #    - REACT_APP_TEMPLATE={template}
    # 4. Build yap (npm run build veya yarn build)
    # 5. Docker image oluştur (template-specific)
    # 6. Container başlat
    # 7. Traefik routing ekle (zaten domain_task'da yapılıyor)
    # 8. SSL sertifikası al (zaten domain_task'da yapılıyor)
    
    return {
        'tenant_id': tenant_id,
        'domain_name': domain_name,
        'template': template,
        'status': 'pending',
        'frontend_url': f"https://{domain_name}",
    }

