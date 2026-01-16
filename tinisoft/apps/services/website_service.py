import logging
from apps.models.website import WebsiteTemplate, WebsitePage
from apps.utils.website_defaults import AVAILABLE_TEMPLATES, DEFAULT_PAGES

logger = logging.getLogger(__name__)

class WebsiteService:
    """
    Website management service.
    Handles template initialization, page management, and publishing.
    """

    @staticmethod
    def init_tenant_website(tenant, template_key='classic-ecommerce'):
        """
        Initializes a tenant's website with a default template and pages.
        Called during tenant registration.
        """
        try:
            # 1. Check if template already exists
            if hasattr(tenant, 'website_template'):
                logger.warning(f"[WebsiteService] Tenant '{tenant.slug}' already has a website template. Skipping init.")
                return tenant.website_template

            # 2. Get template data
            if template_key not in AVAILABLE_TEMPLATES:
                logger.warning(f"[WebsiteService] Template '{template_key}' not found. Falling back to 'classic-ecommerce'.")
                template_key = 'classic-ecommerce'
            
            template_data = AVAILABLE_TEMPLATES[template_key]

            # 3. Create WebsiteTemplate
            # We initialize both LIVE and DRAFT fields to ensure the site works immediately
            template = WebsiteTemplate.objects.create(
                tenant=tenant,
                base_template=template_key,
                site_name=tenant.name,
                
                # Live Config
                homepage_config=template_data['homepage_config'],
                theme_config=template_data['theme_config'],
                navigation_menus=template_data['navigation_menus'],
                footer_config=template_data['footer_config'],
                social_links=template_data['social_links'],
                announcement_bar=template_data['announcement_bar'],
                analytics_config=template_data['analytics_config'],
                pwa_config=template_data['pwa_config'],
                custom_css=template_data.get('custom_css', ''),
                custom_js=template_data.get('custom_js', ''),

                # Draft Config (copies of live at init)
                draft_homepage_config=template_data['homepage_config'],
                draft_theme_config=template_data['theme_config'],
                draft_navigation_menus=template_data['navigation_menus'],
                draft_footer_config=template_data['footer_config'],
                draft_social_links=template_data['social_links'],
                draft_announcement_bar=template_data['announcement_bar'],
                draft_custom_css=template_data.get('custom_css', ''),
                draft_custom_js=template_data.get('custom_js', ''),

                # Identity & SEO
                meta_title=f"{tenant.name} - Online Store",
                meta_description=f"Welcome to {tenant.name}. Shop our latest collections online.",
                is_active=True
            )

            # 4. Create Default Pages
            for page_data in DEFAULT_PAGES:
                WebsitePage.objects.create(
                    template=template,
                    slug=page_data['slug'],
                    title=page_data['title'],
                    page_config=page_data['page_config'],
                    # Draft fields for pages should also be initialized
                    draft_page_config=page_data['page_config'],
                    meta_title=page_data.get('meta_title', page_data['title']),
                    meta_description=page_data.get('meta_description', ''),
                    show_in_menu=True,
                    sort_order=1
                )

            logger.info(f"[WebsiteService] Successfully initialized website for tenant '{tenant.slug}' with template '{template_key}'")
            return template

        except Exception as e:
            logger.error(f"[WebsiteService] Failed to initialize website for tenant '{tenant.slug}': {str(e)}")
            return None
