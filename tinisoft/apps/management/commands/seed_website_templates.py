"""
Seed command for website templates
Sistemi hazır şablonlarla ve örnek verilerle başlatır.
Her tenant için (varsa) default template oluşturur.

Kullanım:
python manage.py seed_website_templates
"""

from django.core.management.base import BaseCommand
from apps.models.website import WebsiteTemplate, WebsitePage
from apps.models.tenant import Tenant
from apps.utils.website_defaults import AVAILABLE_TEMPLATES, DEFAULT_PAGES

class Command(BaseCommand):
    help = 'Seeds database with default website templates for existing tenants'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Seeding website templates...'))
        
        tenants = Tenant.objects.all()
        count = 0
        
        for tenant in tenants:
            # Varsa geç
            if hasattr(tenant, 'website_template'):
                self.stdout.write(f"Tenant {tenant.slug} already has a template. Skipping.")
                continue
                
            # Default template: Classic E-Commerce
            template_key = "classic-ecommerce"
            template_data = AVAILABLE_TEMPLATES[template_key]
            
            # Create template
            template = WebsiteTemplate.objects.create(
                tenant=tenant,
                base_template=template_key,
                site_name=tenant.name,
                homepage_config=template_data['homepage_config'],
                theme_config=template_data['theme_config'],
                navigation_menus=template_data['navigation_menus'],
                footer_config=template_data['footer_config'],
                social_links=template_data['social_links'],
                announcement_bar=template_data['announcement_bar'],
                analytics_config=template_data['analytics_config'],
                pwa_config=template_data['pwa_config'],
                
                # SEO Defaults
                meta_title=f"{tenant.name} - Online Alışveriş",
                meta_description=f"{tenant.name} ile en kaliteli ürünler kapınızda."
            )
            
            # Create default pages
            for page_data in DEFAULT_PAGES:
                WebsitePage.objects.create(
                    template=template,
                    slug=page_data['slug'],
                    title=page_data['title'],
                    page_config=page_data['page_config'],
                    meta_title=page_data['meta_title'],
                    meta_description=page_data['meta_description'],
                    show_in_menu=True,
                    sort_order=1
                )
            
            count += 1
            self.stdout.write(self.style.SUCCESS(f"Created template for tenant: {tenant.slug}"))
            
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count} templates!'))
