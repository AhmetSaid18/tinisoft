"""
Custom permissions for role-based access control.
Rol bazlı erişim kontrolü için permission class'ları.
"""
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)


class IsOwner(permissions.BasePermission):
    """
    Sadece Owner (Tinisoft - program sahibi) erişebilir.
    """
    
    def has_permission(self, request, view):
        """Permission kontrolü."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_owner
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission kontrolü."""
        return self.has_permission(request, view)


class IsTenantOwner(permissions.BasePermission):
    """
    Sadece TenantOwner (mağaza sahibi) erişebilir.
    """
    
    def has_permission(self, request, view):
        """Permission kontrolü."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_tenant_owner
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission kontrolü."""
        return self.has_permission(request, view)


class IsTenantStaff(permissions.BasePermission):
    """
    Sadece TenantStaff (mağaza personeli) erişebilir.
    """
    
    def has_permission(self, request, view):
        """Permission kontrolü."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_tenant_staff
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission kontrolü."""
        return self.has_permission(request, view)


class HasStaffPermission(permissions.BasePermission):
    """
    Personelin belirli bir modül yetkisi (products, orders, vb.) olup olmadığını kontrol eder.
    Mağaza sahibi (TenantOwner) tüm yetkilere sahiptir.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super Admin (Tinisoft Admin) her şeye erişebilir
        if request.user.is_owner:
            return True
            
        # Mağaza Sahibi (Tenant Owner) veya Personel (Tenant Staff) için tenant kontrolü
        if request.user.is_tenant_owner or request.user.is_tenant_staff:
            from core.middleware import get_tenant_from_request
            tenant = get_tenant_from_request(request)
            
            # Request'teki tenant ile user'ın bağlı olduğu tenant eşleşmeli
            if not tenant or request.user.tenant != tenant:
                logger.warning(f"[PERMISSION] Tenant mismatch. User: {request.user.email} (Tenant: {request.user.tenant}), Request Tenant: {tenant}")
                return False
            
            # Sahipse tam yetki
            if request.user.is_tenant_owner:
                return True
                
            # Personel ise modül bazlı yetki kontrolü
            required = getattr(view, 'staff_permission', None)
            
            if not required:
                # Yetki belirtilmemişse personelin hiçbir şeye erişimi olmasın (Zero Trust)
                logger.warning(f"[PERMISSION] Missing staff_permission attr on view: {view}. User: {request.user.email}")
                return False
            
            # OKUMA işlemleri (GET, HEAD, OPTIONS)
            if request.method in permissions.SAFE_METHODS:
                # Bazı modüller çok kritiktir, okuması bile yetki ister (Örn: Personeller, Entegrasyonlar)
                sensitive_modules = ['staff', 'integrations']
                if required not in sensitive_modules:
                    # Ürün, sipariş vb. genel modüllerde okumaya her personelin izni olsun
                    return True
            
            # YAZMA işlemleri (POST, PUT, PATCH, DELETE) veya HASSAS OKUMA
            has_perm = request.user.has_staff_permission(required)
            if not has_perm:
                 logger.warning(f"[PERMISSION] Denied. User: {request.user.email} lacks '{required}' permission for {request.method} {request.path}")
            return has_perm
            
        return False

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsTenantUser(permissions.BasePermission):
    """
    Sadece TenantUser (müşteri) erişebilir.
    """
    
    def has_permission(self, request, view):
        """Permission kontrolü."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Tenant User veya Tenant Owner erişebilir
        return request.user.is_tenant_user or request.user.is_tenant_owner
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission kontrolü."""
        return self.has_permission(request, view)


class IsTenantOwnerOrReadOnly(permissions.BasePermission):
    """
    TenantOwner yazabilir, diğerleri sadece okuyabilir.
    """
    
    def has_permission(self, request, view):
        """Permission kontrolü."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # GET, HEAD, OPTIONS için herkes okuyabilir
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Yazma işlemleri için TenantOwner olmalı
        return request.user.is_tenant_owner


