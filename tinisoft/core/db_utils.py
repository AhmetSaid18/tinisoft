"""
Database utility functions for multi-tenant schema management.
"""
from django.db import connection
from django.core.management import call_command
from core.db_router import get_tenant_schema


def create_tenant_schema(schema_name):
    """
    Yeni tenant için schema oluştur.
    """
    with connection.cursor() as cursor:
        # Schema oluştur
        cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}";')
        # Schema'ya izin ver
        cursor.execute(f'GRANT ALL ON SCHEMA "{schema_name}" TO postgres;')
        # Search path'e ekle
        cursor.execute(f'ALTER DATABASE tinisoft SET search_path TO public, "{schema_name}";')


def delete_tenant_schema(schema_name):
    """
    Tenant schema'sını sil (CASCADE ile tüm tablolar silinir).
    """
    with connection.cursor() as cursor:
        cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE;')


def migrate_tenant_schema(schema_name):
    """
    Tenant schema'sına migration uygula.
    """
    # Schema'yı set et
    from core.db_router import set_tenant_schema
    set_tenant_schema(schema_name)
    
    # Migration'ları uygula
    # TODO: Schema-specific migration logic
    # call_command('migrate', schema=schema_name)


def get_current_schema():
    """
    Şu anki aktif schema'yı döndür.
    """
    return get_tenant_schema()

