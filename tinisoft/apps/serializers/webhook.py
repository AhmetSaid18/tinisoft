"""
Webhook serializers.
"""
from rest_framework import serializers
from apps.models import Webhook, WebhookEvent


class WebhookEventSerializer(serializers.ModelSerializer):
    """Webhook event serializer."""
    
    class Meta:
        model = WebhookEvent
        fields = [
            'id', 'event_type', 'payload', 'request_url', 'request_method',
            'request_headers', 'request_body', 'response_status',
            'response_body', 'response_time_ms', 'is_success',
            'error_message', 'retry_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class WebhookSerializer(serializers.ModelSerializer):
    """Webhook serializer."""
    events_count = serializers.SerializerMethodField()
    last_event = serializers.SerializerMethodField()
    
    class Meta:
        model = Webhook
        fields = [
            'id', 'name', 'url', 'events', 'secret_key', 'status',
            'success_count', 'failure_count', 'last_triggered_at',
            'events_count', 'last_event', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'secret_key', 'success_count', 'failure_count', 'last_triggered_at', 'created_at', 'updated_at']
    
    def get_events_count(self, obj):
        """Toplam event sayısı."""
        return obj.webhook_events.count()
    
    def get_last_event(self, obj):
        """Son event."""
        last_event = obj.webhook_events.first()
        if last_event:
            return WebhookEventSerializer(last_event).data
        return None


class WebhookCreateSerializer(serializers.ModelSerializer):
    """Webhook create serializer."""
    
    class Meta:
        model = Webhook
        fields = [
            'name', 'url', 'events', 'status',
        ]
    
    def validate_events(self, value):
        """Events array kontrolü."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Events bir array olmalıdır.")
        if len(value) == 0:
            raise serializers.ValidationError("En az bir event seçilmelidir.")
        return value


class WebhookTestSerializer(serializers.Serializer):
    """Webhook test serializer."""
    event_type = serializers.CharField(required=True, max_length=100)
    payload = serializers.JSONField(required=True)

