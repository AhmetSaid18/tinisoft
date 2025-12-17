"""
İstek listesi / Favoriler modelleri - Tenant-specific.
İkas benzeri wishlist sistemi.
"""
from django.db import models
from core.models import BaseModel


class Wishlist(BaseModel):
    """
    İstek listesi.
    Tenant-specific - her tenant'ın kendi wishlist'leri.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='wishlists',
        db_index=True,
    )
    
    # Müşteri
    customer = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='wishlists',
        help_text="Wishlist sahibi (TenantUser)"
    )
    
    # Liste adı (müşteri birden fazla liste oluşturabilir)
    name = models.CharField(
        max_length=255,
        default='Favorilerim',
        help_text="Liste adı"
    )
    is_default = models.BooleanField(
        default=True,
        help_text="Varsayılan liste mi?"
    )
    is_public = models.BooleanField(
        default=False,
        help_text="Herkese açık mı?"
    )
    
    class Meta:
        db_table = 'wishlists'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'customer']),
            models.Index(fields=['is_default']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.customer.email} ({self.tenant.name})"


class WishlistItem(BaseModel):
    """
    İstek listesi kalemi.
    """
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='items',
    )
    
    # Ürün
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='wishlist_items',
    )
    variant = models.ForeignKey(
        'ProductVariant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='wishlist_items',
    )
    
    # Not
    note = models.TextField(blank=True, help_text="Müşteri notu")
    
    class Meta:
        db_table = 'wishlist_items'
        ordering = ['-created_at']
        unique_together = ('wishlist', 'product', 'variant')
        indexes = [
            models.Index(fields=['wishlist']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        variant_str = f" - {self.variant.name}" if self.variant else ""
        return f"{self.product.name}{variant_str} in {self.wishlist.name}"

