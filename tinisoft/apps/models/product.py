"""
Gelişmiş ürün modelleri - Tenant-specific.
Her tenant'ın kendi schema'sında ürün, varyant, opsiyon ve görsel tabloları olur.
"""
from django.db import models
from core.models import BaseModel


class Category(BaseModel):
    """
    Ürün kategorisi.
    Tenant-specific - her tenant kendi kategori ağacına sahip olur.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='categories',
        db_index=True,
    )
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'slug']),
            models.Index(fields=['tenant', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class Product(BaseModel):
    """
    Ürün modeli.
    Tenant-specific - her tenant'ın kendi schema'sında.

    Not:
    - Basit ürünler için direkt bu model kullanılır.
    - Varyantlı ürünlerde fiyat/stok bilgisi ProductVariant üzerinde tutulur.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='products',
        db_index=True,
    )
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, db_index=True)
    description = models.TextField(blank=True)

    # Fiyat (varyant yoksa kullanılır, varyant varsa default display fiyat için)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # SKU / Barkod (basit ürünler için)
    sku = models.CharField(max_length=100, blank=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True)

    # Stok bilgileri (basit ürünler için)
    track_inventory = models.BooleanField(default=True)
    inventory_quantity = models.IntegerField(default=0)

    # Ürün özellikleri
    is_variant_product = models.BooleanField(
        default=False,
        help_text="Ürünün varyantları var mı? Varsa stok/fiyat bilgisi varyantlarda tutulur.",
    )

    # Durum
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('archived', 'Archived'),
        ],
        default='draft',
        db_index=True,
    )

    # Kategoriler (çoklu)
    categories = models.ManyToManyField(
        Category,
        related_name='products',
        blank=True,
    )
    
    # SEO ve Meta
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="SEO başlık (meta title)"
    )
    meta_description = models.TextField(
        blank=True,
        help_text="SEO açıklama (meta description)"
    )
    meta_keywords = models.CharField(
        max_length=500,
        blank=True,
        help_text="SEO anahtar kelimeler (virgülle ayrılmış)"
    )
    
    # Etiketler (Tags)
    tags = models.JSONField(
        default=list,
        help_text="Ürün etiketleri (JSON array)"
    )
    
    # Koleksiyonlar (Collections)
    collections = models.JSONField(
        default=list,
        help_text="Ürün koleksiyonları (JSON array)"
    )
    
    # Ağırlık ve Boyutlar (Kargo için)
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Ağırlık (kg)"
    )
    length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Uzunluk (cm)"
    )
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Genişlik (cm)"
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Yükseklik (cm)"
    )
    
    # Satış bilgileri
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Öne çıkan ürün mü?"
    )
    is_new = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Yeni ürün mü?"
    )
    is_bestseller = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Çok satan ürün mü?"
    )
    
    # Sıralama
    sort_order = models.IntegerField(
        default=0,
        db_index=True,
        help_text="Sıralama (düşük değer önce gösterilir)"
    )
    
    # Görüntüleme
    is_visible = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Müşterilere görünür mü?"
    )
    available_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Ne zaman satışa çıkacak?"
    )
    available_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Ne zaman satıştan kalkacak?"
    )
    
    # İstatistikler
    view_count = models.PositiveIntegerField(default=0)
    sale_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Ek bilgiler (JSON format)"
    )

    class Meta:
        db_table = 'products'
        ordering = ['sort_order', '-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'slug']),
            models.Index(fields=['tenant', 'is_visible']),
            models.Index(fields=['tenant', 'is_featured']),
            models.Index(fields=['sku']),
            models.Index(fields=['sort_order']),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class ProductImage(BaseModel):
    """
    Ürün görselleri.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image_url = models.URLField(max_length=1000)
    alt_text = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = 'product_images'
        ordering = ['position', 'created_at']

    def __str__(self):
        return f"Image for {self.product.name} ({self.position})"


class ProductOption(BaseModel):
    """
    Ürün opsiyonu (örn: Beden, Renk).
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='options',
    )
    name = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'product_options'
        ordering = ['position', 'created_at']

    def __str__(self):
        return f"{self.name} ({self.product.name})"


class ProductOptionValue(BaseModel):
    """
    Ürün opsiyon değeri (örn: Kırmızı, M, L).
    """
    option = models.ForeignKey(
        ProductOption,
        on_delete=models.CASCADE,
        related_name='values',
    )
    value = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'product_option_values'
        ordering = ['position', 'created_at']
        unique_together = ('option', 'value')

    def __str__(self):
        return f"{self.option.name}: {self.value}"


class ProductVariant(BaseModel):
    """
    Ürün varyantı.
    Örn: T-Shirt / Beden: M / Renk: Kırmızı
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
    )
    name = models.CharField(
        max_length=255,
        help_text="Varyant adı (örn: M / Kırmızı).",
    )

    # Fiyat
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Stok
    track_inventory = models.BooleanField(default=True)
    inventory_quantity = models.IntegerField(default=0)

    # Kimlik
    sku = models.CharField(max_length=100, blank=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True)
    
    # Option Values (varyantın hangi option değerlerine sahip olduğu)
    option_values = models.ManyToManyField(
        ProductOptionValue,
        related_name='variants',
        blank=True,
        help_text="Varyantın sahip olduğu option değerleri (örn: Beden: M, Renk: Kırmızı)"
    )

    is_default = models.BooleanField(
        default=False,
        help_text="Varsayılan gösterilecek varyant mı?",
    )
    
    # Görsel (varyanta özel görsel)
    image_url = models.URLField(max_length=1000, blank=True, help_text="Varyanta özel görsel")

    class Meta:
        db_table = 'product_variants'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'sku']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

