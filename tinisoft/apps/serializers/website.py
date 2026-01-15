"""
Website Template & Page Serializers
- Public API: Storefront için (sadece gerekli alanlar, tenant bilgisi olmadan)
- Admin API: Tenant panel için (tüm alanlar + düzenleme yetkisi)
"""

from rest_framework import serializers
from apps.models.website import WebsiteTemplate, WebsitePage


# ================================
# PUBLIC SERIALIZERS (Storefront)
# ================================

class PublicWebsitePageSerializer(serializers.ModelSerializer):
    """
    Public API için sayfa serializer (Storefront)
    Sadece aktif sayfalar gösterilir
    """
    
    class Meta:
        model = WebsitePage
        fields = [
            'slug',
            'title',
            'page_config',
            'meta_title',
            'meta_description',
            'show_in_menu',
            'sort_order',
        ]
        read_only_fields = fields  # Tüm alanlar read-only


class PublicWebsiteTemplateSerializer(serializers.ModelSerializer):
    """
    Public API için template serializer (Storefront)
    Domain ile config çekilir, tenant_slug döndürülür (diğer API'ler için)
    """
    pages = PublicWebsitePageSerializer(many=True, read_only=True)
    tenant_slug = serializers.CharField(source='tenant.slug', read_only=True)
    
    class Meta:
        model = WebsiteTemplate
        fields = [
            'tenant_slug',
            'homepage_config',
            'theme_config',
            'site_name',
            'site_logo_url',
            'support_phone',
            'support_email',
            'meta_title',
            'meta_description',
            'custom_css',
            'custom_js',
            # New fields
            'navigation_menus',
            'footer_config',
            'announcement_bar',
            'analytics_config',
            'pwa_config',
            'favicon_url',
            'pages',
        ]
        read_only_fields = fields
    
    def to_representation(self, instance):
        """Sadece aktif sayfaları döndür"""
        representation = super().to_representation(instance)
        # Active pages only
        active_pages = instance.pages.filter(is_active=True).order_by('sort_order')
        representation['pages'] = PublicWebsitePageSerializer(active_pages, many=True).data
        return representation


# ================================
# ADMIN SERIALIZERS (Tenant Panel)
# ================================

class AdminWebsitePageSerializer(serializers.ModelSerializer):
    """
    Admin API için sayfa serializer
    """
    class Meta:
        model = WebsitePage
        fields = [
            'id',
            'slug',
            'title',
            'page_config',      # Live config
            'draft_page_config',# Draft config (Editable)
            'meta_title',
            'meta_description',
            'is_active',
            'show_in_menu',
            'sort_order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'page_config'] # page_config read-only, changes go to draft
    
    def validate_slug(self, value):
        """Slug uniqueness check (within same template)"""
        template = self.context.get('template')
        if template:
            existing = WebsitePage.objects.filter(
                template=template,
                slug=value
            ).exclude(id=self.instance.id if self.instance else None)
            
            if existing.exists():
                raise serializers.ValidationError(
                    f"Bu template'de '{value}' slug'ı zaten kullanılıyor."
                )
        return value


class AdminWebsiteTemplateSerializer(serializers.ModelSerializer):
    """
    Admin API için template serializer
    Draft alanlarını öne çıkarır.
    """
    pages = AdminWebsitePageSerializer(many=True, read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_slug = serializers.CharField(source='tenant.slug', read_only=True)
    preview_url = serializers.SerializerMethodField()
    
    class Meta:
        model = WebsiteTemplate
        fields = [
            'id',
            'tenant_name',
            'tenant_slug',
            'base_template',
            
            # Live Configs (Read-only reference)
            'homepage_config',
            'theme_config',
            
            # Draft Configs (Editable)
            'draft_homepage_config',
            'draft_theme_config',
            'draft_navigation_menus',
            'draft_footer_config',
            'draft_social_links',
            'draft_announcement_bar',
            'draft_custom_css',
            'draft_custom_js',
            
            'site_name',
            'site_logo_url',
            'support_phone',
            'support_email',
            'meta_title',
            'meta_description',
            
            'analytics_config',
            'pwa_config',
            'favicon_url',
            'preview_mode',
            'preview_url',
            
            'is_active',
            'created_at',
            'updated_at',
            'pages',
        ]
        read_only_fields = [
            'id', 'tenant_name', 'tenant_slug', 'preview_url', 
            'created_at', 'updated_at', 'pages',
            'homepage_config', 'theme_config' # Live configs are read-only here
        ]
    
    def get_preview_url(self, obj):
        """Preview URL döndür"""
        if obj.preview_token:
            return obj.get_preview_url()
        return None
    
    def validate_homepage_config(self, value):
        """Validate JSON structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("homepage_config must be a valid JSON object.")
        return value
    
    def validate_theme_config(self, value):
        """Validate JSON structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("theme_config must be a valid JSON object.")
        return value


# ================================
# PAGE CREATE/UPDATE SERIALIZERS
# ================================

class AdminWebsitePageCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Sayfa oluşturma/güncelleme için özel serializer
    """
    
    class Meta:
        model = WebsitePage
        fields = [
            'slug',
            'title',
            'draft_page_config', # Only draft is editable
            'meta_title',
            'meta_description',
            'is_active',
            'show_in_menu',
            'sort_order',
        ]
    
    def create(self, validated_data):
        """Template bilgisi context'ten gelir"""
        template = self.context.get('template')
        if not template:
            raise serializers.ValidationError("Template bilgisi bulunamadı.")
        
        validated_data['template'] = template
        return super().create(validated_data)
