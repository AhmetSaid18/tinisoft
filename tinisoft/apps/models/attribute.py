"""
Ürün özellikleri modelleri - Tenant-specific.
İkas benzeri attribute sistemi.
"""
from django.db import models
from core.models import BaseModel


class ProductAttribute(BaseModel):
    """
    Ürün özelliği (Attribute).
    Örn: Renk, Beden, Malzeme, Marka
    Tenant-specific - her tenant'ın kendi özellikleri.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='product_attributes',
        db_index=True,
    )
    
    name = models.CharField(max_length=100, db_index=True, help_text="Özellik adı (örn: Renk)")
    slug = models.SlugField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    
    # Özellik tipi
    attribute_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Metin'),
            ('number', 'Sayı'),
            ('boolean', 'Evet/Hayır'),
            ('select', 'Seçim'),
            ('multiselect', 'Çoklu Seçim'),
            ('color', 'Renk'),
            ('image', 'Görsel'),
        ],
        default='select',
    )
    
    # Filtreleme
    is_filterable = models.BooleanField(
        default=True,
        help_text="Filtreleme için kullanılabilir mi?"
    )
    is_visible = models.BooleanField(
        default=True,
        help_text="Ürün sayfasında görünür mü?"
    )
    
    # Sıralama
    position = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'product_attributes'
        ordering = ['position', 'name']
        indexes = [
            models.Index(fields=['tenant', 'slug']),
            models.Index(fields=['tenant', 'is_filterable']),
        ]
        unique_together = ('tenant', 'slug')
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class ProductAttributeValue(BaseModel):
    """
    Ürün özellik değeri (Attribute Value).
    Örn: Kırmızı, M, Pamuk, Nike
    """
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name='values',
    )
    
    value = models.CharField(max_length=255, db_index=True, help_text="Değer (örn: Kırmızı)")
    slug = models.SlugField(max_length=255, db_index=True)
    
    # Renk için hex kodu
    color_code = models.CharField(
        max_length=7,
        blank=True,
        help_text="Renk kodu (hex, örn: #FF0000)"
    )
    
    # Görsel
    image_url = models.URLField(max_length=1000, blank=True)
    
    # Sıralama
    position = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'product_attribute_values'
        ordering = ['position', 'value']
        unique_together = ('attribute', 'slug')
        indexes = [
            models.Index(fields=['attribute', 'slug']),
        ]
    
    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductAttributeMapping(BaseModel):
    """
    Ürün-Özellik eşleştirmesi.
    Hangi ürün hangi özelliklere sahip?
    """
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='attribute_mappings',
    )
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name='product_mappings',
    )
    value = models.ForeignKey(
        ProductAttributeValue,
        on_delete=models.CASCADE,
        related_name='product_mappings',
    )
    
    class Meta:
        db_table = 'product_attribute_mappings'
        unique_together = ('product', 'attribute', 'value')
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['attribute', 'value']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}: {self.value.value}"

