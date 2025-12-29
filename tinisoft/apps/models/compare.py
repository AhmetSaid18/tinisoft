"""
Product comparison models - Tenant-specific.
Ürün karşılaştırma sistemi.
"""
from django.db import models
from core.models import BaseModel


class ProductCompare(BaseModel):
    """
    Ürün karşılaştırma listesi.
    Tenant-specific - her tenant'ın kendi karşılaştırma listeleri.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='compare_lists',
        db_index=True,
    )
    
    # Kullanıcı (opsiyonel - session-based olabilir)
    customer = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='compare_lists',
        null=True,
        blank=True,
        help_text="Kullanıcı giriş yapmışsa, yoksa session-based"
    )
    
    # Session ID (giriş yapmamış kullanıcılar için)
    session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text="Session ID (giriş yapmamış kullanıcılar için)"
    )
    
    # Maksimum karşılaştırma sayısı (default: 4)
    max_items = models.PositiveIntegerField(default=4)
    
    class Meta:
        db_table = 'product_compares'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'customer']),
            models.Index(fields=['tenant', 'session_id']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'customer'],
                condition=models.Q(customer__isnull=False),
                name='unique_tenant_customer_compare'
            ),
            models.UniqueConstraint(
                fields=['tenant', 'session_id'],
                condition=models.Q(session_id__isnull=False),
                name='unique_tenant_session_compare'
            ),
        ]
    
    def __str__(self):
        if self.customer:
            return f"Compare list - {self.customer.email} ({self.tenant.name})"
        return f"Compare list - {self.session_id} ({self.tenant.name})"
    
    def add_product(self, product):
        """Ürün ekle (maksimum sayı kontrolü ile)."""
        if self.items.filter(is_deleted=False).count() >= self.max_items:
            raise ValueError(f"Maksimum {self.max_items} ürün karşılaştırılabilir.")
        
        if self.items.filter(product=product, is_deleted=False).exists():
            raise ValueError("Bu ürün zaten karşılaştırma listesinde.")
        
        return CompareItem.objects.create(
            compare_list=self,
            product=product
        )
    
    def remove_product(self, product):
        """Ürün çıkar."""
        item = self.items.filter(product=product, is_deleted=False).first()
        if item:
            item.soft_delete()
            return True
        return False
    
    def clear(self):
        """Tüm ürünleri temizle."""
        self.items.filter(is_deleted=False).update(is_deleted=True)


class CompareItem(BaseModel):
    """
    Karşılaştırma listesindeki ürün.
    """
    compare_list = models.ForeignKey(
        ProductCompare,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='compare_items'
    )
    
    # Sıralama
    position = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'compare_items'
        ordering = ['position', 'created_at']
        unique_together = [['compare_list', 'product']]
        indexes = [
            models.Index(fields=['compare_list', 'is_deleted']),
        ]
    
    def __str__(self):
        return f"{self.product.name} in {self.compare_list}"

