"""
Serializers for new dynamic site features
Form Builder, Popup, URL Redirects, Template Revisions
"""

from rest_framework import serializers
from apps.models.website import (
    CustomForm, FormSubmission,
    Popup, URLRedirect, TemplateRevision
)


# ================================
# FORM BUILDER
# ================================

class CustomFormSerializer(serializers.ModelSerializer):
    """Form builder serializer"""
    
    class Meta:
        model = CustomForm
        fields = [
            'id',
            'name',
            'slug',
            'form_config',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FormSubmissionSerializer(serializers.ModelSerializer):
    """Form gönderileri"""
    form_name = serializers.CharField(source='form.name', read_only=True)
    
    class Meta:
        model = FormSubmission
        fields = [
            'id',
            'form',
            'form_name',
            'data',
            'ip_address',
            'submitted_at',
        ]
        read_only_fields = ['id', 'submitted_at']


# ================================
# POPUP BUILDER
# ================================

class PopupSerializer(serializers.ModelSerializer):
    """Popup/notification builder"""
    
    class Meta:
        model = Popup
        fields = [
            'id',
            'name',
            'type',
            'content',
            'trigger',
            'is_active',
            'priority',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PublicPopupSerializer(serializers.ModelSerializer):
    """Public popup serializer (storefront için)"""
    
    class Meta:
        model = Popup
        fields = [
            'id',
            'type',
            'content',
            'trigger',
        ]


# ================================
# URL REDIRECTS
# ================================

class URLRedirectSerializer(serializers.ModelSerializer):
    """URL redirect management"""
    
    class Meta:
        model = URLRedirect
        fields = [
            'id',
            'from_url',
            'to_url',
            'redirect_type',
            'is_active',
            'hit_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'hit_count', 'created_at', 'updated_at']


# ================================
# TEMPLATE REVISIONS
# ================================

class TemplateRevisionSerializer(serializers.ModelSerializer):
    """Template version control"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = TemplateRevision
        fields = [
            'id',
            'snapshot',
            'note',
            'created_by',
            'created_by_name',
            'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_by_name', 'created_at']
