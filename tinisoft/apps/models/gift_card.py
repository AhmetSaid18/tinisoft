"""
Hediye kartı modelleri - Tenant-specific.
İkas benzeri gift card sistemi.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel


class GiftCard(BaseModel):
    """
    Hediye kartı.
    Tenant-specific - her tenant'ın kendi hediye kartları.
    """
    class GiftCardType(models.TextChoices):
        FIXED = 'fixed', 'Sabit Tutar'
        PERCENTAGE = 'percentage', 'Yüzde'
    
    class GiftCardStatus(models.TextChoices):
        ACTIVE = 'active', 'Aktif'
        USED = 'used', 'Kullanıldı'
        EXPIRED = 'expired', 'Süresi Doldu'
        CANCELLED = 'cancelled', 'İptal Edildi'
    
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='gift_cards',
        db_index=True,
    )
    
    # Kart bilgileri
    code = models.CharField(max_length=50, unique=True, db_index=True, help_text="Kart kodu")
    type = models.CharField(
        max_length=20,
        choices=GiftCardType.choices,
        default=GiftCardType.FIXED,
    )
    
    # Tutar
    initial_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Başlangıç tutarı"
    )
    current_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Kalan tutar"
    )
    percentage_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Yüzde değeri (percentage tipinde)"
    )
    
    # Sahiplik
    customer = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gift_cards',
        help_text="Kart sahibi (opsiyonel)"
    )
    customer_email = models.EmailField(
        blank=True,
        help_text="Kart sahibi e-posta (guest için)"
    )
    
    # Tarih aralığı
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Durum
    status = models.CharField(
        max_length=20,
        choices=GiftCardStatus.choices,
        default=GiftCardStatus.ACTIVE,
        db_index=True,
    )
    
    # Kullanım bilgileri
    usage_count = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    # Notlar
    note = models.TextField(blank=True, help_text="Kart notu")
    
    class Meta:
        db_table = 'gift_cards'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'code']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['customer']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        return f"Gift Card {self.code} - {self.current_amount} {self.tenant.name}"
    
    def is_valid(self):
        """Kart geçerli mi?"""
        if self.status != self.GiftCardStatus.ACTIVE:
            return False, "Kart aktif değil."
        
        if self.valid_until and timezone.now() > self.valid_until:
            return False, "Kart süresi dolmuş."
        
        if timezone.now() < self.valid_from:
            return False, "Kart henüz geçerli değil."
        
        if self.type == self.GiftCardType.FIXED and self.current_amount <= Decimal('0.00'):
            return False, "Kart bakiyesi yetersiz."
        
        return True, "Kart geçerli."
    
    def calculate_discount(self, order_amount):
        """İndirim tutarını hesapla."""
        if self.type == self.GiftCardType.FIXED:
            return min(self.current_amount, order_amount)
        elif self.type == self.GiftCardType.PERCENTAGE and self.percentage_value:
            discount = order_amount * (self.percentage_value / Decimal('100'))
            if self.initial_amount:  # Maksimum limit varsa
                return min(discount, self.initial_amount)
            return discount
        return Decimal('0.00')
    
    def use(self, amount):
        """Kartı kullan."""
        if self.type == self.GiftCardType.FIXED:
            if amount > self.current_amount:
                raise ValueError("Yetersiz bakiye.")
            self.current_amount -= amount
            if self.current_amount <= Decimal('0.00'):
                self.status = self.GiftCardStatus.USED
        
        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save()


class GiftCardTransaction(BaseModel):
    """
    Hediye kartı işlem kaydı.
    """
    gift_card = models.ForeignKey(
        GiftCard,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    
    # İşlem bilgileri
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('purchase', 'Satın Alma'),
            ('usage', 'Kullanım'),
            ('refund', 'İade'),
            ('expiry', 'Süre Dolması'),
        ],
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="İşlem tutarı"
    )
    
    # İlişkili kayıtlar
    order = models.ForeignKey(
        'Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gift_card_transactions',
    )
    
    # Notlar
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'gift_card_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gift_card']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} - {self.gift_card.code}"

