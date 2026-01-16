from django.db import models
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from django.conf import settings
import uuid
import logging

logger = logging.getLogger(__name__)


class WebsiteTemplate(models.Model):
    """
    Her tenant'ın kendi website template'i.
    WordPress benzeri page builder için JSON-based yapı.
    Redis cache ile performans optimizasyonu.
    
    Her tenant bir base template seçer ve kendi kopyasını özelleştirir.
    Örnek: 3 tenant "classic-ecommerce" seçer, her biri kendi renklerini ayarlar.
    """
    
    TEMPLATE_CHOICES = [
        ('modern-minimalist', 'Modern Minimalist'),
        ('classic-ecommerce', 'Classic E-Commerce'),
    ]
    
    tenant = models.OneToOneField(
        'Tenant',  # String referans kullan (circular import'u önler)
        on_delete=models.CASCADE,
        related_name='website_template',
        help_text="Bu template'in ait olduğu tenant"
    )
    
    # Template seçimi (WordPress tema seçimi gibi)
    base_template = models.CharField(
        max_length=50,
        choices=TEMPLATE_CHOICES,
        default='classic-ecommerce',
        help_text="Seçilen base template (her tenant kendi kopyasını özelleştirir)"
    )
    
    # Ana sayfa yapılandırması (JSON - block'lar)
    homepage_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Ana sayfa için component block'ları ve özellikleri"
    )
    
    # Tema ayarları (renkler, fontlar vb.)
    theme_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Site teması: renkler, fontlar, logo vb."
    )
    
    # Site bilgileri
    site_name = models.CharField(
        max_length=255,
        default="",
        blank=True,
        help_text="Site adı (örn: Avrupa Mutfak)"
    )
    
    site_logo_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Logo URL'i (Cloudflare R2 veya başka CDN)"
    )
    
    support_phone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Müşteri destek telefonu"
    )
    
    support_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Müşteri destek e-posta"
    )
    
    # SEO & Meta


    # ================================
    # CONFIGURATION (LIVE & DRAFT)
    # ================================
    
    # 1. LIVE CONFIGS (Storefront'ta görünen)
    homepage_config = models.JSONField(default=dict, blank=True)
    theme_config = models.JSONField(default=dict, blank=True)
    navigation_menus = models.JSONField(default=dict, blank=True)
    footer_config = models.JSONField(default=dict, blank=True)
    
    # 2. DRAFT CONFIGS (Admin panelde düzenlenen)
    draft_homepage_config = models.JSONField(default=dict, blank=True)
    draft_theme_config = models.JSONField(default=dict, blank=True)
    draft_navigation_menus = models.JSONField(default=dict, blank=True)
    draft_footer_config = models.JSONField(default=dict, blank=True)

    # ================================
    # SITE IDENTITY
    # ================================
    
    site_name = models.CharField(max_length=255)
    site_logo_url = models.URLField(max_length=500, blank=True, null=True)
    favicon_url = models.URLField(max_length=500, blank=True, null=True)
    
    support_phone = models.CharField(max_length=50, blank=True, null=True)
    support_email = models.EmailField(blank=True, null=True)
    
    # ================================
    # EXTRAS
    # ================================
    
    social_links = models.JSONField(default=dict, blank=True)
    announcement_bar = models.JSONField(default=dict, blank=True)
    
    # Draft versions for extras
    draft_social_links = models.JSONField(default=dict, blank=True)
    draft_announcement_bar = models.JSONField(default=dict, blank=True)

    # ================================
    # SEO & ANALYTICS
    # ================================
    
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    
    analytics_config = models.JSONField(default=dict, blank=True)
    
    # ================================
    # CUSTOM CODE (LIVE & DRAFT)
    # ================================
    
    custom_css = models.TextField(blank=True, null=True)
    custom_js = models.TextField(blank=True, null=True)
    
    draft_custom_css = models.TextField(blank=True, null=True)
    draft_custom_js = models.TextField(blank=True, null=True)

    # ================================
    # PWA & PREVIEW
    # ================================
    
    pwa_config = models.JSONField(default=dict, blank=True)
    
    preview_mode = models.BooleanField(default=False)
    preview_token = models.CharField(max_length=100, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'website_templates'
        verbose_name = 'Website Template'
        verbose_name_plural = 'Website Templates'
        indexes = [
            models.Index(fields=['tenant'], name='idx_website_tenant'),
            models.Index(fields=['is_active'], name='idx_website_active'),
            models.Index(fields=['updated_at'], name='idx_website_updated'),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.base_template}"
    
    @staticmethod
    def get_cache_key(tenant_id=None, domain=None):
        """Redis cache key generator"""
        if tenant_id:
            return f"website_template:tenant:{tenant_id}"
        elif domain:
            return f"website_template:domain:{domain}"
        return None
    
    def invalidate_cache(self):
        """Redis cache temizle"""
        cache_key = f"storefront_config:{self.tenant.slug}" # Eski domain bazlı cache yerine slug bazlı
        # Domain lookup için cache key'i domain'den bulmamız gerekebilir
        # Şimdilik basitçe tenant slug kullanıyoruz
        pass
    
    @classmethod
    def get_by_domain(cls, domain):
        """Domain'e göre template getir (cache'li)"""
        cache_key = cls.get_cache_key(domain=domain)
        cached = cache.get(cache_key)
        
        if cached is not None:
            return cached
        
        try:
            from apps.models import Tenant
            from django.db.models import Q
            
            # Tek query ile hem tenant alanlarını tara hem template'i getir
            q = Q(tenant__custom_domain=domain) | Q(tenant__domains__domain_name=domain)
            
            # Subdomain kontrolü (örn: ates.tinisoft.com.tr)
            if 'tinisoft.com.tr' in domain:
                subdomain_part = domain.split('.')[0]
                q |= Q(tenant__subdomain=subdomain_part)

            template = cls.objects.select_related('tenant').filter(q, is_active=True).distinct().first()

            if template:
                logger.info(f"[WebsiteTemplate] MATCH: Template found for '{domain}' (Tenant: {template.tenant.slug})")
                cache.set(cache_key, template, timeout=3600)  # 1 saat cache
                return template
            
            logger.warning(f"[WebsiteTemplate] NO MATCH: No template/tenant found for domain '{domain}'")
            return None
        except Exception as e:
            logger.error(f"[WebsiteTemplate] ERROR: get_by_domain failed for '{domain}': {str(e)}")
            return None
    
    def generate_preview_token(self):
        """Preview mode için random token oluştur"""
        import secrets
        self.preview_token = secrets.token_urlsafe(32)
        self.save(update_fields=['preview_token'])
        return self.preview_token
    
    def get_preview_url(self):
        """Preview URL döndür"""
        if not self.preview_token:
            self.generate_preview_token()
        return f"/preview/{self.preview_token}/"

    def publish_changes(self):
        """Draft verilerini Live'a kopyalar"""
        self.homepage_config = self.draft_homepage_config
        self.theme_config = self.draft_theme_config
        self.navigation_menus = self.draft_navigation_menus
        self.footer_config = self.draft_footer_config
        self.social_links = self.draft_social_links
        self.announcement_bar = self.draft_announcement_bar
        self.custom_css = self.draft_custom_css
        self.custom_js = self.draft_custom_js
        self.save()
        
        # Sayfaları da publish et
        for page in self.pages.all():
            if hasattr(page, 'publish_changes'):
                page.publish_changes()



class WebsitePage(models.Model):
    """
    Template içindeki özel sayfalar (Hakkımızda, İletişim, vb.)
    Ana sayfa homepage_config'de saklanır.
    """
    template = models.ForeignKey(
        WebsiteTemplate,
        on_delete=models.CASCADE,
        related_name='pages',
        help_text="Bu sayfanın ait olduğu template"
    )
    
    slug = models.SlugField(
        max_length=255,
        help_text="Sayfa slug'ı (örn: hakkimizda, iletisim)"
    )
    
    title = models.CharField(
        max_length=255,
        help_text="Sayfa başlığı"
    )
    
    page_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Bu sayfanın component block'ları (Live)"
    )
    
    draft_page_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Bu sayfanın component block'ları (Draft)"
    )

    def publish_changes(self):
        """Draft verisini Live'a kopyalar"""
        self.page_config = self.draft_page_config
        self.save()

    
    # SEO & Meta
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="SEO meta title (boşsa title kullanılır)"
    )
    
    meta_description = models.TextField(
        blank=True,
        null=True,
        help_text="SEO meta description"
    )
    
    # Visibility
    is_active = models.BooleanField(
        default=True,
        help_text="Sayfa aktif mi?"
    )
    
    show_in_menu = models.BooleanField(
        default=True,
        help_text="Menüde görünsün mü?"
    )
    
    sort_order = models.IntegerField(
        default=0,
        help_text="Menüdeki sıralama"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'website_pages'
        verbose_name = 'Website Page'
        verbose_name_plural = 'Website Pages'
        unique_together = ['template', 'slug']
        ordering = ['sort_order', 'title']
        indexes = [
            models.Index(fields=['template', 'slug'], name='idx_page_template_slug'),
            models.Index(fields=['template', 'is_active'], name='idx_page_template_active'),
            models.Index(fields=['sort_order'], name='idx_page_sort'),
        ]
    
    def __str__(self):
        return f"{self.template.tenant.slug} - {self.title} ({self.slug})"


# Signal: Cache invalidation
@receiver(post_save, sender=WebsiteTemplate)
@receiver(post_delete, sender=WebsiteTemplate)
def invalidate_template_cache(sender, instance, **kwargs):
    """Template kaydedildiğinde veya silindiğinde cache'i temizle"""
    instance.invalidate_cache()


@receiver(post_save, sender=WebsitePage)
@receiver(post_delete, sender=WebsitePage)
def invalidate_page_cache(sender, instance, **kwargs):
    """Page değiştiğinde template cache'ini de temizle"""
    instance.template.invalidate_cache()


# ================================
# CUSTOM FORMS
# ================================

class CustomForm(models.Model):
    """
    Özel form builder (İletişim formu, başvuru formu vs.)
    """
    template = models.ForeignKey(
        WebsiteTemplate,
        on_delete=models.CASCADE,
        related_name='custom_forms'
    )
    
    name = models.CharField(max_length=255, help_text="Form adı (örn: İletişim Formu)")
    slug = models.SlugField(max_length=255, help_text="Form slug (URL için)")
    
    form_config = models.JSONField(
        default=dict,
        help_text="Form alanları ve ayarları: {fields: [...], submit_action: {...}}"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'custom_forms'
        unique_together = ['template', 'slug']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.template.tenant.slug} - {self.name}"


class FormSubmission(models.Model):
    """Form gönderileri"""
    form = models.ForeignKey(CustomForm, on_delete=models.CASCADE, related_name='submissions')
    data = models.JSONField(help_text="Gönderilen form data")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'form_submissions'
        ordering = ['-submitted_at']


# ================================
# POPUPS / NOTIFICATIONS
# ================================

class Popup(models.Model):
    """
    Popup/Modal builder (Newsletter, indirim, duyuru)
    """
    
    TYPE_CHOICES = [
        ('newsletter', 'Newsletter'),
        ('discount', 'İndirim'),
        ('announcement', 'Duyuru'),
        ('exit_intent', 'Çıkış Niyeti'),
    ]
    
    TRIGGER_CHOICES = [
        ('time_delay', 'Zaman Gecikmesi'),
        ('scroll_percent', 'Scroll Yüzdesi'),
        ('exit_intent', 'Çıkış Niyeti'),
        ('on_load', 'Sayfa Yüklenince'),
    ]
    
    template = models.ForeignKey(
        WebsiteTemplate,
        on_delete=models.CASCADE,
        related_name='popups'
    )
    
    name = models.CharField(max_length=255, help_text="Popup adı")
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='announcement')
    
    content = models.JSONField(
        default=dict,
        help_text="Popup içeriği: {title, description, button_text, image, ...}"
    )
    
    trigger = models.JSONField(
        default=dict,
        help_text="Tetikleme ayarları: {type: 'time_delay', value: 5000}"
    )
    
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Öncelik (yüksek önce gösterilir)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'popups'
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.template.tenant.slug} - {self.name}"


