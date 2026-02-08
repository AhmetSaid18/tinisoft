from apps.models import ActivityLog
import logging

logger = logging.getLogger(__name__)

class ActivityLogService:
    """
    Tenant bazlı işlem loglarını yöneten servis.
    Limit: Her tenant için son 1000 işlem tutulur.
    """
    
    LIMIT = 1000

    @staticmethod
    def log(tenant, user, action, description, content_type=None, object_id=None, changes=None, ip_address=None):
        """
        Yeni bir işlem logu oluşturur (Asenkron - Güvenlik Kontrollü).
        """
        if not user or not user.is_authenticated:
            return None
            
        # 1. Güvenlik Kontrolü: Personel ise yetkisi var mı?
        if user.is_tenant_staff and not user.is_tenant_owner and not user.is_owner:
            # Action içinden modül adını tahmin et (örn: product_update -> products)
            module = action.split('_')[0]
            if module == 'category': module = 'products' # Category yetkisi Product ile bağlı
            
            # Yetki kontrolü (bu sefer canlı user objesinden veya cache'den)
            if not user.has_staff_permission(module):
                logger.warning(f"[SECURITY] Unauthorized log attempt by {user.email} for action: {action}")
                return False

        from apps.tasks.activity_task import create_activity_log_task
        
        try:
            # Task'ı tetikle
            create_activity_log_task.delay(
                tenant_id=str(tenant.id) if tenant else None,
                user_id=user.id if user else None,
                action=action,
                description=description,
                content_type=content_type,
                object_id=object_id,
                changes=changes,
                ip_address=ip_address
            )
            return True
        except Exception as e:
            logger.error(f"ActivityLog delay failed for tenant {tenant.slug if tenant else 'N/A'}: {str(e)}")
            return None

    @staticmethod
    def _cleanup_old_logs(tenant):
        """
        Belirlenen limitin üzerindeki eski logları hard delete ile siler.
        """
        try:
            # Toplam log sayısını kontrol et
            count = ActivityLog.objects.filter(tenant=tenant).count()
            
            if count > ActivityLogService.LIMIT:
                # Silinecek miktar
                to_delete_count = count - ActivityLogService.LIMIT
                
                # En eski logların ID'lerini al
                old_log_ids = ActivityLog.objects.filter(
                    tenant=tenant
                ).order_by('created_at')[:to_delete_count].values_list('id', flat=True)
                
                # Hard delete (BaseModel'de soft delete varsa onu bypass etmek için direkt models.Model üzerinden silme gerekebilir 
                # ama şu an BaseModel'de özel bir delete override yoksa normal delete yeterli)
                ActivityLog.objects.filter(id__in=list(old_log_ids)).delete()
                
                logger.info(f"Cleaned up {to_delete_count} old logs for tenant {tenant.slug}")
        except Exception as e:
            logger.error(f"ActivityLog cleanup failed for tenant {tenant.slug}: {str(e)}")

    @staticmethod
    def get_logs(tenant, user=None, action=None, content_type=None):
        """Tenant'a ait logları getir."""
        queryset = ActivityLog.objects.filter(tenant=tenant)
        if user:
            queryset = queryset.filter(user=user)
        if action:
            queryset = queryset.filter(action=action)
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        return queryset.order_by('-created_at')
