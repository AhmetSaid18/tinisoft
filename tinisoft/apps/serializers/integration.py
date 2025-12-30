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
    
    def validate_test_endpoint(self, value):
        """Test endpoint validasyonu."""
        if value:
            # Sadece host girilmişse (path eksik) uyar
            if value.count('/') < 3 or not (value.endswith('.svc') or value.endswith('.asmx')):
                raise serializers.ValidationError(
                    'Test endpoint tam URL olmalı (örn: https://customerservicestest.araskargo.com.tr/ArasCargoIntegrationService.svc). '
                    'Sadece host girilmemeli.'
                )
        return value
    
    def validate_api_endpoint(self, value):
        """API endpoint validasyonu."""
        if value:
            # Sadece host girilmişse (path eksik) uyar
            if value.count('/') < 3 or not (value.endswith('.svc') or value.endswith('.asmx')):
                raise serializers.ValidationError(
                    'API endpoint tam URL olmalı (örn: https://customerservices.araskargo.com.tr/ArasCargoCustomerIntegrationService/ArasCargoIntegrationService.svc). '
                    'Sadece host girilmemeli.'
                )
        return value
    
    def validate(self, data):
        """Validation."""
        # Test modunda test_endpoint zorunlu ve doğru format olmalı
        if data.get('status') == IntegrationProvider.Status.TEST_MODE:
            test_endpoint = data.get('test_endpoint') or (self.instance.test_endpoint if self.instance else None)
            if not test_endpoint:
                raise serializers.ValidationError({
                    'test_endpoint': 'Test modu için test endpoint gereklidir.'
                })
            # Test modunda API endpoint prod'a işaret ediyorsa uyar
            api_endpoint = data.get('api_endpoint') or (self.instance.api_endpoint if self.instance else None)
            if api_endpoint and 'customerservices.araskargo.com.tr' in api_endpoint and 'customerservicestest' not in api_endpoint:
                raise serializers.ValidationError({
                    'api_endpoint': 'Test modunda production endpoint kullanılamaz. Test endpoint kullanın.'
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
    
    def validate_test_endpoint(self, value):
        """Test endpoint validasyonu."""
        if value:
            # Sadece host girilmişse (path eksik) uyar
            if value.count('/') < 3 or not (value.endswith('.svc') or value.endswith('.asmx')):
                raise serializers.ValidationError(
                    'Test endpoint tam URL olmalı (örn: https://customerservicestest.araskargo.com.tr/ArasCargoIntegrationService.svc). '
                    'Sadece host girilmemeli.'
                )
        return value
    
    def validate_api_endpoint(self, value):
        """API endpoint validasyonu."""
        if value:
            # Sadece host girilmişse (path eksik) uyar
            if value.count('/') < 3 or not (value.endswith('.svc') or value.endswith('.asmx')):
                raise serializers.ValidationError(
                    'API endpoint tam URL olmalı (örn: https://customerservices.araskargo.com.tr/ArasCargoCustomerIntegrationService/ArasCargoIntegrationService.svc). '
                    'Sadece host girilmemeli.'
                )
        return value
    
    def validate(self, data):
        """Validation."""
        # Test modunda test_endpoint zorunlu ve doğru format olmalı
        if data.get('status') == IntegrationProvider.Status.TEST_MODE:
            test_endpoint = data.get('test_endpoint')
            if not test_endpoint:
                raise serializers.ValidationError({
                    'test_endpoint': 'Test modu için test endpoint gereklidir.'
                })
            # Test modunda API endpoint prod'a işaret ediyorsa uyar
            api_endpoint = data.get('api_endpoint')
            if api_endpoint and 'customerservices.araskargo.com.tr' in api_endpoint and 'customerservicestest' not in api_endpoint:
                raise serializers.ValidationError({
                    'api_endpoint': 'Test modunda production endpoint kullanılamaz. Test endpoint kullanın.'
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
        config_data = validated_data.pop('config', None)
        
        # Normal field'ları güncelle
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Config'i merge et (yeni değerler varsa güncelle)
        if config_data is not None:
            # Mevcut config'i al
            current_config = instance.config or {}
            # Yeni config ile merge et (deep merge)
            if isinstance(config_data, dict):
                # Deep merge yap (nested dict'ler için)
                def deep_merge(base, new):
                    for key, value in new.items():
                        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                            deep_merge(base[key], value)
                        else:
                            base[key] = value
                    return base
                
                deep_merge(current_config, config_data)
                instance.config = current_config
        
        # API key'leri güncelle (sadece gönderilmişse)
        if api_key is not None:
            instance.set_api_key(api_key)
        if api_secret is not None:
            instance.set_api_secret(api_secret)
        if api_token is not None:
            instance.set_api_token(api_token)
        
        instance.save()
        return instance
    
    def validate_test_endpoint(self, value):
        """Test endpoint validasyonu."""
        if value:
            # Sadece host girilmişse (path eksik) uyar
            if value.count('/') < 3 or not (value.endswith('.svc') or value.endswith('.asmx')):
                raise serializers.ValidationError(
                    'Test endpoint tam URL olmalı (örn: https://customerservicestest.araskargo.com.tr/ArasCargoIntegrationService.svc). '
                    'Sadece host girilmemeli.'
                )
        return value
    
    def validate_api_endpoint(self, value):
        """API endpoint validasyonu."""
        if value:
            # Sadece host girilmişse (path eksik) uyar
            if value.count('/') < 3 or not (value.endswith('.svc') or value.endswith('.asmx')):
                raise serializers.ValidationError(
                    'API endpoint tam URL olmalı (örn: https://customerservices.araskargo.com.tr/ArasCargoCustomerIntegrationService/ArasCargoIntegrationService.svc). '
                    'Sadece host girilmemeli.'
                )
        return value
    
    def validate(self, data):
        """Validation."""
        # Test endpoint girilmişse ve status belirtilmemişse otomatik test_mode yap
        if data.get('test_endpoint') and not data.get('status'):
            data['status'] = IntegrationProvider.Status.TEST_MODE
        
        # API key'ler girilmişse ve status belirtilmemişse otomatik active yap
        if (data.get('api_key') or data.get('api_secret')) and not data.get('status'):
            # Mevcut instance varsa status'ünü koru, yoksa active yap
            if not self.instance or not self.instance.status:
                data['status'] = IntegrationProvider.Status.ACTIVE
        
        # Test modunda test_endpoint zorunlu ve doğru format olmalı
        if data.get('status') == IntegrationProvider.Status.TEST_MODE:
            test_endpoint = data.get('test_endpoint') or (self.instance.test_endpoint if self.instance else None)
            if not test_endpoint:
                raise serializers.ValidationError({
                    'test_endpoint': 'Test modu için test endpoint gereklidir.'
                })
            # Test modunda API endpoint prod'a işaret ediyorsa uyar
            api_endpoint = data.get('api_endpoint') or (self.instance.api_endpoint if self.instance else None)
            if api_endpoint and 'customerservices.araskargo.com.tr' in api_endpoint and 'customerservicestest' not in api_endpoint:
                raise serializers.ValidationError({
                    'api_endpoint': 'Test modunda production endpoint kullanılamaz. Test endpoint kullanın.'
                })
        return data


class IntegrationProviderTestSerializer(serializers.Serializer):
    """Integration provider test serializer."""
    test_data = serializers.JSONField(required=False, default=dict)

