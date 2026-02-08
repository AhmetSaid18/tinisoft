"""
Celery tasks for activity logging.
"""
from celery import shared_task
from apps.models import ActivityLog, Tenant
import logging

logger = logging.getLogger(__name__)

@shared_task
def create_activity_log_task(tenant_id, user_id, action, description, content_type=None, object_id=None, changes=None, ip_address=None):
    """
    Asenkron olarak işlem logu oluşturur. (Tenant-Aware)
    """
    try:
        from apps.models import Tenant, ActivityLog, User
        
        # 1. Tenant'ı bul (Veri izolasyonu için şart)
        tenant = Tenant.objects.get(id=tenant_id)
        
        # 2. Logu oluştur (user_id üzerinden direkt bağlantı daha hızlı)
        log_entry = ActivityLog.objects.create(
            tenant=tenant,
            user_id=user_id,
            action=action,
            description=description,
            content_type=content_type,
            object_id=str(object_id) if object_id else None,
            changes=changes or {},
            ip_address=ip_address
        )
        
        # 3. Limit Kontrolü ve Temizlik (Arka planda dükkanın log kapasitesini koru)
        LIMIT = 1000
        count = ActivityLog.objects.filter(tenant=tenant).count()
        
        if count > LIMIT:
            to_delete_count = count - LIMIT
            old_log_ids = ActivityLog.objects.filter(
                tenant=tenant
            ).order_by('created_at')[:to_delete_count].values_list('id', flat=True)
            
            ActivityLog.objects.filter(id__in=list(old_log_ids)).delete()
            logger.info(f"Cleaned up {to_delete_count} old logs for tenant: {tenant.slug}")
            
        return str(log_entry.id)
        
    except Exception as e:
        logger.error(f"Async ActivityLog logging failed: {str(e)}")
        return None
