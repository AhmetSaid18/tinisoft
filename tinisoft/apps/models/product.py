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
    sort_order = models.IntegerField(default=0, help_text="Sıralama (küçükten büyüğe)")

    class Meta:
        db_table = 'categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['tenant', 'slug']),
            models.Index(fields=['tenant', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class Brand(BaseModel):
    """
    Ürün markası.
    Tenant-specific.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='brands',
        db_index=True,
    )
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, db_index=True)
    logo_url = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'brands'
        ordering = ['name']
        unique_together = ('tenant', 'name')
        indexes = [
            models.Index(fields=['tenant', 'slug']),
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
    description = models.TextField(
        blank=True,
        help_text="Düz metin açıklama (plain text)"
    )
    description_html = models.TextField(
        blank=True,
        help_text="HTML formatında açıklama (rich text)"
    )

    # Fiyat (varyant yoksa kullanılır, varyant varsa default display fiyat için)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(
        max_length=3,
        default='TRY',
        help_text="Para birimi (ISO 4217 kodu: TRY, USD, EUR, vb.) - TCMB entegrasyonu için"
    )

    # SKU / Barkod (basit ürünler için)
    sku = models.CharField(max_length=200, blank=True, db_index=True)
    barcode = models.CharField(max_length=200, blank=True)
    
    # Varyant Grubu SKU (aynı SKU'ya sahip ürünler birbirinin varyantı)
    variant_group_sku = models.CharField(max_length=200, blank=True, db_index=True)

    # Stok bilgileri (basit ürünler için)
    track_inventory = models.BooleanField(default=True)
    inventory_quantity = models.IntegerField(default=0)
    
    # Sanal stok (Drop-shipping, sipariş üzerine üretim, vb.)
    allow_backorder = models.BooleanField(
        default=False,
        help_text="Stok bittiğinde satışa devam edilsin mi? (Sanal stok - backorder)"
    )
    virtual_stock_quantity = models.IntegerField(
        default=0,
        null=True,
        blank=True,
        help_text="Sanal stok miktarı (opsiyonel - takip edilmek istenirse). 0 = sınırsız, >0 = limitli sanal stok"
    )

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
    is_reviewed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Yönetici tarafından incelendi mi/güncellendi mi?"
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
    
    # Marka ve Menşei
    brand_item = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    brand = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Marka (String - Legacy)"
    )
    origin = models.CharField(
        max_length=255,
        blank=True,
        help_text="Menşei"
    )
    
    # Ürün Tipi
    product_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ürün tipi"
    )
    
    # GTIN, MPN, GTIP (E-ticaret standartları)
    gtin = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text="GTIN (Global Trade Item Number)"
    )
    mpn = models.CharField(
        max_length=100,
        blank=True,
        help_text="MPN (Manufacturer Part Number)"
    )
    gtip = models.CharField(
        max_length=50,
        blank=True,
        help_text="GTIP (Gümrük Tarife İstatistik Pozisyonu)"
    )
    
    # Fiyat bilgileri
    buying_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Alış fiyatı (maliyet)"
    )
    ecommerce_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="E-ticaret site fiyatı"
    )
    shipping_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Kargo fiyatı"
    )
    
    # KDV dahil fiyat (Tax modelinden otomatik hesaplanır)
    price_with_vat = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="KDV dahil fiyat (tenant'ın aktif Tax'ından otomatik hesaplanır)"
    )
    
    # Stok bilgileri
    critical_stock = models.IntegerField(
        default=0,
        help_text="Kritik stok seviyesi"
    )
    
    # Kargo bilgileri
    desi = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Desi (kargo hesaplama için)"
    )
    depth = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Derinlik (cm)"
    )
    
    # Tarih bilgileri
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Son kullanma tarihi (Miad)"
    )
    
    # Fatura bilgileri
    invoice_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Fatura adı"
    )
    
    # Raf bilgisi
    shelf_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Raf numarası"
    )
    
    # E-ticaret entegrasyon
    ecommerce_category = models.CharField(
        max_length=255,
        blank=True,
        help_text="E-ticaret kategori adı"
    )
    ecommerce_integration_code = models.CharField(
        max_length=100,
        blank=True,
        help_text="E-ticaret entegrasyon kodu"
    )
    fulfillment_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Fulfillment ID"
    )
    
    # Uyumluluk bilgileri (metadata'da saklanır)
    # Model, Seri, Hacim, Yıl, Numara, Beden, Renk, Desen, Cinsiyet, vb.
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Ek bilgiler (JSON format) - Uyumluluk bilgileri, vb."
    )
    
    # Teknik Özellikler (Esnek Yapı)
    specifications = models.JSONField(
        default=list,
        blank=True,
        help_text="Teknik özellikler (JSON list: [{'key': 'Başlık', 'value': 'Değer'}])"
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
    
    def is_available(self, quantity=1):
        """
        Ürünün stokta olup olmadığını kontrol et (gerçek + sanal stok).
        """
        if not self.track_inventory:
            return True
        
        real_stock = self.inventory_quantity
        available_qty = real_stock
        
        if self.allow_backorder:
            if self.virtual_stock_quantity is not None and self.virtual_stock_quantity > 0:
                available_qty = real_stock + self.virtual_stock_quantity
            else:
                return True # Sınırsız sanal stok
        
        return available_qty >= quantity

    def save(self, *args, **kwargs):
        """Save metodunu override et - KDV dahil fiyatı tenant'ın aktif Tax'ından otomatik hesapla."""
        # Sanal stok girildiyse, otomatik olarak stoksuz satışa izin ver
        if self.virtual_stock_quantity is not None and self.virtual_stock_quantity > 0:
            self.allow_backorder = True
            
        from decimal import Decimal
        from apps.models import Tax
        
        # Tenant'ın aktif ve varsayılan Tax'ını bul
        active_tax = Tax.objects.filter(
            tenant=self.tenant,
            is_active=True,
            is_deleted=False
        ).order_by('-is_default', '-created_at').first()
        
        # KDV dahil fiyat hesaplama
        if active_tax and active_tax.rate and active_tax.rate > 0:
            # KDV dahil fiyat = Fiyat * (1 + KDV oranı / 100)
            # Örnek: 100 TL * (1 + 20/100) = 100 * 1.20 = 120 TL
            self.price_with_vat = self.price * (Decimal('1') + (active_tax.rate / Decimal('100')))
        else:
            # Aktif Tax yoksa veya oran 0 ise, KDV dahil fiyat = normal fiyat
            self.price_with_vat = self.price
        
        super().save(*args, **kwargs)


class ProductImage(BaseModel):
    """
    Ürün görselleri.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image_url = models.TextField(help_text="Görsel URL'i (signed URL'ler için TextField kullanılıyor)")
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
    
    # Sanal stok (Drop-shipping, sipariş üzerine üretim, vb.)
    allow_backorder = models.BooleanField(
        default=False,
        help_text="Stok bittiğinde satışa devam edilsin mi? (Sanal stok - backorder)"
    )
    virtual_stock_quantity = models.IntegerField(
        default=0,
        null=True,
        blank=True,
        help_text="Sanal stok miktarı (opsiyonel - takip edilmek istenirse). 0 = sınırsız, >0 = limitli sanal stok"
    )

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
    image_url = models.TextField(blank=True, help_text="Varyanta özel görsel URL'i (signed URL'ler için TextField kullanılıyor)")

    class Meta:
        db_table = 'product_variants'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'sku']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def is_available(self, quantity=1):
        """
        Varyantın stokta olup olmadığını kontrol et (gerçek + sanal stok).
        """
        if not self.track_inventory:
            return True
        
        real_stock = self.inventory_quantity
        available_qty = real_stock
        
        if self.allow_backorder:
            if self.virtual_stock_quantity is not None and self.virtual_stock_quantity > 0:
                available_qty = real_stock + self.virtual_stock_quantity
            else:
                return True # Sınırsız sanal stok
        
        return available_qty >= quantity

    def save(self, *args, **kwargs):
        """Save metodunu override et."""
        # Sanal stok girildiyse, otomatik olarak stoksuz satışa izin ver
        if self.virtual_stock_quantity is not None and self.virtual_stock_quantity > 0:
            self.allow_backorder = True
            
        super().save(*args, **kwargs)

