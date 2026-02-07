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
        Yeni bir işlem logu oluşturur ve eski logları temizler.
        
        Args:
            tenant: İlgili tenant
            user: İşlemi yapan kullanıcı
            action: İşlem kodu (örn: "product_update")
            description: İşlem özeti (örn: "iPhone 13 ürünü güncellendi")
            content_type: İlgili modelin adı
            object_id: İlgili objenin ID'si
            changes: {old: {}, new: {}} formatında değişiklikler
            ip_address: İşlemin yapıldığı IP
        """
        try:
            # 1. Logu oluştur
            log_entry = ActivityLog.objects.create(
                tenant=tenant,
                user=user,
                action=action,
                description=description,
                content_type=content_type,
                object_id=str(object_id) if object_id else None,
                changes=changes or {},
                ip_address=ip_address
            )
            
            # 2. Limit Kontrolü ve Temizlik
            ActivityLogService._cleanup_old_logs(tenant)
            
            return log_entry
        except Exception as e:
            logger.error(f"ActivityLog logging failed for tenant {tenant.slug}: {str(e)}")
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
