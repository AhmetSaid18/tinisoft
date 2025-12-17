"""
Webhook modelleri - Tenant-specific.
İkas benzeri webhook sistemi.
"""
from django.db import models
from core.models import BaseModel
import uuid


def generate_webhook_secret():
    """Webhook secret key oluştur."""
    return str(uuid.uuid4())


class Webhook(BaseModel):
    """
    Webhook tanımı.
    Tenant-specific - her tenant'ın kendi webhook'ları.
    """
    class WebhookStatus(models.TextChoices):
        ACTIVE = 'active', 'Aktif'
        INACTIVE = 'inactive', 'Pasif'
    
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='webhooks',
        db_index=True,
    )
    
    name = models.CharField(max_length=255, help_text="Webhook adı")
    url = models.URLField(max_length=1000, help_text="Webhook URL'i")
    
    # Event'ler
    events = models.JSONField(
        default=list,
        help_text="Dinlenecek event'ler (JSON array)"
    )
    
    # Secret key (güvenlik için)
    secret_key = models.CharField(
        max_length=255,
        default=generate_webhook_secret,
        help_text="Webhook secret key (signature için)"
    )
    
    # Durum
    status = models.CharField(
        max_length=20,
        choices=WebhookStatus.choices,
        default=WebhookStatus.ACTIVE,
        db_index=True,
    )
    
    # İstatistikler
    success_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'webhooks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.url} ({self.tenant.name})"


class WebhookEvent(BaseModel):
    """
    Webhook event kaydı.
    """
    webhook = models.ForeignKey(
        Webhook,
        on_delete=models.CASCADE,
        related_name='webhook_events',
    )
    
    # Event bilgileri
    event_type = models.CharField(max_length=100, db_index=True, help_text="Event tipi")
    payload = models.JSONField(default=dict, help_text="Event payload")
    
    # İstek bilgileri
    request_url = models.URLField(max_length=1000)
    request_method = models.CharField(max_length=10, default='POST')
    request_headers = models.JSONField(default=dict)
    request_body = models.TextField(blank=True)
    
    # Yanıt bilgileri
    response_status = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    
    # Durum
    is_success = models.BooleanField(default=False, db_index=True)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'webhook_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['webhook', 'is_success']),
            models.Index(fields=['event_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.webhook.name} ({'Success' if self.is_success else 'Failed'})"

