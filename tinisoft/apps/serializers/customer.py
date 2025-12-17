"""
Customer serializers.
"""
from rest_framework import serializers
from apps.models import Customer


class CustomerListSerializer(serializers.ModelSerializer):
    """Customer list serializer (lightweight)."""
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'email', 'full_name', 'phone',
            'total_orders', 'total_spent', 'average_order_value',
            'is_active', 'is_verified', 'customer_group',
            'first_order_at', 'last_order_at', 'last_login_at',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'total_orders', 'total_spent', 'average_order_value']
    
    def get_full_name(self, obj):
        """Tam adı döndür."""
        return f"{obj.first_name} {obj.last_name}"


class CustomerDetailSerializer(serializers.ModelSerializer):
    """Customer detail serializer (full)."""
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'date_of_birth', 'gender',
            'total_orders', 'total_spent', 'average_order_value',
            'is_active', 'is_verified', 'is_newsletter_subscribed',
            'customer_group', 'tags',
            'first_order_at', 'last_order_at', 'last_login_at',
            'notes', 'metadata',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'email', 'created_at', 'updated_at',
            'total_orders', 'total_spent', 'average_order_value',
        ]
    
    def get_full_name(self, obj):
        """Tam adı döndür."""
        return f"{obj.first_name} {obj.last_name}"

