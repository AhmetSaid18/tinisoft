"""
Ürün yorumları ve puanlama modelleri - Tenant-specific.
İkas benzeri yorum sistemi.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from core.models import BaseModel


class ProductReview(BaseModel):
    """
    Ürün yorumu.
    Tenant-specific - her tenant'ın kendi yorumları.
    """
    class ReviewStatus(models.TextChoices):
        PENDING = 'pending', 'Beklemede'
        APPROVED = 'approved', 'Onaylandı'
        REJECTED = 'rejected', 'Reddedildi'
    
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='reviews',
        db_index=True,
    )
    
    # Ürün ve müşteri
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    customer = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews',
        help_text="Yorum yapan müşteri (guest için null)"
    )
    
    # Müşteri bilgileri (guest için)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    
    # Yorum içeriği
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Puan (1-5)"
    )
    title = models.CharField(max_length=255, blank=True)
    comment = models.TextField()
    
    # Durum
    status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        db_index=True,
    )
    
    # Onay bilgileri
    approved_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_reviews',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Yardımcı oldu mu?
    helpful_count = models.PositiveIntegerField(default=0)
    
    # Görseller
    images = models.JSONField(
        default=list,
        help_text="Yorum görselleri (JSON array of URLs)"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    verified_purchase = models.BooleanField(
        default=False,
        help_text="Doğrulanmış satın alma (sipariş verdi mi?)"
    )
    
    class Meta:
        db_table = 'product_reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'product', 'status']),
            models.Index(fields=['tenant', 'customer']),
            models.Index(fields=['rating']),
        ]
        unique_together = ('product', 'customer', 'customer_email')
    
    def __str__(self):
        return f"Review for {self.product.name} - {self.rating} stars"


class ReviewHelpful(BaseModel):
    """
    Yorum yardımcı oldu mu? (Like/Dislike)
    """
    review = models.ForeignKey(
        ProductReview,
        on_delete=models.CASCADE,
        related_name='helpful_votes',
    )
    customer = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='helpful_votes',
    )
    is_helpful = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'review_helpful'
        unique_together = ('review', 'customer', 'ip_address')
    
    def __str__(self):
        return f"{'Helpful' if self.is_helpful else 'Not helpful'} - {self.review.product.name}"

