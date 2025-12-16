"""
Database router for multi-tenant schema routing.
Her tenant için ayrı schema kullanılacak ama tek PostgreSQL veritabanı.
"""
from django.conf import settings
from threading import local

_thread_locals = local()


def set_tenant_schema(schema_name):
    """Thread-local olarak tenant schema'sını ayarla."""
    _thread_locals.schema = schema_name


def get_tenant_schema():
    """Thread-local'dan tenant schema'sını al."""
    return getattr(_thread_locals, 'schema', 'public')


def clear_tenant_schema():
    """Thread-local'dan tenant schema'sını temizle."""
    if hasattr(_thread_locals, 'schema'):
        delattr(_thread_locals, 'schema')


class TenantDatabaseRouter:
    """
    Multi-tenant database router.
    Tenant-specific modeller için schema routing yapar.
    
    Tenant-specific modeller: Product, ShippingMethod, ShippingAddress, Order, vb.
    Sistem modelleri: User, Tenant, Domain (public schema'da)
    """
    
    # Tenant-specific modeller (tenant schema'sında olacak)
    TENANT_MODELS = [
        'Product',
        'ShippingMethod',
        'ShippingAddress',
        'Order',
        'OrderItem',
        'Category',
        'Inventory',
        'Payment',
        'Invoice',
        'Customer',
    ]
    
    # Sistem modelleri (public schema'da)
    SYSTEM_MODELS = [
        'User',
        'Tenant',
        'Domain',
    ]
    
    def _is_tenant_model(self, model):
        """Model tenant-specific mi?"""
        model_name = model.__name__
        # Tenant ForeignKey varsa tenant-specific
        if hasattr(model, 'tenant'):
            return True
        # Sistem modelleri değilse tenant-specific
        if model_name not in self.SYSTEM_MODELS:
            return model_name in self.TENANT_MODELS
        return False
    
    def db_for_read(self, model, **hints):
        """Read işlemleri için schema belirle."""
        if self._is_tenant_model(model):
            return 'default'  # Tenant schema'sına yönlendirilecek
        return None  # Public schema (default)
    
    def db_for_write(self, model, **hints):
        """Write işlemleri için schema belirle."""
        if self._is_tenant_model(model):
            return 'default'  # Tenant schema'sına yönlendirilecek
        return None  # Public schema (default)
    
    def allow_relation(self, obj1, obj2, **hints):
        """İlişkilere izin ver (aynı DB'de oldukları için)."""
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Migration'lara izin ver."""
        return True

