"""
Multi-tenant middleware.
Request'ten tenant bilgisini alıp database router'a iletir.
"""
from django.utils.deprecation import MiddlewareMixin
from core.db_router import set_tenant_schema, clear_tenant_schema


class TenantMiddleware(MiddlewareMixin):
    """
    Request'ten tenant bilgisini çıkarıp database schema'sını ayarlar.
    """
    
    def process_request(self, request):
        """Request geldiğinde tenant schema'sını ayarla."""
        from django.db import connection
        
        # Tenant instance'ını al
        tenant = get_tenant_from_request(request)
        
        if tenant:
            # Tenant schema adını oluştur
            tenant_schema = f'tenant_{tenant.id}'
            set_tenant_schema(tenant_schema)
            
            # PostgreSQL search_path'i ayarla
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{tenant_schema}", public;')
        else:
            # Default schema (public)
            set_tenant_schema('public')
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO public;')
    
    def process_response(self, request, response):
        """Response döndürülmeden önce schema'yı temizle."""
        from django.db import connection
        
        # Search path'i public'e geri al
        try:
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO public;')
        except:
            pass
        
        clear_tenant_schema()
        return response
    
    def get_tenant_from_request(self, request):
        """
        Request'ten tenant bilgisini çıkar.
        - Subdomain: tenant1.tinisoft.com.tr -> tenant1
        - Custom domain: example.com -> domain'den tenant bul
        - Header: X-Tenant-ID header'ından
        """
        host = request.get_host()
        
        # Subdomain kontrolü (tinisoft ana domain'i için)
        # Örnek: ates.tinisoft.com.tr -> ates
        if '.tinisoft.com.tr' in host:
            subdomain = host.split('.')[0]
            return f"tenant_{subdomain}"
        
        # Custom domain kontrolü (cache'den veya DB'den)
        # TODO: Domain'den tenant lookup yapılacak
        # domain = Domain.objects.filter(domain_name=host).first()
        # if domain:
        #     return f"tenant_{domain.tenant_id}"
        
        # Header'dan tenant ID
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            return f"tenant_{tenant_id}"
        
        return None


def get_tenant_from_request(request):
    """
    Request'ten tenant instance'ını döndür.
    View'larda kullanılmak için utility fonksiyonu.
    """
    from apps.models import Tenant, Domain
    
    host = request.get_host()
    
    # Subdomain kontrolü (tinisoft ana domain'i için)
    # Örnek: ates.tinisoft.com.tr -> ates
    if '.tinisoft.com.tr' in host:
        subdomain = host.split('.')[0]
        try:
            tenant = Tenant.objects.get(subdomain=subdomain, is_deleted=False)
            return tenant
        except Tenant.DoesNotExist:
            pass
    
    # Custom domain kontrolü
    try:
        domain = Domain.objects.filter(domain_name=host, is_deleted=False).first()
        if domain:
            return domain.tenant
    except:
        pass
    
    # Header'dan tenant ID
    tenant_id = request.headers.get('X-Tenant-ID')
    if tenant_id:
        try:
            tenant = Tenant.objects.get(id=tenant_id, is_deleted=False)
            return tenant
        except Tenant.DoesNotExist:
            pass
    
    # User'dan tenant (authenticated ise)
    if hasattr(request, 'user') and request.user.is_authenticated:
        if hasattr(request.user, 'tenant') and request.user.tenant:
            return request.user.tenant
    
    return None

