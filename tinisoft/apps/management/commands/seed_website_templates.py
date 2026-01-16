"""
Seed command for website templates
Sistemi hazır şablonlarla ve örnek verilerle başlatır.
Her tenant için (varsa) default template oluşturur.

Kullanım:
python manage.py seed_website_templates [--force]
"""

from django.core.management.base import BaseCommand
from apps.models import Tenant

class Command(BaseCommand):
    help = 'Seeds database with default website templates for existing tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing templates',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Seeding website templates...'))
        force = options.get('force', False)
        
        tenants = Tenant.objects.all()
        count = 0
        
        from apps.services.website_service import WebsiteService
        
        for tenant in tenants:
            # Varsa ve force değilse geç
            if hasattr(tenant, 'website_template') and not force:
                self.stdout.write(f"Tenant {tenant.slug} already has a template. Use --force to overwrite. Skipping.")
                continue
            
            if force and hasattr(tenant, 'website_template'):
                tenant.website_template.delete()
                self.stdout.write(f"Deleted existing template for {tenant.slug} (Force mode)")

            # WebsiteService kullanarak dükkanı doğru şekilde döşe
            template_key = getattr(tenant, 'template', 'classic-ecommerce')
            # Template null veya boşsa classic-ecommerce'e zorla
            if not template_key or template_key == "default":
                template_key = 'classic-ecommerce'

            template = WebsiteService.init_tenant_website(tenant, template_key=template_key)
            
            if template:
                count += 1
                self.stdout.write(self.style.SUCCESS(f"Initialized template for tenant: {tenant.slug} ({template_key})"))
            
        self.stdout.write(self.style.SUCCESS(f'Successfully processed {count} templates!'))
