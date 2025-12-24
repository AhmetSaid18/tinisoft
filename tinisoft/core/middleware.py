"""
Multi-tenant middleware.
Request'ten tenant bilgisini alıp database router'a iletir.
"""
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from core.db_router import set_tenant_schema, clear_tenant_schema, get_tenant_schema


class TenantMiddleware(MiddlewareMixin):
    """
    Request'ten tenant bilgisini çıkarıp database schema'sını ayarlar.
    """
    
    def process_request(self, request):
        """Request geldiğinde tenant schema'sını ayarla."""
        from django.http import HttpResponseNotFound
        from django.http import JsonResponse
        
        # Tenant instance'ını al
        tenant = get_tenant_from_request(request)
        
        # Eğer subdomain veya custom domain varsa ama tenant bulunamadıysa 404 döndür
        host = request.get_host()
        is_subdomain_request = '.tinisoft.com.tr' in host and host != 'api.tinisoft.com.tr'
        is_custom_domain = host not in ['api.tinisoft.com.tr', 'tinisoft.com.tr', 'www.tinisoft.com.tr']
        
        if (is_subdomain_request or is_custom_domain) and not tenant:
            # Mağaza bulunamadı - Shopify/İKAS gibi 404 döndür
            return JsonResponse({
                'success': False,
                'message': 'Mağaza bulunamadı.',
                'error_code': 'STORE_NOT_FOUND',
            }, status=404)
        
        if tenant:
            # Tenant aktif mi kontrol et
            if tenant.status != 'active' and tenant.status != 'pending':
                return JsonResponse({
                    'success': False,
                    'message': 'Bu mağaza şu anda aktif değil.',
                    'error_code': 'STORE_INACTIVE',
                }, status=403)
            
            # Tenant schema adını oluştur
            tenant_schema = f'tenant_{tenant.id}'
            set_tenant_schema(tenant_schema)
            
            # Connection wrapper ile her sorgudan önce search_path'i ayarla
            self._setup_search_path(tenant_schema)
        else:
            # API endpoint'leri için public schema (api.tinisoft.com.tr)
            set_tenant_schema('public')
            self._setup_search_path('public')
    
    def _setup_search_path(self, schema_name):
        """Connection'da search_path'i ayarla."""
        # Connection'ı aç ve search_path'i ayarla
        # Her sorgudan önce bu ayar geçerli olacak (connection pooling ile)
        connection.ensure_connection()
        
        # Connection'ın thread-local'ına schema'yı kaydet
        if not hasattr(connection, '_tenant_schema'):
            connection._tenant_schema = None
        
        # Eğer schema değiştiyse search_path'i güncelle
        if connection._tenant_schema != schema_name:
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{schema_name}", public;')
            connection._tenant_schema = schema_name
    
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
        # TenantUser ise tenant'ı al
        if hasattr(request.user, 'tenant') and request.user.tenant:
            return request.user.tenant
        # TenantOwner ise owned_tenants'tan ilkini al (veya tenant field'ından)
        if request.user.is_tenant_owner:
            try:
                # TenantOwner'ın owned_tenants'ından ilkini al
                tenant = request.user.owned_tenants.filter(is_deleted=False).first()
                if tenant:
                    return tenant
            except:
                pass
    
    return None

