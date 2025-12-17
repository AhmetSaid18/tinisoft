"""
Abandoned Cart serializers.
"""
from rest_framework import serializers
from apps.models import AbandonedCart
from apps.serializers.cart import CartSerializer


class AbandonedCartSerializer(serializers.ModelSerializer):
    """Abandoned cart serializer."""
    cart = CartSerializer(read_only=True)
    
    class Meta:
        model = AbandonedCart
        fields = [
            'id', 'cart', 'customer_email', 'customer_name', 'customer_phone',
            'abandoned_at', 'last_activity_at',
            'email_sent_count', 'first_email_sent_at', 'last_email_sent_at',
            'recovered_at', 'is_recovered', 'is_ignored',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'abandoned_at', 'last_activity_at', 'created_at', 'updated_at']

