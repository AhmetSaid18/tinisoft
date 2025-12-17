"""
İndirim ve promosyon modelleri - Tenant-specific.
İkas benzeri kupon ve indirim sistemi.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel


class Coupon(BaseModel):
    """
    İndirim kuponu.
    Tenant-specific - her tenant'ın kendi kuponları.
    """
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Yüzde'
        FIXED = 'fixed', 'Sabit Tutar'
        FREE_SHIPPING = 'free_shipping', 'Ücretsiz Kargo'
    
    class ApplicableTo(models.TextChoices):
        ALL = 'all', 'Tüm Ürünler'
        CATEGORY = 'category', 'Kategori'
        PRODUCT = 'product', 'Ürün'
        COLLECTION = 'collection', 'Koleksiyon'
    
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='coupons',
        db_index=True,
    )
    
    # Kupon bilgileri
    code = models.CharField(max_length=50, unique=True, db_index=True, help_text="Kupon kodu")
    name = models.CharField(max_length=255, help_text="Kupon adı")
    description = models.TextField(blank=True)
    
    # İndirim tipi ve miktarı
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="İndirim değeri (yüzde veya tutar)"
    )
    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maksimum indirim tutarı (yüzde indirimlerde)"
    )
    
    # Uygulanabilirlik
    applicable_to = models.CharField(
        max_length=20,
        choices=ApplicableTo.choices,
        default=ApplicableTo.ALL,
    )
    applicable_categories = models.ManyToManyField(
        'Category',
        related_name='coupons',
        blank=True,
    )
    applicable_products = models.ManyToManyField(
        'Product',
        related_name='coupons',
        blank=True,
    )
    applicable_collections = models.JSONField(
        default=list,
        help_text="Uygulanabilir koleksiyonlar (JSON array)"
    )
    
    # Minimum tutar
    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Minimum sipariş tutarı"
    )
    
    # Kullanım limitleri
    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Toplam kullanım limiti (null = sınırsız)"
    )
    usage_count = models.PositiveIntegerField(default=0, help_text="Kullanım sayısı")
    usage_limit_per_customer = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Müşteri başına kullanım limiti (null = sınırsız)"
    )
    
    # Tarih aralığı
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Durum
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Özel müşteriler
    customer_emails = models.JSONField(
        default=list,
        help_text="Sadece bu email'lere uygulanır (boş = herkese)"
    )
    customer_groups = models.JSONField(
        default=list,
        help_text="Sadece bu müşteri gruplarına uygulanır (boş = herkese)"
    )
    
    class Meta:
        db_table = 'coupons'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'code']),
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.tenant.name})"
    
    def is_valid(self, customer_email=None, order_amount=Decimal('0.00')):
        """Kupon geçerli mi?"""
        if not self.is_active:
            return False, "Kupon aktif değil."
        
        if self.valid_until and timezone.now() > self.valid_until:
            return False, "Kupon süresi dolmuş."
        
        if timezone.now() < self.valid_from:
            return False, "Kupon henüz geçerli değil."
        
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False, "Kupon kullanım limitine ulaşıldı."
        
        if order_amount < self.minimum_order_amount:
            return False, f"Minimum sipariş tutarı {self.minimum_order_amount} TL olmalıdır."
        
        if self.customer_emails and customer_email not in self.customer_emails:
            return False, "Bu kupon sizin için geçerli değil."
        
        return True, "Kupon geçerli."
    
    def calculate_discount(self, order_amount):
        """İndirim tutarını hesapla."""
        if self.discount_type == self.DiscountType.PERCENTAGE:
            discount = order_amount * (self.discount_value / Decimal('100'))
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return discount
        elif self.discount_type == self.DiscountType.FIXED:
            return min(self.discount_value, order_amount)
        elif self.discount_type == self.DiscountType.FREE_SHIPPING:
            return Decimal('0.00')  # Kargo ücreti ayrı hesaplanır
        return Decimal('0.00')


class Promotion(BaseModel):
    """
    Promosyon kampanyası.
    Tenant-specific - her tenant'ın kendi promosyonları.
    """
    class PromotionType(models.TextChoices):
        BUY_X_GET_Y = 'buy_x_get_y', 'X Al Y Bedava'
        BUY_X_GET_DISCOUNT = 'buy_x_get_discount', 'X Al İndirim Kazan'
        MINIMUM_PURCHASE = 'minimum_purchase', 'Minimum Alışveriş İndirimi'
        FREE_SHIPPING = 'free_shipping', 'Ücretsiz Kargo'
        GIFT = 'gift', 'Hediye'
    
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='promotions',
        db_index=True,
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    promotion_type = models.CharField(
        max_length=30,
        choices=PromotionType.choices,
    )
    
    # Kampanya kuralları
    minimum_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum ürün miktarı"
    )
    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum sipariş tutarı"
    )
    
    # Uygulanabilir ürünler
    applicable_products = models.ManyToManyField(
        'Product',
        related_name='promotions',
        blank=True,
    )
    applicable_categories = models.ManyToManyField(
        'Category',
        related_name='promotions',
        blank=True,
    )
    
    # İndirim/Hediye bilgileri
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100.00'))],
    )
    gift_product = models.ForeignKey(
        'Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gift_promotions',
    )
    
    # Tarih aralığı
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Durum
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        db_table = 'promotions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

