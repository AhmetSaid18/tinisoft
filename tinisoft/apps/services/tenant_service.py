"""
Tenant service.
Tenant oluşturma, schema yönetimi işlemleri.
"""
from core.db_utils import create_tenant_schema
import logging

logger = logging.getLogger(__name__)


class TenantService:
    """Tenant yönetim servisi."""
    
    @staticmethod
    def create_tenant_schema(tenant, schema_name: str):
        """
        Tenant için schema oluştur.
        """
        try:
            create_tenant_schema(schema_name)
            logger.info(f"Schema created successfully: {schema_name}")
        except Exception as e:
            logger.error(f"Failed to create schema {schema_name}: {str(e)}")
            raise
    
    @staticmethod
    def delete_tenant_schema(schema_name: str):
        """
        Tenant schema'sını sil.
        """
        from core.db_utils import delete_tenant_schema
        try:
            delete_tenant_schema(schema_name)
            logger.info(f"Schema deleted successfully: {schema_name}")
        except Exception as e:
            logger.error(f"Failed to delete schema {schema_name}: {str(e)}")
            raise

