"""
Website Service - Business logic for website templates and pages.
"""
from apps.models.website import WebsiteTemplate, WebsitePage
from apps.utils.website_defaults import get_template_by_key, DEFAULT_PAGES
import logging

logger = logging.getLogger(__name__)

class WebsiteService:
    """Website management service."""
    
    @staticmethod
    def init_tenant_website(tenant, template_key='classic-ecommerce', force_update=False):
        """
        Tenant için website template ve default sayfaları başlatır.
        """
        # Template data getir
        template_data = get_template_by_key(template_key)
        
        # Template'i al veya oluştur
        website_template, created = WebsiteTemplate.objects.get_or_create(
            tenant=tenant,
            defaults={
                'is_active': True,
                'site_name': tenant.name,
                'base_template': template_key,
                'homepage_config': template_data['homepage_config'],
                'theme_config': template_data['theme_config'],
                'meta_title': f"{tenant.name} - Online Alışveriş",
                'meta_description': f"{tenant.name} ile kaliteli ürünler, uygun fiyatlar ve hızlı teslimat."
            }
        )
        
        if not created and force_update:
            website_template.base_template = template_key
            website_template.homepage_config = template_data['homepage_config']
            website_template.theme_config = template_data['theme_config']
            website_template.save()
            
        # Default pages oluştur
        existing_slugs = set(website_template.pages.values_list('slug', flat=True))
        for page_data in DEFAULT_PAGES:
            if page_data['slug'] not in existing_slugs:
                WebsitePage.objects.create(
                    template=website_template,
                    **page_data
                )
            elif force_update:
                try:
                    page = WebsitePage.objects.get(template=website_template, slug=page_data['slug'])
                    for key, value in page_data.items():
                        setattr(page, key, value)
                    page.save()
                except WebsitePage.DoesNotExist:
                    pass
        
        return website_template
