from django.db import models
from core.models import BaseModel
import uuid

class ActivityLog(BaseModel):
    """
    Tenant bazlı işlem logları.
    Mağaza sahibi (Owner) ve personelin (Staff) yaptığı işlemler kaydedilir.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='activity_logs',
        db_index=True
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs'
    )
    
    # İşlem detayları
    action = models.CharField(
        max_length=100,
        help_text="Yapılan işlem (örn: product_updated, order_status_changed)"
    )
    description = models.TextField(
        help_text="İşlemin okunabilir özeti"
    )
    
    # İlgili obje bilgileri (Generic relation yerine basit string/UUID tutuyoruz)
    content_type = models.CharField(
        max_length=50,
        help_text="İlgili model adı (örn: Product, Order)"
    )
    object_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="İlgili objenin ID'si"
    )
    
    # Teknik detaylar
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Değişen verilerin önceki ve sonraki halleri"
    )
    
    class Meta:
        db_table = 'activity_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.tenant.slug} - {self.action} - {self.user}"
