"""
Sadakat puanları modelleri - Tenant-specific.
İkas benzeri loyalty points sistemi.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import BaseModel


class LoyaltyProgram(BaseModel):
    """
    Sadakat programı.
    Tenant-specific - her tenant'ın kendi programı.
    """
    tenant = models.OneToOneField(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='loyalty_program',
    )
    
    name = models.CharField(max_length=255, default="Sadakat Programı")
    description = models.TextField(blank=True)
    
    # Puan kazanma kuralları
    points_per_currency = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Her 1 TL için kaç puan? (örn: 1 TL = 1 puan)"
    )
    points_per_order = models.PositiveIntegerField(
        default=0,
        help_text="Her sipariş için ekstra puan"
    )
    
    # Puan kullanma kuralları
    currency_per_point = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.01'),
        help_text="Her 1 puan kaç TL? (örn: 1 puan = 0.01 TL)"
    )
    minimum_points_to_redeem = models.PositiveIntegerField(
        default=100,
        help_text="Kullanmak için minimum puan"
    )
    maximum_points_per_order = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Sipariş başına maksimum kullanılabilir puan (null = sınırsız)"
    )
    
    # Durum
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        db_table = 'loyalty_programs'
    
    def __str__(self):
        return f"{self.name} - {self.tenant.name}"
    
    def calculate_points_earned(self, order_amount):
        """Sipariş tutarına göre kazanılacak puanı hesapla."""
        points = Decimal(str(int(order_amount * self.points_per_currency)))
        points += self.points_per_order
        return int(points)
    
    def calculate_discount_from_points(self, points):
        """Puanlardan indirim tutarını hesapla."""
        if points < self.minimum_points_to_redeem:
            return Decimal('0.00')
        return Decimal(str(points)) * self.currency_per_point


class LoyaltyPoints(BaseModel):
    """
    Müşteri sadakat puanları.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='loyalty_points',
        db_index=True,
    )
    
    customer = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='loyalty_points',
        help_text="Müşteri (TenantUser)"
    )
    
    # Puan bilgileri
    total_points = models.PositiveIntegerField(
        default=0,
        help_text="Toplam kazanılan puan"
    )
    available_points = models.PositiveIntegerField(
        default=0,
        help_text="Kullanılabilir puan"
    )
    used_points = models.PositiveIntegerField(
        default=0,
        help_text="Kullanılan puan"
    )
    expired_points = models.PositiveIntegerField(
        default=0,
        help_text="Süresi dolan puan"
    )
    
    class Meta:
        db_table = 'loyalty_points'
        indexes = [
            models.Index(fields=['tenant', 'customer']),
        ]
    
    def __str__(self):
        return f"{self.customer.email} - {self.available_points} points ({self.tenant.name})"
    
    def add_points(self, points, reason=''):
        """Puan ekle."""
        self.total_points += points
        self.available_points += points
        self.save()
        
        # İşlem kaydı oluştur
        LoyaltyTransaction.objects.create(
            loyalty_points=self,
            transaction_type='earned',
            points=points,
            reason=reason,
        )
    
    def use_points(self, points, reason=''):
        """Puan kullan."""
        if points > self.available_points:
            raise ValueError("Yetersiz puan.")
        
        self.available_points -= points
        self.used_points += points
        self.save()
        
        # İşlem kaydı oluştur
        LoyaltyTransaction.objects.create(
            loyalty_points=self,
            transaction_type='used',
            points=points,
            reason=reason,
        )


class LoyaltyTransaction(BaseModel):
    """
    Sadakat puanı işlem kaydı.
    """
    loyalty_points = models.ForeignKey(
        LoyaltyPoints,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    
    # İşlem bilgileri
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('earned', 'Kazanıldı'),
            ('used', 'Kullanıldı'),
            ('expired', 'Süresi Doldu'),
            ('refunded', 'İade Edildi'),
        ],
    )
    points = models.PositiveIntegerField(help_text="İşlem puanı")
    
    # İlişkili kayıtlar
    order = models.ForeignKey(
        'Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loyalty_transactions',
    )
    
    # Notlar
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'loyalty_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['loyalty_points']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.points} points - {self.loyalty_points.customer.email}"

