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
    """
    
    def db_for_read(self, model, **hints):
        """Read işlemleri için schema belirle."""
        if hasattr(model, '_tenant_schema'):
            return 'default'
        return None
    
    def db_for_write(self, model, **hints):
        """Write işlemleri için schema belirle."""
        if hasattr(model, '_tenant_schema'):
            return 'default'
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """İlişkilere izin ver (aynı DB'de oldukları için)."""
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Migration'lara izin ver."""
        return True

