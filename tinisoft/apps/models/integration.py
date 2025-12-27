"""
Integration API Keys modelleri - Tenant-specific.
Tüm entegrasyonlar için API key yönetimi (Kuveyt, Aras, Yurtiçi, Trendyol, Vakıf, vb.)
"""
from django.db import models
from django.core.validators import MinLengthValidator
from core.models import BaseModel
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import json
import logging

logger = logging.getLogger(__name__)


def get_encryption_key():
    """Encryption key'i al (settings'ten veya default)."""
    key = getattr(settings, 'INTEGRATION_ENCRYPTION_KEY', None)
    if not key:
        # Development için default key (production'da mutlaka değiştirilmeli!)
        key = Fernet.generate_key().decode()
        logger.warning("Using auto-generated encryption key. Set INTEGRATION_ENCRYPTION_KEY in settings for production!")
    elif isinstance(key, str):
        # String ise bytes'a çevir
        key = key.encode()
    return key


class IntegrationProvider(BaseModel):
    """
    Entegrasyon sağlayıcı modeli.
    Tenant-specific - her tenant'ın kendi entegrasyonları.
    """
    class ProviderType(models.TextChoices):
        # Ödeme Sağlayıcıları
        KUVEYT = 'kuveyt', 'Kuveyt API'
        IYZICO = 'iyzico', 'İyzico'
        PAYTR = 'paytr', 'PayTR'
        VAKIF = 'vakif', 'Vakıf Bankası'
        GARANTI = 'garanti', 'Garanti Bankası'
        AKBANK = 'akbank', 'Akbank'
        
        # Kargo Sağlayıcıları
        ARAS = 'aras', 'Aras Kargo'
        YURTICI = 'yurtici', 'Yurtiçi Kargo'
        MNG = 'mng', 'MNG Kargo'
        SENDEX = 'sendex', 'Sendex'
        TRENDYOL = 'trendyol', 'Trendyol Express'
        
        # E-Ticaret Platformları
        TRENDYOL_MARKETPLACE = 'trendyol_marketplace', 'Trendyol Marketplace'
        HEPSIBURADA = 'hepsiburada', 'Hepsiburada'
        N11 = 'n11', 'N11'
        GITTIGIDIYOR = 'gittigidiyor', 'GittiGidiyor'
        
        # Diğer Entegrasyonlar
        SMS = 'sms', 'SMS Servisi'
        EMAIL = 'email', 'Email Servisi'
        ANALYTICS = 'analytics', 'Analytics'
        OTHER = 'other', 'Diğer'
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Aktif'
        INACTIVE = 'inactive', 'Pasif'
        TEST_MODE = 'test_mode', 'Test Modu'
    
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='integrations',
        db_index=True,
    )
    
    # Entegrasyon bilgileri
    provider_type = models.CharField(
        max_length=50,
        choices=ProviderType.choices,
        db_index=True,
        help_text="Entegrasyon tipi"
    )
    name = models.CharField(
        max_length=255,
        help_text="Entegrasyon adı (örn: Kuveyt API - Test)"
    )
    description = models.TextField(blank=True)
    
    # Durum
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INACTIVE,
        db_index=True,
        help_text="Entegrasyon durumu"
    )
    
    # API Bilgileri (şifreli)
    api_key = models.TextField(
        blank=True,
        help_text="API Key (şifreli)"
    )
    api_secret = models.TextField(
        blank=True,
        help_text="API Secret (şifreli)"
    )
    api_token = models.TextField(
        blank=True,
        help_text="API Token (şifreli)"
    )
    
    # Endpoint ve Config
    api_endpoint = models.URLField(
        blank=True,
        help_text="API Endpoint URL"
    )
    test_endpoint = models.URLField(
        blank=True,
        help_text="Test API Endpoint URL"
    )
    
    # Ekstra config (JSON - şifreli değil, hassas bilgi içermemeli)
    config = models.JSONField(
        default=dict,
        help_text="Ekstra konfigürasyon (merchant_id, vb. - hassas bilgi içermemeli)"
    )
    
    # Metadata
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, help_text="Son hata mesajı")
    
    class Meta:
        db_table = 'integration_providers'
        ordering = ['provider_type', 'name']
        indexes = [
            models.Index(fields=['tenant', 'provider_type']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['provider_type', 'status']),
        ]
        # Her tenant için her provider_type'tan sadece 1 tane olabilir
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'provider_type'],
                condition=models.Q(is_deleted=False),
                name='unique_active_integration_per_tenant'
            )
        ]
    
    def __str__(self):
        return f"{self.get_provider_type_display()} - {self.name} ({self.tenant.name})"
    
    def encrypt_value(self, value):
        """Değeri şifrele."""
        if not value:
            return ''
        try:
            fernet = Fernet(get_encryption_key())
            encrypted = fernet.encrypt(value.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            raise ValueError(f"Şifreleme hatası: {str(e)}")
    
    def decrypt_value(self, encrypted_value):
        """Şifreli değeri çöz."""
        if not encrypted_value:
            return ''
        try:
            fernet = Fernet(get_encryption_key())
            decrypted = fernet.decrypt(encrypted_value.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            raise ValueError(f"Şifre çözme hatası: {str(e)}")
    
    def set_api_key(self, value):
        """API key'i şifreleyerek kaydet."""
        self.api_key = self.encrypt_value(value) if value else ''
    
    def get_api_key(self):
        """API key'i çözerek döndür."""
        return self.decrypt_value(self.api_key) if self.api_key else ''
    
    def set_api_secret(self, value):
        """API secret'ı şifreleyerek kaydet."""
        self.api_secret = self.encrypt_value(value) if value else ''
    
    def get_api_secret(self):
        """API secret'ı çözerek döndür."""
        return self.decrypt_value(self.api_secret) if self.api_secret else ''
    
    def set_api_token(self, value):
        """API token'ı şifreleyerek kaydet."""
        self.api_token = self.encrypt_value(value) if value else ''
    
    def get_api_token(self):
        """API token'ı çözerek döndür."""
        return self.decrypt_value(self.api_token) if self.api_token else ''
    
    def get_endpoint(self):
        """Test modunda ise test endpoint, değilse normal endpoint döndür."""
        if self.status == self.Status.TEST_MODE and self.test_endpoint:
            return self.test_endpoint
        return self.api_endpoint
    
    def get_provider_config(self):
        """Provider config dict'i döndür (payment_providers için)."""
        return {
            'api_key': self.get_api_key(),
            'api_secret': self.get_api_secret(),
            'api_token': self.get_api_token(),
            'endpoint': self.get_endpoint(),
            'test_mode': self.status == self.Status.TEST_MODE,
            **self.config
        }
    
    def save(self, *args, **kwargs):
        """Save öncesi şifreleme kontrolü."""
        # Eğer api_key, api_secret, api_token düz metin olarak gelmişse şifrele
        # (zaten şifreli ise değiştirme)
        if self.api_key and not self.api_key.startswith('gAAAAAB'):  # Fernet encrypted prefix
            self.api_key = self.encrypt_value(self.api_key)
        if self.api_secret and not self.api_secret.startswith('gAAAAAB'):
            self.api_secret = self.encrypt_value(self.api_secret)
        if self.api_token and not self.api_token.startswith('gAAAAAB'):
            self.api_token = self.encrypt_value(self.api_token)
        
        super().save(*args, **kwargs)

