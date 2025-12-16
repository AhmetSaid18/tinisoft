"""
Domain management models.
"""
from django.db import models
from django.utils import timezone
from core.models import BaseModel


class Domain(BaseModel):
    """
    Domain modeli.
    Her tenant birden fazla domain'e sahip olabilir.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='domains'
    )
    domain_name = models.CharField(max_length=255, unique=True, db_index=True)
    is_primary = models.BooleanField(default=False)  # Ana domain mi?
    is_custom = models.BooleanField(default=True)  # Custom domain mi yoksa subdomain mi?
    
    # Doğrulama durumu
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('verifying', 'Verifying'),
            ('verified', 'Verified'),
            ('failed', 'Failed'),
        ],
        default='pending',
        db_index=True
    )
    verification_code = models.CharField(max_length=100, blank=True)  # DNS doğrulama kodu
    verified_at = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    
    # SSL Settings
    ssl_enabled = models.BooleanField(default=True)
    ssl_certificate = models.TextField(blank=True, null=True)
    ssl_key = models.TextField(blank=True, null=True)
    ssl_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Traefik Routing
    traefik_router_name = models.CharField(max_length=255, blank=True)
    traefik_service_name = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'domains'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'verification_status']),
            models.Index(fields=['domain_name']),
        ]
    
    def __str__(self):
        return f"{self.domain_name} ({self.tenant.name})"
    
    def verify(self):
        """Domain'i doğrula."""
        from django.utils import timezone
        self.verification_status = 'verified'
        self.verified_at = timezone.now()
        self.last_checked_at = timezone.now()
        self.save()

