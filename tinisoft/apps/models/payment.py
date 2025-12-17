"""
Ödeme modelleri - Tenant-specific.
İkas benzeri ödeme yönetimi.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import BaseModel


class Payment(BaseModel):
    """
    Ödeme modeli.
    Tenant-specific - her tenant'ın kendi schema'sında.
    """
    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = 'credit_card', 'Kredi Kartı'
        DEBIT_CARD = 'debit_card', 'Banka Kartı'
        BANK_TRANSFER = 'bank_transfer', 'Banka Havalesi'
        CASH_ON_DELIVERY = 'cash_on_delivery', 'Kapıda Ödeme'
        WALLET = 'wallet', 'Cüzdan'
        OTHER = 'other', 'Diğer'
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Beklemede'
        PROCESSING = 'processing', 'İşleniyor'
        COMPLETED = 'completed', 'Tamamlandı'
        FAILED = 'failed', 'Başarısız'
        CANCELLED = 'cancelled', 'İptal Edildi'
        REFUNDED = 'refunded', 'İade Edildi'
        PARTIALLY_REFUNDED = 'partially_refunded', 'Kısmen İade Edildi'
    
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='payments',
        db_index=True,
    )
    
    # Sipariş ilişkisi
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        related_name='payments',
    )
    
    # Ödeme bilgileri
    payment_number = models.CharField(max_length=50, unique=True, db_index=True)
    method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    
    # Tutar
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    currency = models.CharField(max_length=3, default='TRY')
    
    # Ödeme sağlayıcı bilgileri
    provider = models.CharField(
        max_length=50,
        blank=True,
        help_text="Ödeme sağlayıcı (iyzico, paytr, vb.)"
    )
    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Ödeme sağlayıcı transaction ID"
    )
    payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Payment intent ID (iyzico, paytr vb.)"
    )
    
    # Tarih bilgileri
    paid_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    # Hata bilgileri
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=50, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(
        default=dict,
        help_text="Ek bilgiler (JSON format)"
    )
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['order']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['payment_number']),
        ]
    
    def __str__(self):
        return f"Payment #{self.payment_number} - {self.amount} {self.currency} ({self.get_status_display()})"

