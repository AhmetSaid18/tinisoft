"""
TenantUser service.
Tenant'ın sitesinde kayıt olan müşteriler için servis.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.models import Tenant
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class TenantUserService:
    """TenantUser yönetim servisi."""
    
    @staticmethod
    @transaction.atomic
    def register_tenant_user(
        tenant_id: str,
        email: str,
        password: str,
        first_name: str = '',
        last_name: str = '',
        phone: str = None,
    ):
        """
        Tenant'ın sitesinde müşteri kaydı yapar.
        
        Adımlar:
        1. Tenant'ı bul
        2. Email kontrolü (aynı tenant içinde unique olmalı)
        3. TenantUser oluştur (role=tenant_user)
        """
        # 1. Tenant'ı bul
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            raise ValueError(f"Tenant bulunamadı: {tenant_id}")
        
        # 2. Email kontrolü (aynı tenant içinde unique)
        if User.objects.filter(email=email, tenant=tenant).exists():
            raise ValueError("Bu email adresi bu mağazada zaten kayıtlı.")
        
        # 3. TenantUser oluştur
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=User.UserRole.TENANT_USER,
            tenant=tenant,
        )
        logger.info(f"TenantUser created: {user.email} for tenant: {tenant.name}")
        
        return {
            'user': user,
            'tenant': tenant,
        }
    
    @staticmethod
    def login_tenant_user(email: str, password: str, tenant_id: str = None):
        """
        TenantUser girişi.
        Tenant ID verilirse, sadece o tenant'a ait user'lar giriş yapabilir.
        JWT token döndürür.
        """
        from django.contrib.auth import authenticate
        from apps.utils.jwt_utils import generate_jwt_token
        
        # User'ı bul
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValueError("Email veya şifre hatalı.")
        
        # Tenant kontrolü
        if tenant_id:
            if str(user.tenant_id) != tenant_id:
                raise ValueError("Bu email adresi bu mağazaya ait değil.")
        
        # TenantUser kontrolü
        if user.role != User.UserRole.TENANT_USER:
            raise ValueError("Bu hesap müşteri hesabı değil.")
        
        # Authentication
        authenticated_user = authenticate(username=email, password=password)
        if not authenticated_user:
            raise ValueError("Email veya şifre hatalı.")
        
        if not authenticated_user.is_active:
            raise ValueError("Hesabınız aktif değil.")
        
        # JWT token oluştur
        token = generate_jwt_token(authenticated_user)
        
        return {
            'user': authenticated_user,
            'tenant': authenticated_user.tenant,
            'token': token,
        }

