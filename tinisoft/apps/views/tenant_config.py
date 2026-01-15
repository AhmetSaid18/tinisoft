from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from apps.permissions import IsTenantOwner, IsTenantUser
from apps.models.website import WebsiteTemplate
from apps.serializers.website import AdminWebsiteTemplateSerializer

class TenantSettingsView(APIView):
    """
    GET, PUT /api/v1/tenant/settings/
    
    Tenant'ın genel ayarlarını yönetir (Site kimliği, İletişim, Sosyal Medya vb.)
    Bu view, WebsiteTemplate modelindeki ilgili alanları kullanır.
    """
    permission_classes = [IsAuthenticated, IsTenantOwner]

    def get(self, request):
        """Ayarları getir"""
        tenant = request.user.tenant
        template, _ = WebsiteTemplate.objects.get_or_create(tenant=tenant)
        
        # Frontend'in beklediği format tahmini
        data = {
            "site_identity": {
                "site_name": template.site_name,
                "site_logo_url": template.site_logo_url,
                "favicon_url": template.favicon_url,
            },
            "contact_info": {
                "support_phone": template.support_phone,
                "support_email": template.support_email,
            },
            "social_links": template.social_links, # veya draft_social_links?
            "seo": {
                "meta_title": template.meta_title,
                "meta_description": template.meta_description,
            }
        }
        return Response(data)

    def put(self, request):
        """Ayarları güncelle"""
        tenant = request.user.tenant
        template, _ = WebsiteTemplate.objects.get_or_create(tenant=tenant)
        
        data = request.data
        
        # Site Kimliği
        if 'site_identity' in data:
            identity = data['site_identity']
            if 'site_name' in identity: template.site_name = identity['site_name']
            if 'site_logo_url' in identity: template.site_logo_url = identity['site_logo_url']
            if 'favicon_url' in identity: template.favicon_url = identity['favicon_url']
            
        # İletişim
        if 'contact_info' in data:
            contact = data['contact_info']
            if 'support_phone' in contact: template.support_phone = contact['support_phone']
            if 'support_email' in contact: template.support_email = contact['support_email']
            
        # Sosyal Medya
        if 'social_links' in data:
            # Hem draft hem live güncelliyoruz çünkü bu ayarlar genelde anlık
            template.social_links = data['social_links']
            template.draft_social_links = data['social_links']
            
        # SEO
        if 'seo' in data:
            seo = data['seo']
            if 'meta_title' in seo: template.meta_title = seo['meta_title']
            if 'meta_description' in seo: template.meta_description = seo['meta_description']
            
        template.save()
        return Response({"message": "Ayarlar güncellendi"})
