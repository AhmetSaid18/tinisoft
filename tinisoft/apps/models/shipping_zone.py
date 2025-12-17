"""
Kargo bölgeleri modelleri - Tenant-specific.
İkas benzeri shipping zone sistemi.
"""
from django.db import models
from decimal import Decimal
from core.models import BaseModel


class ShippingZone(BaseModel):
    """
    Kargo bölgesi.
    Tenant-specific - her tenant'ın kendi bölgeleri.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='shipping_zones',
        db_index=True,
    )
    
    name = models.CharField(max_length=255, help_text="Bölge adı (İstanbul, Ankara, vb.)")
    description = models.TextField(blank=True)
    
    # Bölge tanımlaması
    countries = models.JSONField(
        default=list,
        help_text="Ülkeler (JSON array, örn: ['TR', 'US'])"
    )
    cities = models.JSONField(
        default=list,
        help_text="Şehirler (JSON array, boş = tüm şehirler)"
    )
    postal_codes = models.JSONField(
        default=list,
        help_text="Posta kodları (JSON array, boş = tüm posta kodları)"
    )
    
    # Durum
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        db_table = 'shipping_zones'
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"
    
    def matches(self, country, city=None, postal_code=None):
        """Bölge bu adresle eşleşiyor mu?"""
        if country not in self.countries:
            return False
        
        if self.cities and city and city not in self.cities:
            return False
        
        if self.postal_codes and postal_code and postal_code not in self.postal_codes:
            return False
        
        return True


class ShippingZoneRate(BaseModel):
    """
    Kargo bölgesi fiyatlandırması.
    Her bölge için farklı kargo ücretleri.
    """
    zone = models.ForeignKey(
        ShippingZone,
        on_delete=models.CASCADE,
        related_name='rates',
    )
    shipping_method = models.ForeignKey(
        'ShippingMethod',
        on_delete=models.CASCADE,
        related_name='zone_rates',
    )
    
    # Fiyatlandırma
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Sabit kargo ücreti"
    )
    free_shipping_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Bu tutarın üzerinde ücretsiz kargo"
    )
    
    # Ağırlık bazlı fiyatlandırma
    weight_based_pricing = models.BooleanField(
        default=False,
        help_text="Ağırlık bazlı fiyatlandırma kullan"
    )
    base_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Temel ağırlık (kg)"
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Temel ağırlık için fiyat"
    )
    additional_weight_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Ek ağırlık başına fiyat (kg başına)"
    )
    
    # Durum
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'shipping_zone_rates'
        ordering = ['shipping_method', 'zone']
        unique_together = ('zone', 'shipping_method')
        indexes = [
            models.Index(fields=['zone', 'shipping_method']),
        ]
    
    def __str__(self):
        return f"{self.shipping_method.name} - {self.zone.name} ({self.price} TL)"
    
    def calculate_shipping_cost(self, order_amount=Decimal('0.00'), total_weight=Decimal('0.00')):
        """Kargo ücretini hesapla."""
        # Ücretsiz kargo kontrolü
        if self.free_shipping_threshold and order_amount >= self.free_shipping_threshold:
            return Decimal('0.00')
        
        # Ağırlık bazlı fiyatlandırma
        if self.weight_based_pricing:
            if total_weight <= self.base_weight:
                return self.base_price
            else:
                additional_weight = total_weight - self.base_weight
                additional_cost = additional_weight * self.additional_weight_price
                return self.base_price + additional_cost
        
        # Sabit fiyat
        return self.price

