"""
Shipping model - Tenant-specific.
Her tenant'ın kendi schema'sında shipping tabloları olur.
"""
from django.db import models
from core.models import BaseModel


class ShippingMethod(BaseModel):
    """
    Kargo yöntemi modeli.
    Tenant-specific - her tenant'ın kendi kargo yöntemleri.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='shipping_methods',
        db_index=True
    )
    name = models.CharField(max_length=255)  # Örn: "Aras Kargo", "MNG Kargo"
    code = models.CharField(max_length=50, db_index=True)  # Örn: "aras", "mng"
    is_active = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'shipping_methods'
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class ShippingAddress(BaseModel):
    """
    Kargo adresi modeli.
    Tenant-specific - her tenant'ın müşterilerinin adresleri.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='shipping_addresses',
        db_index=True
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='shipping_addresses'
    )
    
    # Adres tipi (fatura veya kargo)
    address_type = models.CharField(
        max_length=20,
        choices=[
            ('billing', 'Fatura Adresi'),
            ('shipping', 'Kargo Adresi'),
        ],
        default='shipping',
        db_index=True
    )
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='Turkey')
    is_default = models.BooleanField(default=False)
    
    # Fatura adresi için vergi bilgileri (sadece address_type='billing' için)
    tax_id = models.CharField(max_length=20, blank=True, null=True, help_text='Vergi Numarası / TC Kimlik No')
    tax_office = models.CharField(max_length=100, blank=True, null=True, help_text='Vergi Dairesi')
    company_name = models.CharField(max_length=255, blank=True, null=True, help_text='Şirket/Firma Adı')
    
    class Meta:
        db_table = 'shipping_addresses'
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['tenant', 'user']),
            models.Index(fields=['tenant', 'user', 'address_type']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.city}"
    
    @property
    def full_address(self):
        """Tam adres string'i."""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            f"{self.postal_code} {self.city}",
            self.state,
            self.country
        ]
        return ", ".join([part for part in address_parts if part])

