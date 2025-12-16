"""
Product model - Tenant-specific.
Her tenant'ın kendi schema'sında products tablosu olur.
"""
from django.db import models
from core.models import BaseModel


class Product(BaseModel):
    """
    Ürün modeli.
    Tenant-specific - her tenant'ın kendi schema'sında.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='products',
        db_index=True
    )
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sku = models.CharField(max_length=100, blank=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True)
    
    # Stok bilgileri
    track_inventory = models.BooleanField(default=True)
    inventory_quantity = models.IntegerField(default=0)
    
    # Durum
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('archived', 'Archived'),
        ],
        default='draft',
        db_index=True
    )
    
    # Kategori (gelecekte Category modeli eklenecek)
    # category = models.ForeignKey('Category', ...)
    
    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'slug']),
            models.Index(fields=['sku']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

