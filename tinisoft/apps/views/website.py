"""
Website Template API Views
- Public API: Storefront için (anonymous, cached)
- Admin API: Tenant panel için (authenticated, full CRUD)
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from apps.models.website import WebsiteTemplate, WebsitePage
from apps.serializers.website import (
    PublicWebsiteTemplateSerializer,
    AdminWebsiteTemplateSerializer,
    AdminWebsitePageSerializer,
    AdminWebsitePageCreateUpdateSerializer,
)
from apps.permissions import IsTenantUser


# ================================
# PUBLIC API (Storefront)
# ================================

class PublicWebsiteTemplateView(APIView):
    """
    GET /api/v1/storefront/config?domain=magaza1.com
    
    Public endpoint - Storefront için site konfigürasyonu
    - Anonymous access (Public)
    - Redis cache ile hızlandırılmış
    - Domain'e göre template getirir
    
    Query Parameters:
        - domain (required): Tenant domain (örn: magaza1.com)
    
    Response:
        {
            "homepage_config": {...},
            "theme_config": {...},
            "site_name": "Avrupa Mutfak",
            "site_logo_url": "https://...",
            "support_phone": "+90...",
            "support_email": "info@...",
            "meta_title": "...",
            "meta_description": "...",
            "custom_css": "...",
            "custom_js": "...",
            "pages": [...]
        }
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get website template by domain"""
        domain = request.query_params.get('domain')
        
        if not domain:
            return Response(
                {"error": "Domain parametresi gerekli. Örn: ?domain=magaza1.com"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cache key
        cache_key = f"website_template:public:{domain}"
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        # Get from database
        template = WebsiteTemplate.get_by_domain(domain)
        
        if not template:
            return Response(
                {"error": f"'{domain}' için aktif bir site yapılandırması bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize
        serializer = PublicWebsiteTemplateSerializer(template)
        response_data = serializer.data
        
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, response_data, timeout=3600)
        
        return Response(response_data)


# ================================
# ADMIN API (Tenant Panel)
# ================================

class AdminWebsiteTemplateView(APIView):
    """
    GET /api/v1/tenant/website/template/ - Kendi template'ini getir
    PUT /api/v1/tenant/website/template/ - Template'i güncelle
    
    Tenant kullanıcıları kendi website template'lerini yönetir.
    """
    
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def get(self, request):
        """Get tenant's website template"""
        tenant = request.user.tenant
        
        # Get or create template
        template, created = WebsiteTemplate.objects.get_or_create(
            tenant=tenant,
            defaults={
                'site_name': tenant.name,
                'is_active': True,
            }
        )
        
        serializer = AdminWebsiteTemplateSerializer(template)
        return Response(serializer.data)
    
    def put(self, request):
        """Update tenant's website template"""
        tenant = request.user.tenant
        
        # Get or create template
        template, created = WebsiteTemplate.objects.get_or_create(
            tenant=tenant,
            defaults={'is_active': True}
        )
        
        # Update
        serializer = AdminWebsiteTemplateSerializer(
            template,
            data=request.data,
            partial=True  # Allow partial updates
        )
        
        if serializer.is_valid():
            serializer.save()
            # Cache will be invalidated by signal
            return Response(serializer.data)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminWebsitePageListCreateView(APIView):
    """
    GET /api/v1/tenant/website/pages/ - Tüm sayfaları listele
    POST /api/v1/tenant/website/pages/ - Yeni sayfa ekle
    """
    
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def get(self, request):
        """List all pages for this tenant"""
        tenant = request.user.tenant
        
        # Get or create template
        template, _ = WebsiteTemplate.objects.get_or_create(
            tenant=tenant,
            defaults={'is_active': True}
        )
        
        pages = template.pages.all().order_by('sort_order', 'title')
        serializer = AdminWebsitePageSerializer(pages, many=True)
        
        return Response(serializer.data)
    
    def post(self, request):
        """Create new page"""
        tenant = request.user.tenant
        
        # Get or create template
        template, _ = WebsiteTemplate.objects.get_or_create(
            tenant=tenant,
            defaults={'is_active': True}
        )
        
        # Create page
        serializer = AdminWebsitePageCreateUpdateSerializer(
            data=request.data,
            context={'template': template}
        )
        
        if serializer.is_valid():
            page = serializer.save()
            # Return full page data
            response_serializer = AdminWebsitePageSerializer(page)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminWebsitePageDetailView(APIView):
    """
    GET /api/v1/tenant/website/pages/{id}/ - Sayfa detayı
    PUT /api/v1/tenant/website/pages/{id}/ - Sayfayı güncelle
    DELETE /api/v1/tenant/website/pages/{id}/ - Sayfayı sil
    """
    
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def get_page(self, request, page_id):
        """Get page and verify ownership"""
        tenant = request.user.tenant
        
        # Get template
        template = get_object_or_404(WebsiteTemplate, tenant=tenant)
        
        # Get page
        page = get_object_or_404(WebsitePage, id=page_id, template=template)
        
        return page
    
    def get(self, request, page_id):
        """Get page details"""
        page = self.get_page(request, page_id)
        serializer = AdminWebsitePageSerializer(page)
        return Response(serializer.data)
    
    def put(self, request, page_id):
        """Update page"""
        page = self.get_page(request, page_id)
        
        serializer = AdminWebsitePageCreateUpdateSerializer(
            page,
            data=request.data,
            partial=True,
            context={'template': page.template}
        )
        
        if serializer.is_valid():
            serializer.save()
            # Return full page data
            response_serializer = AdminWebsitePageSerializer(page)
            return Response(response_serializer.data)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request, page_id):
        """Delete page"""
        page = self.get_page(request, page_id)
        page.delete()
        # Cache will be invalidated by signal
        return Response(status=status.HTTP_204_NO_CONTENT)


