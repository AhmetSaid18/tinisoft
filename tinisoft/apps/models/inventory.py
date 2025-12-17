"""
Stok/Envanter modelleri - Tenant-specific.
İkas benzeri stok yönetimi.
"""
from django.db import models
from django.core.validators import MinValueValidator
from core.models import BaseModel


class InventoryMovement(BaseModel):
    """
    Stok hareketi modeli.
    Her stok değişikliği burada kayıt altına alınır.
    """
    class MovementType(models.TextChoices):
        IN = 'in', 'Giriş'
        OUT = 'out', 'Çıkış'
        ADJUSTMENT = 'adjustment', 'Düzeltme'
        RESERVED = 'reserved', 'Rezerve'
        UNRESERVED = 'unreserved', 'Rezerve İptal'
        RETURNED = 'returned', 'İade'
        DAMAGED = 'damaged', 'Hasarlı'
        LOST = 'lost', 'Kayıp'
    
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='inventory_movements',
        db_index=True,
    )
    
    # Ürün/Varyant bilgileri
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='inventory_movements',
        null=True,
        blank=True,
    )
    variant = models.ForeignKey(
        'ProductVariant',
        on_delete=models.CASCADE,
        related_name='inventory_movements',
        null=True,
        blank=True,
    )
    
    # Hareket bilgileri
    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
        db_index=True,
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Hareket miktarı (pozitif değer)"
    )
    
    # Önceki ve sonraki stok
    previous_quantity = models.IntegerField(
        default=0,
        help_text="Hareket öncesi stok miktarı"
    )
    new_quantity = models.IntegerField(
        default=0,
        help_text="Hareket sonrası stok miktarı"
    )
    
    # İlişkili kayıtlar
    order = models.ForeignKey(
        'Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_movements',
        help_text="Sipariş kaynaklı hareket"
    )
    order_item = models.ForeignKey(
        'OrderItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_movements',
    )
    
    # Açıklama
    reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Hareket nedeni"
    )
    notes = models.TextField(
        blank=True,
        help_text="Ek notlar"
    )
    
    # Kullanıcı bilgisi
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_movements',
        help_text="Hareketi oluşturan kullanıcı"
    )
    
    class Meta:
        db_table = 'inventory_movements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'movement_type']),
            models.Index(fields=['product', 'variant']),
            models.Index(fields=['order']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        product_name = self.variant.name if self.variant else (self.product.name if self.product else 'N/A')
        return f"{self.get_movement_type_display()} - {product_name} ({self.quantity})"