class IsOwnerOrTenantOwner(permissions.BasePermission):
    """
    Owner veya TenantOwner erişebilir.
    Owner her şeye erişebilir, TenantOwner sadece kendi tenant'ına ait objelere.
    """
    
    def has_permission(self, request, view):
        """Permission kontrolü."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Owner her şeye erişebilir
        if request.user.is_owner:
            return True
        
        # TenantOwner erişebilir
        return request.user.is_tenant_owner
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission kontrolü."""
        # Owner her şeye erişebilir
        if request.user.is_owner:
            return True
        
        # TenantOwner ise, sadece kendi tenant'ına ait objelere erişebilir
        if request.user.is_tenant_owner:
            if hasattr(obj, 'tenant'):
                return obj.tenant == request.user.tenant
            elif hasattr(obj, 'id') and hasattr(request.user, 'tenant'):
                return obj.id == request.user.tenant.id
        
        return False


class IsSystemAdmin(permissions.BasePermission):
    """
    Sadece SystemAdmin erişebilir.
    """
    
    def has_permission(self, request, view):
        """Permission kontrolü."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_system_admin
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission kontrolü."""
        return self.has_permission(request, view)


class IsTenantOwnerOfObject(permissions.BasePermission):
    """
    Owner her şeye erişebilir.
    TenantOwner sadece kendi tenant'ına ait objelere erişebilir.
    Object'in tenant field'ı olmalı.
    """
    
    def has_permission(self, request, view):
        """Permission kontrolü."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Owner her şeye erişebilir
        if request.user.is_owner:
            return True
        
        # SystemAdmin her şeye erişebilir
        if request.user.is_system_admin:
            return True
        
        # TenantOwner veya TenantStaff olmalı
        return request.user.is_tenant_owner or request.user.is_tenant_staff
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission kontrolü."""
        # Owner her şeye erişebilir
        if request.user.is_owner:
            return True
        
        # SystemAdmin her şeye erişebilir
        if request.user.is_system_admin:
            return True
        
        # TenantOwner veya TenantStaff ise, sadece kendi tenant'ına ait objelere erişebilir
        if request.user.is_tenant_owner or request.user.is_tenant_staff:
            # Object'in tenant field'ı var mı kontrol et
            if hasattr(obj, 'tenant'):
                return obj.tenant == request.user.tenant
            # Eğer obj kendisi tenant ise
            elif hasattr(obj, 'id') and hasattr(request.user, 'tenant'):
                return obj.id == request.user.tenant.id
            else:
                logger.warning(f"Object {obj} has no tenant field for permission check")
                return False
        
        return False


class IsTenantUserOfObject(permissions.BasePermission):
    """
    Owner her şeye erişebilir.
    TenantOwner kendi tenant'ına ait objelere erişebilir.
    TenantUser sadece kendi tenant'ına ait objelere erişebilir (okuma ağırlıklı).
    """
    
    def has_permission(self, request, view):
        """Permission kontrolü."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Owner her şeye erişebilir
        if request.user.is_owner:
            return True
        
        # SystemAdmin her şeye erişebilir
        if request.user.is_system_admin:
            return True
        
        # TenantOwner erişebilir
        if request.user.is_tenant_owner:
            return True
        
        # TenantUser veya TenantOwner olmalı
        return request.user.is_tenant_user or request.user.is_tenant_owner
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission kontrolü."""
        # Owner her şeye erişebilir
        if request.user.is_owner:
            return True
        
        # SystemAdmin her şeye erişebilir
        if request.user.is_system_admin:
            return True
        
        # TenantOwner ise, sadece kendi tenant'ına ait objelere erişebilir
        if request.user.is_tenant_owner:
            if hasattr(obj, 'tenant'):
                return obj.tenant == request.user.tenant
            elif hasattr(obj, 'id') and hasattr(request.user, 'tenant'):
                return obj.id == request.user.tenant.id
        
        # TenantUser ise, sadece kendi tenant'ına ait objelere erişebilir
        if request.user.is_tenant_user:
            if hasattr(obj, 'tenant'):
                return obj.tenant == request.user.tenant
            elif hasattr(obj, 'id') and hasattr(request.user, 'tenant'):
                return obj.id == request.user.tenant.id
        
        return False

