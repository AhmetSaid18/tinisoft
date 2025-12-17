"""
Terk edilen sepet modelleri - Tenant-specific.
İkas benzeri abandoned cart sistemi.
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta
from core.models import BaseModel


class AbandonedCart(BaseModel):
    """
    Terk edilen sepet.
    Tenant-specific - her tenant'ın kendi abandoned cart'ları.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='abandoned_carts',
        db_index=True,
    )
    
    # Sepet bilgisi
    cart = models.OneToOneField(
        'Cart',
        on_delete=models.CASCADE,
        related_name='abandoned_cart',
    )
    
    # Müşteri bilgileri
    customer_email = models.EmailField(db_index=True)
    customer_name = models.CharField(max_length=255, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Terk edilme bilgileri
    abandoned_at = models.DateTimeField(default=timezone.now, db_index=True)
    last_activity_at = models.DateTimeField(default=timezone.now)
    
    # E-posta gönderim durumu
    email_sent_count = models.PositiveIntegerField(default=0)
    first_email_sent_at = models.DateTimeField(null=True, blank=True)
    last_email_sent_at = models.DateTimeField(null=True, blank=True)
    recovered_at = models.DateTimeField(null=True, blank=True, help_text="Siparişe dönüştürüldü mü?")
    
    # Durum
    is_recovered = models.BooleanField(default=False, db_index=True)
    is_ignored = models.BooleanField(
        default=False,
        help_text="E-posta gönderilmeyecek (manuel olarak işaretlenmiş)"
    )
    
    class Meta:
        db_table = 'abandoned_carts'
        ordering = ['-abandoned_at']
        indexes = [
            models.Index(fields=['tenant', 'is_recovered']),
            models.Index(fields=['tenant', 'abandoned_at']),
            models.Index(fields=['customer_email']),
        ]
    
    def __str__(self):
        return f"Abandoned cart - {self.customer_email} ({self.tenant.name})"
    
    def should_send_email(self):
        """E-posta gönderilmeli mi?"""
        if self.is_recovered or self.is_ignored:
            return False
        
        # İlk e-posta: 1 saat sonra
        if self.email_sent_count == 0:
            if timezone.now() - self.abandoned_at >= timedelta(hours=1):
                return True
        
        # İkinci e-posta: 24 saat sonra
        elif self.email_sent_count == 1:
            if self.last_email_sent_at and timezone.now() - self.last_email_sent_at >= timedelta(hours=24):
                return True
        
        # Üçüncü e-posta: 72 saat sonra
        elif self.email_sent_count == 2:
            if self.last_email_sent_at and timezone.now() - self.last_email_sent_at >= timedelta(hours=72):
                return True
        
        return False

