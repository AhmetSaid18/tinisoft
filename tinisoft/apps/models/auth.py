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
        TENANT_USER = 'tenant_user', 'Tenant User'  # Tenant'ın sitesinde kayıt olan müşteriler
        TENANT_BAYII = 'tenant_bayii', 'Tenant Bayii'  # Tenant'ın bayileri
        SYSTEM_ADMIN = 'system_admin', 'System Admin'  # Sistem yöneticisi
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
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
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
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
    
    # Frontend Template
    template = models.CharField(
        max_length=100,
        default='default',
        help_text="Frontend template adı (default, modern, classic, vb.)"
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

