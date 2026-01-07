"""
TenantUser service.
Tenant'ın sitesinde kayıt olan müşteriler için servis.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.models import Tenant
import logging
import random
from django.core.cache import cache
from apps.services.email_service import EmailService

logger = logging.getLogger(__name__)

User = get_user_model()


class TenantUserService:
    """TenantUser yönetim servisi."""

    @staticmethod
    def send_registration_code(tenant, email: str):
        """
        Kayıt için doğrulama kodu üretir ve mail gönderir.
        """
        # 6 haneli kod üret
        code = str(random.randint(100000, 999999))
        
        # Cache'e kaydet (10 dakika geçerli)
        cache_key = f"reg_code_{tenant.id}_{email}"
        cache.set(cache_key, code, timeout=600)
        
        # Mail gönder
        return EmailService.send_verification_email(tenant, email, code)

    @staticmethod
    def verify_registration_code(tenant, email: str, code: str):
        """
        Doğrulama kodunu kontrol eder.
        """
        cache_key = f"reg_code_{tenant.id}_{email}"
        stored_code = cache.get(cache_key)
        
        if not stored_code:
            return False, "Doğrulama kodu süresi dolmuş veya hiç gönderilmemiş."
        
        if str(stored_code) != str(code):
            return False, "Geçersiz doğrulama kodu."
        
        # Kod doğru, cache'den sil
        cache.delete(cache_key)
        return True, "Kod doğrulandı."
    
    @staticmethod
    @transaction.atomic
    def register_tenant_user(
        tenant_id: str,
        email: str,
        password: str,
        first_name: str = '',
        last_name: str = '',
        phone: str = None,
        is_active: bool = True,
    ):
        """
        Tenant'ın sitesinde müşteri kaydı yapar.
        """
        # 1. Tenant'ı bul
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            raise ValueError(f"Tenant bulunamadı: {tenant_id}")
        
        # 2. Mevcut kullanıcı kontrolü (Sadece bu mağaza için)
        user = User.objects.filter(email=email, tenant=tenant).first()
        
        if user:
            if user.is_active:
                raise ValueError("Bu email adresi bu mağazada zaten kayıtlı.")
            else:
                # Eğer daha önce kayıt olmuş ama onaylamamışsa, bilgilerini güncelle
                user.set_password(password)
                user.first_name = first_name
                user.last_name = last_name
                user.phone = phone
                user.save()
                return {'user': user, 'tenant': tenant}
        
        # 3. Yeni TenantUser oluştur
        # Username global olarak unique olmalı, bu yüzden email + tenant_id kullanıyoruz
        unique_username = f"{email}_{tenant.id}"
        
        user = User.objects.create_user(
            username=unique_username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=User.UserRole.TENANT_USER,
            tenant=tenant,
            is_active=is_active
        )
        logger.info(f"TenantUser created: {user.email} (Tenant: {tenant.slug}, Active: {is_active})")
        
        return {
            'user': user,
            'tenant': tenant,
        }
    
    @staticmethod
    def login_tenant_user(email: str, password: str, tenant_id: str = None):
        """
        TenantUser girişi.
        """
        from django.contrib.auth import authenticate
        from apps.utils.jwt_utils import generate_jwt_token
        
        if not tenant_id:
            raise ValueError("Mağaza bilgisi (tenant_id) gerekli.")

        # 1. User'ı bu tenant içinde bul
        try:
            user = User.objects.get(email=email, tenant_id=tenant_id)
        except User.DoesNotExist:
            raise ValueError("Email veya şifre hatalı.")
        
        # 2. TenantUser kontrolü
        if user.role != User.UserRole.TENANT_USER:
            raise ValueError("Bu hesap müşteri hesabı değil.")
        
        # 3. Authentication
        # Django'nun authenticate fonksiyonu USERNAME_FIELD (email) kullanır.
        # Ama email artık unique değil. Bu yüzden user.username (email_tenantid) üzerinden authenticate yapıyoruz.
        authenticated_user = authenticate(username=user.username, password=password)
        
        if not authenticated_user:
            # Eğer email ile authenticate edilemezse (USERNAME_FIELD email olduğu için), 
            # manuel şifre kontrolü yapalım (veya custom backend yazılmalı)
            if user.check_password(password):
                authenticated_user = user
            else:
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

