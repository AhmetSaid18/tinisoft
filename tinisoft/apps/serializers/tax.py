"""
Tax serializers.
"""
from rest_framework import serializers
from apps.models import Tax


class TaxSerializer(serializers.ModelSerializer):
    """Tax serializer."""
    
    class Meta:
        model = Tax
        fields = [
            'id', 'name', 'rate', 'description',
            'is_default', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_rate(self, value):
        """Rate 0-100 arasında olmalı."""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Vergi oranı 0 ile 100 arasında olmalıdır.")
        return value

