"""
Sepet modelleri - Tenant-specific.
İkas benzeri sepet yönetimi.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import BaseModel
import logging

logger = logging.getLogger(__name__)


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
    
    # Seçili ve stokta olan ürünlerin toplamı (Kupon bu matrah üzerinden hesaplanır)
    eligible_subtotal = models.DecimalField(
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
        TWOPLACES = Decimal('0.01')
        
        # Her hesaplamada ürün fiyatlarını güncelle (güncel kur ve fiyat için)
        temp_subtotal = Decimal('0.00')
        eligible_subtotal = Decimal('0.00') # Kupon ve ödeme için geçerli olan tutar
        
        for item in items:
            # Ürün veya varyant fiyatını al
            if item.variant:
                base_price = item.variant.price
                product_currency = item.product.currency or 'TRY'
                is_available = item.variant.is_available(item.quantity)
            else:
                base_price = item.product.price
                product_currency = item.product.currency or 'TRY'
                is_available = item.product.is_available(item.quantity)
            
            cart_currency = self.currency or 'TRY'
            
            # Para birimi dönüşümü yap
            if product_currency != cart_currency:
                from apps.services.currency_service import CurrencyService
                try:
                    current_unit_price = CurrencyService.convert_amount(
                        base_price,
                        product_currency,
                        cart_currency
                    )
                except Exception:
                    current_unit_price = base_price
            else:
                current_unit_price = base_price
            
            # Item'ı güncelle (DB'ye yazmadan sadece toplama ekle)
            item.unit_price = current_unit_price
            item.total_price = current_unit_price * item.quantity
            
            # Tüm sepet toplamı (Görsel referans için)
            temp_subtotal += item.total_price
            
            # Sadece seçili VE stokta olanları kupon/ödeme matrahına ekle
            if item.is_selected and is_available:
                eligible_subtotal += item.total_price
            
            # DB'deki snapshot'ı da güncelle
            CartItem.objects.filter(id=item.id).update(
                unit_price=item.unit_price,
                total_price=item.total_price
            )

        self.subtotal = temp_subtotal
        self.eligible_subtotal = eligible_subtotal.quantize(TWOPLACES)
        
        # Kargo ücreti hesaplama (eligible tutar üzerinden)
        if self.shipping_method:
            if self.shipping_method.free_shipping_threshold:
                if eligible_subtotal >= self.shipping_method.free_shipping_threshold:
                    self.shipping_cost = Decimal('0.00')
                else:
                    self.shipping_cost = self.shipping_method.price
            else:
                self.shipping_cost = self.shipping_method.price
        else:
            self.shipping_cost = Decimal('0.00')
        
        # Vergi hesaplama (Dinamik - Tenant bazlı, eligible tutar üzerinden)
        from apps.models import Tax
        active_tax = Tax.objects.filter(
            tenant=self.tenant,
            is_active=True,
            is_deleted=False
        ).order_by('-is_default', '-created_at').first()
        
        tax_rate = active_tax.rate if active_tax else Decimal('0.00')
        self.tax_amount = eligible_subtotal * (tax_rate / Decimal('100'))
        
        # Kupon indirimi hesapla (Sadece eligible tutar üzerinden!)
        coupon_discount = Decimal('0.00')
        if self.coupon:
            try:
                # Kupon geçerliliğini kontrol et (eligible tutar üzerinden)
                is_valid, msg = self.coupon.is_valid(
                    customer_email=self.customer.email if self.customer else None,
                    order_amount=eligible_subtotal,
                    target_currency=self.currency or 'TRY'
                )
                if is_valid:
                    coupon_discount = self.coupon.calculate_discount(
                        eligible_subtotal,
                        target_currency=self.currency or 'TRY'
                    )
                    # Ücretsiz kargo kontrolü
                    if self.coupon.discount_type == self.coupon.DiscountType.FREE_SHIPPING:
                        self.shipping_cost = Decimal('0.00')
                else:
                    logger.warning(f"[CART_CALC] Coupon {self.coupon.code} invalid for eligible subtotal {eligible_subtotal}: {msg}")
            except Exception as e:
                logger.warning(f"[CART_CALC] Error calculating coupon discount: {e}")
                pass
        
        self.discount_amount = coupon_discount
        
        # Yuvarlama
        self.subtotal = self.subtotal.quantize(TWOPLACES)
        self.shipping_cost = self.shipping_cost.quantize(TWOPLACES)
        self.tax_amount = self.tax_amount.quantize(TWOPLACES)
        self.discount_amount = self.discount_amount.quantize(TWOPLACES)
        
        # Ödenecek Toplamı hesapla (Sadece eligible ürünler + kargo + vergi - indirim)
        gross_total = (eligible_subtotal + self.shipping_cost + self.tax_amount)
        self.total = max(Decimal('0.00'), (gross_total - self.discount_amount)).quantize(TWOPLACES)
        
        logger.info(
            f"[CART_CALC] Cart {self.id} | Total Subtotal: {self.subtotal} | "
            f"Eligible Subtotal: {eligible_subtotal} | Total to Pay: {self.total}"
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
    
    # Seçili mi? (Checkout'a dahil edilsin mi?)
    is_selected = models.BooleanField(default=True, db_index=True)
    
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
        """Toplam fiyatı otomatik hesapla ve para birimi dönüşümü yap."""
        from apps.services.currency_service import CurrencyService
        
        # Fiyat belirleme
        if self.variant:
            price = self.variant.price
        else:
            price = self.product.price
            
        product_currency = self.product.currency or 'TRY'
        cart_currency = self.cart.currency or 'TRY'
        
        # Para birimi farklıysa sepet para birimine çevir
        if product_currency != cart_currency:
            try:
                self.unit_price = CurrencyService.convert_amount(
                    price,
                    product_currency,
                    cart_currency
                )
            except Exception as e:
                logger.warning(f"Currency conversion failed for {self.product.name}: {e}")
                self.unit_price = price
        else:
            self.unit_price = price
        
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