# ================================
# TEMPLATE SELECTION (WordPress-like)
# ================================

class AvailableTemplatesView(APIView):
    """
    GET /api/v1/tenant/website/templates/available/
    
    Mevcut template'leri listele (WordPress tema seçimi gibi)
    """
    
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def get(self, request):
        """List available templates"""
        from apps.utils.website_defaults import AVAILABLE_TEMPLATES
        
        templates = []
        for key, template_data in AVAILABLE_TEMPLATES.items():
            templates.append({
                'key': key,
                'name': template_data['name'],
                'description': template_data['description'],
                'preview_image': f'/static/templates/{key}/preview.jpg',  # Opsiyonel
            })
        
        return Response({
            'templates': templates,
            'current': request.user.tenant.website_template.base_template if hasattr(request.user.tenant, 'website_template') else None
        })


class ApplyTemplateView(APIView):
    """
    POST /api/v1/tenant/website/templates/apply/
    
    Seçilen template'i tenant'a uygula (kendi kopyasını oluştur)
    Her tenant kendi kopyasını özelleştirebilir
    
    Request:
        {
            "template_key": "modern-minimalist"
        }
    """
    
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def post(self, request):
        """Apply selected template"""
        from apps.utils.website_defaults import get_template_by_key, DEFAULT_PAGES
        
        template_key = request.data.get('template_key')
        
        if not template_key:
            return Response(
                {"error": "template_key gerekli. Örn: 'modern-minimalist' veya 'classic-ecommerce'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Template data getir
        template_data = get_template_by_key(template_key)
        
        if not template_data:
            return Response(
                {"error": f"'{template_key}' template'i bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        tenant = request.user.tenant
        
        # Get or create template
        website_template, created = WebsiteTemplate.objects.get_or_create(
            tenant=tenant,
            defaults={'is_active': True}
        )
        
        # Template'i uygula (kendi kopyasını oluştur)
        website_template.base_template = template_key
        website_template.homepage_config = template_data['homepage_config']
        website_template.theme_config = template_data['theme_config']
        
        # Site bilgileri (eski değerler varsa koru)
        if not website_template.site_name:
            website_template.site_name = tenant.name
        if not website_template.meta_title:
            website_template.meta_title = f"{tenant.name} - Online Alışveriş"
        if not website_template.meta_description:
            website_template.meta_description = f"{tenant.name} ile kaliteli ürünler, uygun fiyatlar ve hızlı teslimat."
        
        website_template.save()
        
        # Default pages oluştur (yoksa)
        existing_slugs = set(website_template.pages.values_list('slug', flat=True))
        
        for page_data in DEFAULT_PAGES:
            if page_data['slug'] not in existing_slugs:
                WebsitePage.objects.create(
                    template=website_template,
                    **page_data
                )
        
        # Response
        serializer = AdminWebsiteTemplateSerializer(website_template)
        
        return Response({
            'message': f"'{template_data['name']}' template'i başarıyla uygulandı. Artık özelleştirebilirsiniz!",
            'template': serializer.data
        })