# ================================
# URL REDIRECTS
# ================================

class URLRedirect(models.Model):
    """
    URL yönlendirme (SEO için 301/302 redirects)
    """
    
    TYPE_CHOICES = [
        ('301', '301 Permanent'),
        ('302', '302 Temporary'),
    ]
    
    template = models.ForeignKey(
        WebsiteTemplate,
        on_delete=models.CASCADE,
        related_name='url_redirects'
    )
    
    from_url = models.CharField(max_length=500, help_text="Kaynak URL (örn: /eski-sayfa)")
    to_url = models.CharField(max_length=500, help_text="Hedef URL (örn: /yeni-sayfa)")
    redirect_type = models.CharField(max_length=3, choices=TYPE_CHOICES, default='301')
    
    is_active = models.BooleanField(default=True)
    hit_count = models.IntegerField(default=0, help_text="Kaç kez kullanıldı")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'url_redirects'
        unique_together = ['template', 'from_url']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_url} → {self.to_url} ({self.redirect_type})"


# ================================
# TEMPLATE REVISIONS (Version Control)
# ================================

class TemplateRevision(models.Model):
    """
    Template değişiklik geçmişi (version control)
    """
    template = models.ForeignKey(
        WebsiteTemplate,
        on_delete=models.CASCADE,
        related_name='revisions'
    )
    
    snapshot = models.JSONField(help_text="O anki template data (tüm config'ler)")
    note = models.CharField(max_length=500, blank=True, help_text="Değişiklik notu")
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'template_revisions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.template.tenant.slug} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


# ================================
# SIGNALS (Cache Management)
# ================================

@receiver(post_save, sender=WebsiteTemplate)
@receiver(post_delete, sender=WebsiteTemplate)
def clear_template_cache(sender, instance, **kwargs):
    """Template veya Tenant ayarı değiştiğinde tüm olası cache keyleri temizle"""
    # Domain key'leri (get_by_domain tarafında kullanılanlar)
    keys = [
        f"website_template_{instance.tenant.slug}",
        f"website_template_{instance.tenant.custom_domain}" if instance.tenant.custom_domain else None,
        f"website_template_{instance.tenant.subdomain}.tinisoft.com.tr"
    ]
    for key in keys:
        if key:
            cache.delete(key)
    # Log: Cache temizlendiğini görelim
    print(f"[Signals] Cache cleared for tenant: {instance.tenant.slug}")

@receiver(post_save, sender=WebsitePage)
@receiver(post_delete, sender=WebsitePage)
def clear_page_cache(sender, instance, **kwargs):
    """Sayfa değiştiğinde bağlı olduğu template'in cache'ini temizle"""
    if instance.template:
        clear_template_cache(WebsiteTemplate, instance.template)

