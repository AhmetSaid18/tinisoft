"""
Müşteri modelleri - Tenant-specific.
İkas benzeri müşteri yönetimi.
"""
from django.db import models
from django.utils import timezone
from core.models import BaseModel


class Customer(BaseModel):
    """
    Müşteri modeli.
    Tenant-specific - her tenant'ın kendi schema'sında.
    
    Not: User modeli ile ilişkili ama ayrı bir model çünkü:
    - Müşteri bilgileri tenant'a özgü
    - Müşteri segmentasyonu, istatistikler vb. için
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='customers',
        db_index=True,
    )
    
    # User ilişkisi (TenantUser)
    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='customer_profile',
        help_text="Müşteri user'ı (TenantUser rolünde)"
    )
    
    # Müşteri bilgileri
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Erkek'),
            ('female', 'Kadın'),
            ('other', 'Diğer'),
        ],
        blank=True,
    )
    
    # İstatistikler
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Toplam harcama"
    )
    average_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Ortalama sipariş değeri"
    )
    
    # Durum
    is_active = models.BooleanField(default=True, db_index=True)
    is_verified = models.BooleanField(
        default=False,
        help_text="Email doğrulandı mı?"
    )
    is_newsletter_subscribed = models.BooleanField(
        default=False,
        help_text="Bülten aboneliği"
    )
    
    # Segmentasyon
    customer_group = models.CharField(
        max_length=50,
        blank=True,
        help_text="Müşteri grubu (VIP, Regular, vb.)"
    )
    tags = models.JSONField(
        default=list,
        help_text="Müşteri etiketleri (JSON array)"
    )
    
    # Tarih bilgileri
    first_order_at = models.DateTimeField(null=True, blank=True)
    last_order_at = models.DateTimeField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True, help_text="Admin notları")
    metadata = models.JSONField(
        default=dict,
        help_text="Ek bilgiler (JSON format)"
    )
    
    class Meta:
        db_table = 'customers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['tenant', 'user']),
            models.Index(fields=['customer_group']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.tenant.name})"
    
    def update_statistics(self):
        """Müşteri istatistiklerini güncelle."""
        from .order import Order
        
        orders = Order.objects.filter(
            tenant=self.tenant,
            customer=self.user,
            is_deleted=False,
        )
        
        self.total_orders = orders.count()
        
        if self.total_orders > 0:
            self.total_spent = sum(order.total for order in orders)
            self.average_order_value = self.total_spent / self.total_orders
            
            # İlk ve son sipariş tarihleri
            first_order = orders.order_by('created_at').first()
            last_order = orders.order_by('-created_at').first()
            
            if first_order:
                self.first_order_at = first_order.created_at
            if last_order:
                self.last_order_at = last_order.created_at
        
        self.save()

