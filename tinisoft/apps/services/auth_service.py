"""
Authentication service.
Register, login ve tenant yönetimi işlemleri.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.models import Tenant, Domain, User  # User modelini direkt import et
from apps.services.tenant_service import TenantService
from apps.services.domain_service import DomainService
from apps.services.website_service import WebsiteService
from apps.tasks.build_task import trigger_frontend_build
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication ve tenant yönetimi servisi."""
    
    @staticmethod
    @transaction.atomic
    def register(
        email: str,
        password: str,
        store_name: str,
        store_slug: str,
        custom_domain: str = '',
        template: str = 'default',
        first_name: str = '',
        last_name: str = '',
        phone: str = None,
    ):
        """
        Kullanıcı ve tenant kaydı yapar.
        
        Adımlar:
        1. User oluştur
        2. Tenant oluştur (subdomain otomatik: store_slug)
        3. Tenant schema oluştur
        4. Domain kayıtları oluştur (subdomain + custom domain)
        5. Frontend build tetikle (async)
        """
        # 1. User oluştur (TenantOwner rolü ile - mağaza sahibi)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=User.UserRole.TENANT_OWNER,  # TenantOwner rolü (mağaza sahibi)
        )
        logger.info(f"User created (TenantOwner): {user.email}")
        
        # 2. Tenant oluştur
        # Template: Custom domain varsa kullanıcının seçtiği, yoksa 'default' (bizim template)
        tenant_template = template if custom_domain else 'default'
        
        tenant = Tenant.objects.create(
            name=store_name,
            slug=store_slug,
            owner=user,
            subdomain=store_slug,  # Subdomain = slug
            custom_domain=custom_domain if custom_domain else None,
            status='pending',
            template=tenant_template,  # Custom domain varsa seçilen, yoksa 'default'
        )
        logger.info(f"Tenant created: {tenant.name} ({tenant.slug})")
        
        # 3. User'a tenant'ı ata (Owner olduğu için)
        user.tenant = tenant
        user.save()
        
        # 4. Tenant schema oluştur
        schema_name = f"tenant_{tenant.id}"
        TenantService.create_tenant_schema(tenant, schema_name)
        logger.info(f"Tenant schema created: {schema_name}")
        
        # 5. Domain kayıtları oluştur
        # Subdomain (otomatik aktif)
        subdomain_domain = Domain.objects.create(
            tenant=tenant,
            # Örn: ates.tinisoft.com.tr
            domain_name=f"{store_slug}.tinisoft.com.tr",
            is_primary=True,
            is_custom=False,
            verification_status='verified',  # Subdomain otomatik doğrulu
        )
        logger.info(f"Subdomain created: {subdomain_domain.domain_name}")
        
        # Custom domain (eğer varsa, doğrulama bekliyor)
        if custom_domain:
            custom_domain_obj = Domain.objects.create(
                tenant=tenant,
                domain_name=custom_domain,
                is_primary=False,
                is_custom=True,
                verification_status='pending',
            )
            # DNS doğrulama kodu oluştur
            verification_code = DomainService.generate_verification_code()
            custom_domain_obj.verification_code = verification_code
            custom_domain_obj.save()
            logger.info(f"Custom domain created: {custom_domain} (verification: {verification_code})")
        
        # 6. Website Template ve Page'leri oluştur (Seeding)
        # Kullanıcının seçtiği template ile dükkanı döşe
        WebsiteService.init_tenant_website(tenant, template_key=template)
        logger.info(f"Website template initialized for tenant: {tenant.slug} with template: {template}")

        # 7. Frontend build tetikle (async)
        # Subdomain için: Bizim template ('default') kullanılır
        # Custom domain için: Kullanıcının seçtiği template kullanılır
        subdomain_template = 'default'  # Subdomain her zaman bizim template ile
        
        trigger_frontend_build.delay(
            str(tenant.id),
            subdomain_domain.domain_name,
            subdomain_template  # Subdomain için bizim template
        )
        logger.info(f"Frontend build triggered for tenant: {tenant.id} (subdomain) with template: {subdomain_template}")
        
        # Custom domain varsa, domain doğrulandığında kendi template'i ile build yapılacak
        if custom_domain:
            logger.info(f"Custom domain will use template: {tenant.template} after verification")
        
        return {
            'user': user,
            'tenant': tenant,
            'subdomain_url': tenant.get_subdomain_url(),
            'custom_domain': custom_domain if custom_domain else None,
            'custom_domain_id': str(custom_domain_obj.id) if custom_domain else None,  # Domain ID
            'verification_code': custom_domain_obj.verification_code if custom_domain else None,
            'template': tenant.template,  # Frontend template adı
        }
    
    @staticmethod
    def login(email: str, password: str):
        """
        Kullanıcı girişi yapar.
        JWT token döndürür.
        """
        from django.contrib.auth import authenticate
        from apps.utils.jwt_utils import generate_jwt_token
        
        user = authenticate(username=email, password=password)
        if not user:
            raise ValueError("Email veya şifre hatalı.")
        
        if not user.is_active:
            raise ValueError("Hesabınız aktif değil.")
        
        # JWT token oluştur
        token = generate_jwt_token(user)
        
        return {
            'user': user,
            'tenant': user.tenant,
            'token': token,
        }
    
    @staticmethod
    def create_tenant_staff(tenant, email, password, first_name='', last_name='', phone=None, staff_permissions=None):
        """
        Mağaza personeli (TenantStaff) oluşturur.
        """
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=User.UserRole.TENANT_STAFF,
            tenant=tenant,
            staff_permissions=staff_permissions or []
        )
        logger.info(f"Tenant Staff created for {tenant.slug}: {user.email}")
        return user

