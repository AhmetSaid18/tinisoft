"""
Integration serializers.
"""
from rest_framework import serializers
from apps.models import IntegrationProvider
from core.middleware import get_tenant_from_request


class IntegrationProviderSerializer(serializers.ModelSerializer):
    """Integration provider serializer."""
    
    # Read-only fields (şifreli değerler gösterilmez)
    provider_type_display = serializers.CharField(source='get_provider_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = IntegrationProvider
        fields = [
            'id', 'provider_type', 'provider_type_display',
            'name', 'description',
            'status', 'status_display',
            'api_endpoint', 'test_endpoint',
            'config',
            'last_used_at', 'last_error',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_used_at', 'last_error']
    
    def validate(self, data):
        """Validation."""
        # Test modunda test_endpoint zorunlu
        if data.get('status') == IntegrationProvider.Status.TEST_MODE:
            if not data.get('test_endpoint'):
                raise serializers.ValidationError({
                    'test_endpoint': 'Test modu için test endpoint gereklidir.'
                })
        return data


class IntegrationProviderCreateSerializer(serializers.ModelSerializer):
    """Integration provider create serializer (API key'ler dahil)."""
    
    # API key'ler düz metin olarak alınır, şifrelenerek kaydedilir
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    api_secret = serializers.CharField(write_only=True, required=False, allow_blank=True)
    api_token = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = IntegrationProvider
        fields = [
            'provider_type', 'name', 'description',
            'status',
            'api_key', 'api_secret', 'api_token',
            'api_endpoint', 'test_endpoint',
            'config',
        ]
    
    def create(self, validated_data):
        """Create integration provider."""
        # Get the underlying Django request from DRF Request wrapper
        request = self.context['request']._request
        tenant = get_tenant_from_request(request)
        if not tenant:
            raise serializers.ValidationError('Tenant bulunamadı.')
        
        api_key = validated_data.pop('api_key', '')
        api_secret = validated_data.pop('api_secret', '')
        api_token = validated_data.pop('api_token', '')
        
        integration = IntegrationProvider.objects.create(
            tenant=tenant,
            **validated_data
        )
        
        # API key'leri şifreleyerek kaydet
        if api_key:
            integration.set_api_key(api_key)
        if api_secret:
            integration.set_api_secret(api_secret)
        if api_token:
            integration.set_api_token(api_token)
        
        integration.save()
        return integration
    
    def validate(self, data):
        """Validation."""
        # Test modunda test_endpoint zorunlu
        if data.get('status') == IntegrationProvider.Status.TEST_MODE:
            if not data.get('test_endpoint'):
                raise serializers.ValidationError({
                    'test_endpoint': 'Test modu için test endpoint gereklidir.'
                })
        return data


class IntegrationProviderUpdateSerializer(serializers.ModelSerializer):
    """Integration provider update serializer."""
    
    # API key'ler opsiyonel (sadece güncellenmek istenirse gönderilir)
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    api_secret = serializers.CharField(write_only=True, required=False, allow_blank=True)
    api_token = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = IntegrationProvider
        fields = [
            'name', 'description',
            'status',
            'api_key', 'api_secret', 'api_token',
            'api_endpoint', 'test_endpoint',
            'config',
        ]
    
    def update(self, instance, validated_data):
        """Update integration provider."""
        api_key = validated_data.pop('api_key', None)
        api_secret = validated_data.pop('api_secret', None)
        api_token = validated_data.pop('api_token', None)
        
        # Normal field'ları güncelle
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # API key'leri güncelle (sadece gönderilmişse)
        if api_key is not None:
            instance.set_api_key(api_key)
        if api_secret is not None:
            instance.set_api_secret(api_secret)
        if api_token is not None:
            instance.set_api_token(api_token)
        
        instance.save()
        return instance
    
    def validate(self, data):
        """Validation."""
        # Test modunda test_endpoint zorunlu
        if data.get('status') == IntegrationProvider.Status.TEST_MODE:
            if not data.get('test_endpoint') and not self.instance.test_endpoint:
                raise serializers.ValidationError({
                    'test_endpoint': 'Test modu için test endpoint gereklidir.'
                })
        return data


class IntegrationProviderTestSerializer(serializers.Serializer):
    """Integration provider test serializer."""
    test_data = serializers.JSONField(required=False, default=dict)

