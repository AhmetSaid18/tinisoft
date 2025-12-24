"""
Para birimi modelleri - Tenant-specific.
İkas benzeri çoklu para birimi sistemi.
"""
from django.db import models
from decimal import Decimal
from core.models import BaseModel


class Currency(BaseModel):
    """
    Para birimi.
    Tenant-specific - her tenant'ın kendi para birimleri.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='currencies',
        db_index=True,
    )
    
    code = models.CharField(max_length=3, db_index=True, help_text="Para birimi kodu (TRY, USD, EUR)")
    name = models.CharField(max_length=100, help_text="Para birimi adı (Türk Lirası)")
    symbol = models.CharField(max_length=10, help_text="Sembol (₺, $, €)")
    
    # Dönüşüm oranı (varsayılan para birimine göre)
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('1.0000'),
        help_text="Dönüşüm oranı (varsayılan para birimine göre)"
    )
    
    # Format ayarları
    decimal_places = models.PositiveIntegerField(default=2)
    symbol_position = models.CharField(
        max_length=10,
        choices=[
            ('before', 'Önce (₺100)'),
            ('after', 'Sonra (100₺)'),
        ],
        default='after',
    )
    
    # Durum
    is_default = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Varsayılan para birimi mi?"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        db_table = 'currencies'
        ordering = ['is_default', 'code']
        indexes = [
            models.Index(fields=['tenant', 'code']),
            models.Index(fields=['tenant', 'is_default']),
        ]
        unique_together = ('tenant', 'code')
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.tenant.name})"
    
    def format_amount(self, amount):
        """Tutarı formatla."""
        formatted = f"{amount:,.{self.decimal_places}f}"
        if self.symbol_position == 'before':
            return f"{self.symbol}{formatted}"
        else:
            return f"{formatted} {self.symbol}"


class Tax(BaseModel):
    """
    Vergi.
    Tenant-specific - her tenant'ın kendi vergileri.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='taxes',
        db_index=True,
    )
    
    name = models.CharField(max_length=255, help_text="Vergi adı (KDV, ÖTV, vb.)")
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Vergi oranı (yüzde)"
    )
    description = models.TextField(blank=True)
    
    # Uygulanabilirlik
    is_default = models.BooleanField(
        default=False,
        help_text="Varsayılan vergi mi?"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        db_table = 'taxes'
        ordering = ['is_default', 'name']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.rate}%) - {self.tenant.name}"
    
    def calculate_tax(self, amount):
        """Vergi tutarını hesapla."""
        return amount * (self.rate / Decimal('100'))
    
    def save(self, *args, **kwargs):
        """Save metodunu override et - Aktif olduğunda tüm ürünlerin KDV dahil fiyatlarını güncelle."""
        # is_active veya rate değişip değişmediğini kontrol et
        is_new = self.pk is None
        if not is_new:
            try:
                old_instance = Tax.objects.get(pk=self.pk)
                active_changed = old_instance.is_active != self.is_active
                rate_changed = old_instance.rate != self.rate
            except Tax.DoesNotExist:
                active_changed = False
                rate_changed = False
        else:
            active_changed = False
            rate_changed = False
        
        super().save(*args, **kwargs)
        
        # Eğer aktif edildiyse veya oran değiştiyse, tüm ürünlerin price_with_vat'ini güncelle
        if (is_new and self.is_active) or (active_changed and self.is_active) or rate_changed:
            # Background task olarak tüm ürünleri güncelle
            from apps.tasks.product_task import update_all_products_price_with_vat
            update_all_products_price_with_vat.delay(str(self.tenant.id))

