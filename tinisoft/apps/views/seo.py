from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.models.website import WebsiteTemplate
from apps.models.product import Product, Category

class StorefrontSitemapView(APIView):
    """
    GET /api/v1/storefront/sitemap/
    Tüm public URL'leri listeler (Ürünler, Kategoriler, Sayfalar)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        tenant_slug = request.headers.get('X-Tenant-Slug')
        if not tenant_slug:
            return Response({"error": "X-Tenant-Slug header required"}, status=400)

        urls = []
        
        # 1. Static Pages (Hakkımızda, İletişim vs.)
        # Sadece aktif ve menüde/yayında olanlar
        template = WebsiteTemplate.objects.filter(tenant__slug=tenant_slug, is_active=True).first()
        if template:
            pages = template.pages.filter(is_active=True)
            for page in pages:
                urls.append({
                    "loc": f"/{page.slug}",
                    "lastmod": page.updated_at.date(),
                    "priority": 0.8
                })

        # 2. Categories
        categories = Category.objects.filter(tenant__slug=tenant_slug, is_active=True)
        for cat in categories:
            urls.append({
                "loc": f"/kategori/{cat.slug}",
                "changefreq": "weekly",
                "priority": 0.8
            })

        # 3. Products
        products = Product.objects.filter(tenant__slug=tenant_slug, is_active=True, is_published=True)
        for prod in products:
            urls.append({
                "loc": f"/urun/{prod.slug}",
                "lastmod": prod.updated_at.date(),
                "priority": 1.0, # Ürünler en önemli
                "changefreq": "daily"
            })
            
        return Response(urls)


class StorefrontRobotsView(APIView):
    """
    GET /api/v1/storefront/robots/
    Robots.txt kurallarını döndürür.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        tenant_slug = request.headers.get('X-Tenant-Slug')
        
        # Default E-Commerce Rules
        rules = {
            "user_agent": "*",
            "allow": ["/"],
            "disallow": [
                "/basket",
                "/checkout",
                "/account", 
                "/auth",
                "/search",
                "/api",
                "/admin",
                "/*?sort=", # Duplicate content önlemek için filtreleri engelle
                "/*?price="
            ],
            "sitemap_url": "sitemap.xml"
        }
        
        # Opsiyonel: Eğer site bakım modundaysa her şeyi disallow et
        # if maintenance_mode: rules['disallow'] = ['/']
        
        return Response(rules)
