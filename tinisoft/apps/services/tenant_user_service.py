"""
TenantUser service.
Tenant'ın sitesinde kayıt olan müşteriler için servis.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.models import Tenant
import logging

import logging
import random
from django.core.cache import cache
from apps.services.email_service import EmailService

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
        
        # 2. Mevcut kullanıcı kontrolü
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
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=User.UserRole.TENANT_USER,
            tenant=tenant,
            is_active=is_active
        )
        logger.info(f"TenantUser created: {user.email} (Active: {is_active})")
        
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

