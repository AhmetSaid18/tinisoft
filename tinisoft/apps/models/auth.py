"""
Authentication and Tenant models.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid
from core.models import BaseModel


class User(AbstractUser):
    """
    Custom User model.
    Roller: Owner, TenantUser, TenantBayii, SystemAdmin
    """
    class UserRole(models.TextChoices):
        OWNER = 'owner', 'Owner'  # Tinisoft (program sahibi, biz)
        TENANT_OWNER = 'tenant_owner', 'Tenant Owner'  # Mağaza sahibi (tenant sahibi)
        TENANT_STAFF = 'tenant_staff', 'Tenant Staff'  # Mağaza personeli
        TENANT_USER = 'tenant_user', 'Tenant User'  # Tenant'ın sitesinde kayıt olan müşteriler
        TENANT_BAYII = 'tenant_bayii', 'Tenant Bayii'  # Tenant'ın bayileri
        SYSTEM_ADMIN = 'system_admin', 'System Admin'  # Sistem yöneticisi
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Tenant ilişkisi (TenantOwner, TenantUser, TenantBayii için)
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        help_text="User'ın bağlı olduğu tenant (TenantOwner, TenantUser, TenantBayii için)"
    )
    
    # User rolü
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.TENANT_USER,
        db_index=True,
        help_text="User rolü: Owner, TenantUser, TenantBayii, SystemAdmin"
    )
    
    # Personel Yetkileri (JSON formatında saklanır)
    # Örn: ["products", "orders", "coupons", "customers", "inventory"]
    staff_permissions = models.JSONField(
        default=list,
        blank=True,
        help_text="Personel (TenantStaff) yetki listesi."
    )
    
    # AbstractUser'dan gelen groups ve user_permissions için related_name override
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='custom_user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='user',
    )
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        unique_together = ('email', 'tenant') # Aynı email aynı tenant'ta 2 kere olamaz ama farklı tenant'larda olabilir.
        indexes = [
            models.Index(fields=['tenant', 'role']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    @property
    def is_owner(self):
        """Owner mı? (Tinisoft - program sahibi)"""
        return self.role == self.UserRole.OWNER
    
    @property
    def is_tenant_owner(self):
        """TenantOwner mı? (Mağaza sahibi)"""
        return self.role == self.UserRole.TENANT_OWNER
    
    @property
    def is_tenant_staff(self):
        """TenantStaff mi?"""
        return self.role == self.UserRole.TENANT_STAFF
    
    @property
    def is_tenant_user(self):
        """TenantUser mı?"""
        return self.role == self.UserRole.TENANT_USER
    
    @property
    def is_tenant_bayii(self):
        """TenantBayii mi?"""
        return self.role == self.UserRole.TENANT_BAYII
    
    @property
    def is_system_admin(self):
        """SystemAdmin mi?"""
        return self.role == self.UserRole.SYSTEM_ADMIN

    def has_staff_permission(self, permission):
        """
        Personelin belirli bir yetkiye sahip olup olmadığını kontrol et.
        TenantOwner tüm yetkilere sahiptir.
        """
        if self.is_tenant_owner or self.is_owner:
            return True
        if self.is_tenant_staff:
            return permission in self.staff_permissions
        return False


    def save(self, *args, **kwargs):
        """Save override to clear cache on update."""
        # Cache'i temizle (permissions ve role değişmiş olabilir)
        if self.id:
            from apps.services.cache_service import CacheService
            CacheService.delete_user_permissions(self.id)
        super().save(*args, **kwargs)


class Tenant(BaseModel):
    """
    Tenant (Mağaza) modeli.
    Her tenant bir mağaza temsil eder.
    """
    name = models.CharField(max_length=255, db_index=True)  # Mağaza adı
    slug = models.SlugField(max_length=255, unique=True, db_index=True)  # URL-friendly mağaza adı
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_tenants',
        limit_choices_to={'role': 'tenant_owner'},
        help_text="Tenant sahibi (TenantOwner rolünde user - mağaza sahibi)"
    )
    
    # Domain bilgileri
    subdomain = models.CharField(max_length=255, unique=True, db_index=True)  # Örn: magaza-adi
    custom_domain = models.CharField(max_length=255, blank=True, null=True, db_index=True)  # Örn: example.com
    
    # Durum
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),  # Kayıt olmuş, domain doğrulanmamış
            ('active', 'Active'),     # Aktif, yayında
            ('suspended', 'Suspended'),  # Askıya alınmış
            ('deleted', 'Deleted'),   # Silinmiş
        ],
        default='pending',
        db_index=True
    )
    
    # Plan bilgileri
    plan = models.CharField(
        max_length=50,
        choices=[
            ('free', 'Free'),
            ('basic', 'Basic'),
            ('pro', 'Pro'),
            ('enterprise', 'Enterprise'),
        ],
        default='free'
    )
    
    # Frontend URL (custom domain veya subdomain)
    def get_frontend_url(self):
        """Frontend URL'ini döndür."""
        if self.custom_domain:
            return f"https://{self.custom_domain}"
        return f"https://{self.subdomain}.domains.tinisoft.com.tr"
    
    def get_primary_frontend_url(self):
        """
        Primary domain'den frontend URL'ini döndür.
        Öncelik sırası:
        1. Tenant'ın custom_domain field'ı (doğrulama gerektirmez)
        2. Primary domain (Domain modelinden, doğrulama gerektirmez)
        3. Fallback: subdomain URL
        
        Not: Doğrulama kontrolü yapılmaz, domain kendisindeyse zaten yayın olacak.
        """
        # Önce Tenant'ın custom_domain field'ını kontrol et
        if self.custom_domain:
            return f"https://{self.custom_domain}"
        
        # Sonra Domain modelinden primary domain'i bul (verification_status kontrolü yok)
        primary_domain = self.domains.filter(
            is_primary=True,
            is_deleted=False
        ).first()
        
        if primary_domain:
            return f"https://{primary_domain.domain_name}"
        
        # Primary domain yoksa herhangi bir domain'i kullan
        any_domain = self.domains.filter(
            is_deleted=False
        ).order_by('-is_primary', '-is_custom', '-created_at').first()
        
        if any_domain:
            return f"https://{any_domain.domain_name}"
        
        # Fallback: subdomain URL
        return self.get_frontend_url()
    
    # Frontend Template
    template = models.CharField(
        max_length=100,
        default='default',
        help_text="Frontend template adı (default, modern, classic, vb.)"
    )
    
    # Global ürün ayarları
    show_compare_at_price = models.BooleanField(
        default=True,
        help_text="Tüm ürünlerin karşılaştırma fiyatını public (storefront) endpoint'lerde göster. False ise hiçbir üründe gösterilmez."
    )
    
    # Metadata
    activated_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(
        default=dict,
        help_text="Ek bilgiler (JSON format) - Payment provider configs, vb."
    )
    
    class Meta:
        db_table = 'tenants'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['subdomain']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.slug})"
    
    def get_subdomain_url(self):
        """Subdomain URL'ini döndür."""
        # Örn: ates.tinisoft.com.tr
        return f"https://{self.subdomain}.tinisoft.com.tr"
    
    def get_custom_domain_url(self):
        """Custom domain URL'ini döndür."""
        if self.custom_domain:
            return f"https://{self.custom_domain}"
        return None
    
    def activate(self):
        """Tenant'ı aktif et."""
        self.status = 'active'
        self.activated_at = timezone.now()
        self.save()
    
    def suspend(self):
        """Tenant'ı askıya al."""
        self.status = 'suspended'
        self.suspended_at = timezone.now()
        self.save()

