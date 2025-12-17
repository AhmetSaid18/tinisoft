"""
Analytics ve raporlama modelleri - Tenant-specific.
İkas benzeri analytics sistemi.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import BaseModel


class AnalyticsEvent(BaseModel):
    """
    Analytics event kaydı.
    Tenant-specific - her tenant'ın kendi event'leri.
    """
    class EventType(models.TextChoices):
        PAGE_VIEW = 'page_view', 'Sayfa Görüntüleme'
        PRODUCT_VIEW = 'product_view', 'Ürün Görüntüleme'
        ADD_TO_CART = 'add_to_cart', 'Sepete Ekleme'
        REMOVE_FROM_CART = 'remove_from_cart', 'Sepetten Çıkarma'
        CHECKOUT_START = 'checkout_start', 'Ödeme Başlatma'
        CHECKOUT_COMPLETE = 'checkout_complete', 'Ödeme Tamamlama'
        ORDER_CREATED = 'order_created', 'Sipariş Oluşturma'
        ORDER_COMPLETED = 'order_completed', 'Sipariş Tamamlama'
        SEARCH = 'search', 'Arama'
        FILTER = 'filter', 'Filtreleme'
        COUPON_APPLIED = 'coupon_applied', 'Kupon Uygulama'
        SIGNUP = 'signup', 'Kayıt Olma'
        LOGIN = 'login', 'Giriş Yapma'
    
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='analytics_events',
        db_index=True,
    )
    
    # Event bilgileri
    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices,
        db_index=True,
    )
    
    # Kullanıcı bilgileri
    customer = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_events',
    )
    session_id = models.CharField(max_length=255, blank=True, db_index=True)
    
    # Event data
    event_data = models.JSONField(
        default=dict,
        help_text="Event verileri (JSON format)"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(max_length=1000, blank=True)
    url = models.URLField(max_length=1000, blank=True)
    
    class Meta:
        db_table = 'analytics_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'event_type', 'created_at']),
            models.Index(fields=['tenant', 'customer']),
            models.Index(fields=['session_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.tenant.name} - {self.created_at}"


class SalesReport(BaseModel):
    """
    Satış raporu (günlük/haftalık/aylık özet).
    Tenant-specific - her tenant'ın kendi raporları.
    """
    class ReportPeriod(models.TextChoices):
        DAILY = 'daily', 'Günlük'
        WEEKLY = 'weekly', 'Haftalık'
        MONTHLY = 'monthly', 'Aylık'
        YEARLY = 'yearly', 'Yıllık'
    
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='sales_reports',
        db_index=True,
    )
    
    # Rapor bilgileri
    period = models.CharField(
        max_length=20,
        choices=ReportPeriod.choices,
        db_index=True,
    )
    period_start = models.DateField(db_index=True)
    period_end = models.DateField(db_index=True)
    
    # Satış istatistikleri
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    total_products_sold = models.PositiveIntegerField(default=0)
    average_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    
    # Müşteri istatistikleri
    new_customers = models.PositiveIntegerField(default=0)
    returning_customers = models.PositiveIntegerField(default=0)
    
    # İndirim istatistikleri
    total_discounts = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    total_coupons_used = models.PositiveIntegerField(default=0)
    
    # Kargo istatistikleri
    total_shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    
    # Metadata
    metadata = models.JSONField(default=dict, help_text="Ek istatistikler (JSON format)")
    
    class Meta:
        db_table = 'sales_reports'
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['tenant', 'period', 'period_start']),
        ]
        unique_together = ('tenant', 'period', 'period_start')
    
    def __str__(self):
        return f"Sales Report - {self.get_period_display()} - {self.period_start} ({self.tenant.name})"


class ProductAnalytics(BaseModel):
    """
    Ürün bazlı analytics.
    Tenant-specific - her tenant'ın kendi ürün analytics'leri.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='product_analytics',
        db_index=True,
    )
    
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='analytics',
    )
    
    # Görüntüleme istatistikleri
    view_count = models.PositiveIntegerField(default=0)
    unique_viewers = models.PositiveIntegerField(default=0)
    
    # Satış istatistikleri
    sale_count = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    
    # Sepet istatistikleri
    add_to_cart_count = models.PositiveIntegerField(default=0)
    remove_from_cart_count = models.PositiveIntegerField(default=0)
    cart_conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Sepete ekleme / Görüntüleme oranı (%)"
    )
    
    # Dönüşüm oranı
    conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Satış / Görüntüleme oranı (%)"
    )
    
    # Tarih aralığı (rapor için)
    report_date = models.DateField(db_index=True)
    
    class Meta:
        db_table = 'product_analytics'
        ordering = ['-report_date', '-view_count']
        indexes = [
            models.Index(fields=['tenant', 'product', 'report_date']),
            models.Index(fields=['tenant', 'report_date']),
        ]
        unique_together = ('tenant', 'product', 'report_date')
    
    def __str__(self):
        return f"Analytics - {self.product.name} - {self.report_date} ({self.tenant.name})"
    
    def calculate_conversion_rate(self):
        """Dönüşüm oranını hesapla."""
        if self.view_count > 0:
            self.conversion_rate = (Decimal(str(self.sale_count)) / Decimal(str(self.view_count))) * Decimal('100')
        else:
            self.conversion_rate = Decimal('0.00')
        self.save()
    
    def calculate_cart_conversion_rate(self):
        """Sepet dönüşüm oranını hesapla."""
        if self.view_count > 0:
            self.cart_conversion_rate = (Decimal(str(self.add_to_cart_count)) / Decimal(str(self.view_count))) * Decimal('100')
        else:
            self.cart_conversion_rate = Decimal('0.00')
        self.save()

