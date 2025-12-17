"""
Loyalty serializers.
"""
from rest_framework import serializers
from apps.models import LoyaltyProgram, LoyaltyPoints, LoyaltyTransaction


class LoyaltyProgramSerializer(serializers.ModelSerializer):
    """Loyalty program serializer."""
    
    class Meta:
        model = LoyaltyProgram
        fields = [
            'id', 'name', 'description',
            'points_per_currency', 'points_per_order',
            'currency_per_point', 'minimum_points_to_redeem',
            'maximum_points_per_order',
            'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LoyaltyPointsSerializer(serializers.ModelSerializer):
    """Loyalty points serializer."""
    customer_email = serializers.EmailField(source='customer.email', read_only=True)
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LoyaltyPoints
        fields = [
            'id', 'customer', 'customer_email', 'customer_name',
            'total_points', 'available_points', 'used_points', 'expired_points',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_customer_name(self, obj):
        """Müşteri adını döndür."""
        return f"{obj.customer.first_name} {obj.customer.last_name}".strip() or obj.customer.email


class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    """Loyalty transaction serializer."""
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    customer_email = serializers.EmailField(source='loyalty_points.customer.email', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = LoyaltyTransaction
        fields = [
            'id', 'transaction_type', 'transaction_type_display',
            'points', 'customer_email', 'order', 'order_number',
            'reason', 'notes',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

