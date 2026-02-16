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
            logger.warning(f"[PERM] HasStaffPermission DENIED - User not authenticated")
            return False
            
        # 1. Super Admin veya Sistem Admin her şeye sorgusuz erişebilir
        if request.user.is_owner or request.user.is_system_admin:
            return True
            
        # 2. Mağaza Sahibi veya Personel kontrolü
        if request.user.is_tenant_owner or request.user.is_tenant_staff:
            # Middleware'den gelen cached tenant'ı al
            from core.middleware import get_tenant_from_request
            tenant = getattr(request, 'tenant', get_tenant_from_request(request))
            
            # Request'teki tenant ile user'ın bağlı olduğu tenant eşleşmeli (ID bazlı kontrol daha hızlı)
            if not tenant or request.user.tenant_id != tenant.id:
                logger.warning(
                    f"[PERM] HasStaffPermission DENIED - Tenant mismatch | "
                    f"User: {request.user.email} | Role: {request.user.role} | "
                    f"User tenant_id: {request.user.tenant_id} | "
                    f"Request tenant: {tenant} (id={getattr(tenant, 'id', None)})"
                )
                return False
            
            # Tenant Sahibi ise tüm modüllere erişebilir
            if request.user.is_tenant_owner:
                return True
                
            # 3. Personel ise modül bazlı yetki kontrolü
            required = getattr(view, 'staff_permission', None)
            if not required and hasattr(view, 'cls'):
                required = getattr(view.cls, 'staff_permission', None)
            
            logger.info(
                f"[PERM] Staff permission check | "
                f"User: {request.user.email} | Method: {request.method} | "
                f"Required: {required} | "
                f"View: {view.__class__.__name__} | "
                f"View attrs: {[a for a in dir(view) if 'permission' in a.lower()]}"
            )
            
            if not required:
                logger.warning(
                    f"[PERM] HasStaffPermission DENIED - No required permission found on view | "
                    f"User: {request.user.email} | View: {view.__class__.__name__}"
                )
                return False
            
            # 4. OKUMA işlemleri (GET, HEAD, OPTIONS) - Genel modüller için serbest
            if request.method in permissions.SAFE_METHODS:
                sensitive_modules = ['staff', 'integrations']
                if required not in sensitive_modules:
                    return True
            
            # 5. YAZMA işlemleri veya HASSAS OKUMA - Redis Cache üzerinden yetki kontrolü
            from apps.services.cache_service import CacheService
            user_perms = CacheService.get_user_permissions(request.user.id)
            
            cache_hit = user_perms is not None
            if user_perms is None:
                # Cache'de yoksa veritabanından/user objesinden al ve Redis'e yaz
                user_perms = request.user.staff_permissions or []
                CacheService.set_user_permissions(request.user.id, user_perms)
            
            result = required in user_perms
            logger.info(
                f"[PERM] Staff write permission check | "
                f"User: {request.user.email} | Method: {request.method} | "
                f"Required: '{required}' | User perms: {user_perms} | "
                f"Cache hit: {cache_hit} | Result: {result}"
            )
            return result
            
        logger.warning(
            f"[PERM] HasStaffPermission DENIED - Not tenant_owner or tenant_staff | "
            f"User: {request.user.email} | Role: {request.user.role}"
        )
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

