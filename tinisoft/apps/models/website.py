from django.db import models
# from .tenant import Tenant  <-- Circular import'a neden oluyor


class WebsiteTemplate(models.Model):
    """
    Her tenant'ın kendi website template'i.
    GrapesJS veya manuel olarak düzenlenen sayfa yapısını JSON olarak saklar.
    """
    tenant = models.OneToOneField(
        'Tenant',  # String referans kullan
        on_delete=models.CASCADE,
        related_name='website_template',
        help_text="Bu template'in ait olduğu tenant"
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
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Template aktif mi?"
    )
    
    class Meta:
        db_table = 'website_templates'
        verbose_name = 'Website Template'
        verbose_name_plural = 'Website Templates'
    
    def __str__(self):
        return f"Template: {self.tenant.name} ({self.tenant.slug})"


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
        help_text="Bu sayfanın component block'ları"
    )
    
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'website_pages'
        verbose_name = 'Website Page'
        verbose_name_plural = 'Website Pages'
        unique_together = ['template', 'slug']
        ordering = ['sort_order', 'title']
    
    def __str__(self):
        return f"{self.template.tenant.slug} - {self.title} ({self.slug})"
