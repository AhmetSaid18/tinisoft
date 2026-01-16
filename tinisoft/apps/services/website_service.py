import logging
from django.core.cache import cache
from apps.models.website import WebsiteTemplate, WebsitePage
from apps.utils.website_defaults import AVAILABLE_TEMPLATES, DEFAULT_PAGES

logger = logging.getLogger(__name__)

class WebsiteService:
    """
    Website management service.
    Handles template initialization, page management, and publishing.
    """

    @staticmethod
    def init_tenant_website(tenant, template_key='classic-ecommerce', force_update=False):
        """
        Initializes a tenant's website with a default template and pages.
        Called during tenant registration.
        """
        try:
            # Clear cache for this tenant's domains
            # This ensures any "empty" cached results are cleared
            from django.conf import settings
            cache_keys = [
                f"website_template_{tenant.slug}",
                f"website_template_{tenant.custom_domain}" if tenant.custom_domain else None,
                f"website_template_{tenant.subdomain}.tinisoft.com.tr"
            ]
            for key in cache_keys:
                if key: cache.delete(key)
            
            # 1. Existing template check
            template = WebsiteTemplate.objects.filter(tenant=tenant).first()
            if template:
                # If not forcing and already has content, skip
                if not force_update and template.homepage_config and len(template.homepage_config.get('blocks', [])) > 0:
                    logger.info(f"[WebsiteService] Tenant '{tenant.slug}' already has a configured template. Skipping.")
                    return template
                logger.info(f"[WebsiteService] Tenant '{tenant.slug}' has an empty or forced template. Updating...")

            # 2. Get template data
            if not template_key or template_key == 'default':
                template_key = 'classic-ecommerce'
            
            if template_key not in AVAILABLE_TEMPLATES:
                logger.warning(f"[WebsiteService] Template '{template_key}' not found. Falling back to 'classic-ecommerce'.")
                template_key = 'classic-ecommerce'
            
            template_data = AVAILABLE_TEMPLATES[template_key]

            # 3. Create or Update WebsiteTemplate
            defaults = {
                'base_template': template_key,
                'site_name': tenant.name,
                
                # Live Config
                'homepage_config': template_data['homepage_config'],
                'theme_config': template_data['theme_config'],
                'navigation_menus': template_data['navigation_menus'],
                'footer_config': template_data['footer_config'],
                'social_links': template_data['social_links'],
                'announcement_bar': template_data['announcement_bar'],
                'analytics_config': template_data['analytics_config'],
                'pwa_config': template_data['pwa_config'],
                'custom_css': template_data.get('custom_css', ''),
                'custom_js': template_data.get('custom_js', ''),

                # Draft Config
                'draft_homepage_config': template_data['homepage_config'],
                'draft_theme_config': template_data['theme_config'],
                'draft_navigation_menus': template_data['navigation_menus'],
                'draft_footer_config': template_data['footer_config'],
                'draft_social_links': template_data['social_links'],
                'draft_announcement_bar': template_data['announcement_bar'],
                'draft_custom_css': template_data.get('custom_css', ''),
                'draft_custom_js': template_data.get('custom_js', ''),

                # Identity & SEO
                'meta_title': f"{tenant.name} - Online Store",
                'meta_description': f"Welcome to {tenant.name}. Shop our latest collections online.",
                'is_active': True
            }

            template, created = WebsiteTemplate.objects.update_or_create(
                tenant=tenant,
                defaults=defaults
            )
            
            # Debug Log
            config_size = len(str(template.homepage_config))
            logger.info(f"[WebsiteService] Template saved. Homepage config size: {config_size} chars. Created: {created}")

            # 4. Create Default Pages (Clear old ones if force_update)
            if force_update:
                template.pages.all().delete()

            for page_data in DEFAULT_PAGES:
                WebsitePage.objects.get_or_create(
                    template=template,
                    slug=page_data['slug'],
                    defaults={
                        'title': page_data['title'],
                        'page_config': page_data['page_config'],
                        'draft_page_config': page_data['page_config'],
                        'meta_title': page_data.get('meta_title', page_data['title']),
                        'meta_description': page_data.get('meta_description', ''),
                        'show_in_menu': True,
                        'sort_order': 1
                    }
                )

            logger.info(f"[WebsiteService] Successfully initialized website for tenant '{tenant.slug}'")
            return template

        except Exception as e:
            logger.error(f"[WebsiteService] Failed to initialize website for tenant '{tenant.slug}': {str(e)}")
            return None
