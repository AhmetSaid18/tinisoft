"""
Currency serializers.
"""
from rest_framework import serializers
from apps.models import Currency


class CurrencySerializer(serializers.ModelSerializer):
    """Currency serializer."""
    
    class Meta:
        model = Currency
        fields = [
            'id', 'code', 'name', 'symbol',
            'exchange_rate', 'decimal_places', 'symbol_position',
            'is_default', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

