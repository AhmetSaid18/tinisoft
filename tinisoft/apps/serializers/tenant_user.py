"""
TenantUser serializers.
Tenant'ın sitesinde kayıt olan müşteriler için.
"""
from rest_framework import serializers
from apps.models import User, Tenant
from apps.services.tenant_user_service import TenantUserService


class TenantUserRegisterSerializer(serializers.Serializer):
    """
    TenantUser kayıt serializer.
    Tenant'ın sitesinde müşteri kaydı için.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    phone = serializers.CharField(max_length=20, required=False)
    
    def validate_email(self, value):
        """Email kontrolü - Sadece ilgili tenant içinde benzersiz olmalı."""
        tenant_id = self.context.get('tenant_id')
        if not tenant_id:
            raise serializers.ValidationError("Tenant ID gerekli.")
            
        if User.objects.filter(email=value, tenant_id=tenant_id, is_active=True).exists():
            raise serializers.ValidationError("Bu email adresi bu mağazada zaten kullanımda.")
        return value
    
    def create(self, validated_data):
        """TenantUser oluştur (Pasif) ve kod gönder."""
        tenant_id = self.context.get('tenant_id')
        if not tenant_id:
            raise serializers.ValidationError("Tenant ID gerekli.")
        
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            raise serializers.ValidationError("Mağaza bulunamadı.")

        # 1. Kullanıcıyı oluştur (Pasif olarak)
        result = TenantUserService.register_tenant_user(
            tenant_id=tenant_id,
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone'),
            is_active=False  # Hesabı pasif oluşturuyoruz
        )
        
        # 2. Doğrulama kodunu gönder
        TenantUserService.send_registration_code(tenant, validated_data['email'])
        
        return result


class TenantUserLoginSerializer(serializers.Serializer):
    """
    TenantUser giriş serializer.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Email ve şifre kontrolü."""
        email = attrs.get('email')
        password = attrs.get('password')
        tenant_id = self.context.get('tenant_id')
        
        if email and password:
            try:
                result = TenantUserService.login_tenant_user(
                    email=email,
                    password=password,
                    tenant_id=tenant_id,
                )
                attrs['user'] = result['user']
                attrs['tenant'] = result['tenant']
            except ValueError as e:
                raise serializers.ValidationError(str(e))
        else:
            raise serializers.ValidationError("Email ve şifre gereklidir.")
        
        return attrs

