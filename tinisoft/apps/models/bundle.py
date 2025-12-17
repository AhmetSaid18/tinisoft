"""
Ürün paketleri modelleri - Tenant-specific.
İkas benzeri bundle/package sistemi.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import BaseModel


class ProductBundle(BaseModel):
    """
    Ürün paketi (Bundle).
    Birden fazla ürünü bir arada satma.
    Tenant-specific - her tenant'ın kendi paketleri.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='product_bundles',
        db_index=True,
    )
    
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    
    # Ana ürün (bundle'ın kendisi)
    main_product = models.OneToOneField(
        'Product',
        on_delete=models.CASCADE,
        related_name='bundle',
        help_text="Bundle'ın ana ürünü"
    )
    
    # Fiyatlandırma
    bundle_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Paket fiyatı (bireysel ürün fiyatlarından farklı olabilir)"
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="İndirim yüzdesi (bireysel fiyatlara göre)"
    )
    
    # Durum
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'product_bundles'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['tenant', 'slug']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"
    
    def calculate_total_price(self):
        """Bireysel ürün fiyatlarının toplamını hesapla."""
        total = Decimal('0.00')
        for item in self.items.filter(is_deleted=False):
            if item.variant:
                total += item.variant.price * item.quantity
            else:
                total += item.product.price * item.quantity
        return total
    
    def calculate_discount(self):
        """İndirim tutarını hesapla."""
        total_price = self.calculate_total_price()
        if self.discount_percentage:
            return total_price * (self.discount_percentage / Decimal('100'))
        return total_price - self.bundle_price


class ProductBundleItem(BaseModel):
    """
    Bundle içindeki ürün.
    """
    bundle = models.ForeignKey(
        ProductBundle,
        on_delete=models.CASCADE,
        related_name='items',
    )
    
    # Ürün
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='bundle_items',
    )
    variant = models.ForeignKey(
        'ProductVariant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='bundle_items',
    )
    
    # Miktar
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
    )
    
    # Sıralama
    position = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'product_bundle_items'
        ordering = ['position', 'created_at']
        unique_together = ('bundle', 'product', 'variant')
        indexes = [
            models.Index(fields=['bundle']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        variant_str = f" - {self.variant.name}" if self.variant else ""
        return f"{self.product.name}{variant_str} x{self.quantity} in {self.bundle.name}"

