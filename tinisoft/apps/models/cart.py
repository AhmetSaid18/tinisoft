"""
Sepet modelleri - Tenant-specific.
İkas benzeri sepet yönetimi.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import BaseModel


class Cart(BaseModel):
    """
    Sepet modeli.
    Tenant-specific - her tenant'ın kendi schema'sında.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='carts',
        db_index=True,
    )
    
    # Müşteri (guest checkout için null olabilir)
    customer = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts',
        help_text="Sepet sahibi (TenantUser) - guest checkout için null"
    )
    
    # Session ID (guest checkout için)
    session_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Guest checkout için session ID"
    )
    
    # Fiyat bilgileri (cache)
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    
    # Kargo yöntemi
    shipping_method = models.ForeignKey(
        'ShippingMethod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carts',
    )
    
    # Kupon bilgileri
    coupon = models.ForeignKey(
        'Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carts',
        help_text="Uygulanan kupon"
    )
    coupon_code = models.CharField(max_length=50, blank=True, help_text="Kupon kodu")
    
    # Metadata
    currency = models.CharField(max_length=3, default='TRY')
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Sepet son kullanma tarihi (genelde 30 gün)"
    )
    
    class Meta:
        db_table = 'carts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'customer']),
            models.Index(fields=['tenant', 'session_id']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        if self.customer:
            return f"Cart - {self.customer.email} ({self.tenant.name})"
        return f"Cart - Guest ({self.tenant.name})"
    
    def calculate_totals(self):
        """Sepet toplamlarını hesapla."""
        items = self.items.filter(is_deleted=False)
        self.subtotal = sum(item.total_price for item in items)
        
        # Kargo ücreti hesaplama
        if self.shipping_method:
            if self.shipping_method.free_shipping_threshold:
                if self.subtotal >= self.shipping_method.free_shipping_threshold:
                    self.shipping_cost = Decimal('0.00')
                else:
                    self.shipping_cost = self.shipping_method.price
            else:
                self.shipping_cost = self.shipping_method.price
        else:
            self.shipping_cost = Decimal('0.00')
        
        # Vergi hesaplama (Dinamik - Tenant bazlı)
        from apps.models import Tax
        active_tax = Tax.objects.filter(
            tenant=self.tenant,
            is_active=True,
            is_deleted=False
        ).order_by('-is_default', '-created_at').first()
        
        tax_rate = active_tax.rate if active_tax else Decimal('0.00')
        self.tax_amount = self.subtotal * (tax_rate / Decimal('100'))
        
        # Kupon indirimi hesapla
        coupon_discount = Decimal('0.00')
        if self.coupon:
            try:
                # Kupon geçerliliğini kontrol et (hata durumunda indirim 0 kalsın)
                is_valid, _ = self.coupon.is_valid(
                    customer_email=self.customer.email if self.customer else None,
                    order_amount=self.subtotal
                )
                if is_valid:
                    coupon_discount = self.coupon.calculate_discount(self.subtotal)
                    # Ücretsiz kargo kontrolü
                    if self.coupon.discount_type == self.coupon.DiscountType.FREE_SHIPPING:
                        self.shipping_cost = Decimal('0.00')
            except Exception as e:
                logger.warning(f"Error calculating coupon discount: {e}")
                pass
        
        self.discount_amount = coupon_discount
        
        # Toplam
        self.total = (
            self.subtotal +
            self.shipping_cost +
            self.tax_amount -
            self.discount_amount
        )
        self.save()
        return self.total


class CartItem(BaseModel):
    """
    Sepet kalemi.
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
    )
    
    # Ürün bilgileri
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
    )
    variant = models.ForeignKey(
        'ProductVariant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart_items',
    )
    
    # Miktar
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
    )
    
    # Fiyat (cache - sepete eklendiği andaki fiyat)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    
    class Meta:
        db_table = 'cart_items'
        ordering = ['created_at']
        unique_together = ('cart', 'product', 'variant')
        indexes = [
            models.Index(fields=['cart']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        variant_str = f" - {self.variant.name}" if self.variant else ""
        return f"{self.product.name}{variant_str} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        """Toplam fiyatı otomatik hesapla."""
        # Fiyat belirleme: varyant varsa varyant fiyatı, yoksa ürün fiyatı
        if self.variant:
            self.unit_price = self.variant.price
        else:
            self.unit_price = self.product.price
        
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        
        # Sepet toplamlarını güncelle
        if self.cart:
            self.cart.calculate_totals()
    
    def delete(self, *args, **kwargs):
        """Sepet kalemi silindiğinde sepet toplamlarını güncelle."""
        cart = self.cart
        super().delete(*args, **kwargs)
        if cart:
            cart.calculate_totals()

