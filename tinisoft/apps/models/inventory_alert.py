"""
Stok uyarıları modelleri - Tenant-specific.
İkas benzeri stok uyarı sistemi.
"""
from django.db import models
from core.models import BaseModel


class InventoryAlert(BaseModel):
    """
    Stok uyarısı.
    Tenant-specific - her tenant'ın kendi uyarıları.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='inventory_alerts',
        db_index=True,
    )
    
    # Ürün/Varyant
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='inventory_alerts',
        null=True,
        blank=True,
    )
    variant = models.ForeignKey(
        'ProductVariant',
        on_delete=models.CASCADE,
        related_name='inventory_alerts',
        null=True,
        blank=True,
    )
    
    # Eşik değeri
    threshold = models.PositiveIntegerField(
        help_text="Bu değerin altına düştüğünde uyarı ver"
    )
    
    # Bildirim ayarları
    notify_email = models.EmailField(
        blank=True,
        help_text="Bildirim gönderilecek e-posta"
    )
    notify_on_low_stock = models.BooleanField(
        default=True,
        help_text="Düşük stokta bildir"
    )
    notify_on_out_of_stock = models.BooleanField(
        default=True,
        help_text="Stok bittiğinde bildir"
    )
    
    # Durum
    is_active = models.BooleanField(default=True, db_index=True)
    last_notified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'inventory_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['product', 'variant']),
        ]
    
    def __str__(self):
        product_name = self.variant.name if self.variant else (self.product.name if self.product else 'N/A')
        return f"Inventory alert - {product_name} (threshold: {self.threshold})"
    
    def check_and_notify(self):
        """Stok durumunu kontrol et ve gerekirse bildir."""
        current_stock = 0
        
        if self.variant:
            current_stock = self.variant.inventory_quantity
        elif self.product:
            current_stock = self.product.inventory_quantity
        
        should_notify = False
        
        if current_stock <= 0 and self.notify_on_out_of_stock:
            should_notify = True
        elif current_stock <= self.threshold and self.notify_on_low_stock:
            should_notify = True
        
        if should_notify:
            # Son bildirimden 24 saat geçtiyse tekrar bildir
            from django.utils import timezone
            from datetime import timedelta
            
            if not self.last_notified_at or timezone.now() - self.last_notified_at >= timedelta(hours=24):
                # TODO: E-posta gönder
                self.last_notified_at = timezone.now()
                self.save()
                return True
        
        return False

