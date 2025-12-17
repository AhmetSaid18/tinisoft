"""
Sipariş modelleri - Tenant-specific.
İkas benzeri sipariş yönetimi.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import BaseModel


class Order(BaseModel):
    """
    Sipariş modeli.
    Tenant-specific - her tenant'ın kendi schema'sında.
    """
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', 'Beklemede'
        CONFIRMED = 'confirmed', 'Onaylandı'
        PROCESSING = 'processing', 'Hazırlanıyor'
        SHIPPED = 'shipped', 'Kargoya Verildi'
        DELIVERED = 'delivered', 'Teslim Edildi'
        CANCELLED = 'cancelled', 'İptal Edildi'
        REFUNDED = 'refunded', 'İade Edildi'
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Ödeme Bekleniyor'
        PAID = 'paid', 'Ödendi'
        PARTIALLY_PAID = 'partially_paid', 'Kısmen Ödendi'
        REFUNDED = 'refunded', 'İade Edildi'
        FAILED = 'failed', 'Ödeme Başarısız'
    
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='orders',
        db_index=True,
    )
    
    # Sipariş numarası (unique, tenant bazlı)
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Müşteri bilgileri
    customer = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text="Siparişi veren müşteri (TenantUser)"
    )
    
    # Müşteri bilgileri (guest checkout için)
    customer_email = models.EmailField(db_index=True)
    customer_first_name = models.CharField(max_length=100)
    customer_last_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Adres bilgileri
    shipping_address = models.ForeignKey(
        'ShippingAddress',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
    )
    billing_address = models.JSONField(
        default=dict,
        help_text="Fatura adresi (JSON format)"
    )
    
    # Sipariş durumu
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    
    # Fiyat bilgileri
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Ara toplam (ürün fiyatları toplamı)"
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Kargo ücreti"
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Vergi tutarı"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="İndirim tutarı"
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Toplam tutar"
    )
    
    # Kargo bilgileri
    shipping_method = models.ForeignKey(
        'ShippingMethod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
    )
    tracking_number = models.CharField(max_length=100, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Kupon bilgileri
    coupon = models.ForeignKey(
        'Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text="Kullanılan kupon"
    )
    coupon_code = models.CharField(max_length=50, blank=True, help_text="Kupon kodu (snapshot)")
    coupon_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Kupon indirimi"
    )
    
    # Notlar
    customer_note = models.TextField(blank=True, help_text="Müşteri notu")
    admin_note = models.TextField(blank=True, help_text="Admin notu")
    
    # Metadata
    currency = models.CharField(max_length=3, default='TRY')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'payment_status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['customer_email']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.customer_email}"
    
    def calculate_total(self):
        """Toplam tutarı hesapla."""
        self.total = (
            self.subtotal +
            self.shipping_cost +
            self.tax_amount -
            self.discount_amount
        )
        return self.total


class OrderItem(BaseModel):
    """
    Sipariş kalemi.
    Her siparişteki ürün/varyant bilgileri.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
    )
    
    # Ürün bilgileri
    product = models.ForeignKey(
        'Product',
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items',
    )
    variant = models.ForeignKey(
        'ProductVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
    )
    
    # Ürün bilgileri (snapshot - ürün silinse bile bilgiler kalır)
    product_name = models.CharField(max_length=255)
    variant_name = models.CharField(max_length=255, blank=True)
    product_sku = models.CharField(max_length=100, blank=True)
    
    # Fiyat ve miktar
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Birim fiyat (sipariş anındaki fiyat)"
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Toplam fiyat (quantity * unit_price)"
    )
    
    # Görsel (snapshot)
    product_image_url = models.URLField(max_length=1000, blank=True)
    
    class Meta:
        db_table = 'order_items'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity} - {self.order.order_number}"
    
    def save(self, *args, **kwargs):
        """Toplam fiyatı otomatik hesapla."""
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

