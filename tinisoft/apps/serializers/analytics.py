"""
Analytics serializers.
"""
from rest_framework import serializers
from apps.models import AnalyticsEvent, SalesReport, ProductAnalytics
from apps.serializers.product import ProductListSerializer
from apps.serializers.auth import UserSerializer


class AnalyticsEventSerializer(serializers.ModelSerializer):
    """Analytics event serializer."""
    customer = UserSerializer(read_only=True)
    
    class Meta:
        model = AnalyticsEvent
        fields = [
            'id', 'event_type', 'customer', 'session_id',
            'event_data', 'ip_address', 'user_agent', 'referrer', 'url',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AnalyticsEventCreateSerializer(serializers.ModelSerializer):
    """Analytics event create serializer (public)."""
    
    class Meta:
        model = AnalyticsEvent
        fields = [
            'event_type', 'session_id', 'event_data',
            'ip_address', 'user_agent', 'referrer', 'url',
        ]


class SalesReportSerializer(serializers.ModelSerializer):
    """Sales report serializer."""
    
    class Meta:
        model = SalesReport
        fields = [
            'id', 'period', 'period_start', 'period_end',
            'total_orders', 'total_revenue', 'total_products_sold',
            'average_order_value', 'new_customers', 'returning_customers',
            'total_discounts', 'total_coupons_used', 'total_shipping_cost',
            'metadata', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductAnalyticsSerializer(serializers.ModelSerializer):
    """Product analytics serializer."""
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = ProductAnalytics
        fields = [
            'id', 'product', 'view_count', 'unique_viewers',
            'sale_count', 'total_revenue', 'add_to_cart_count',
            'remove_from_cart_count', 'cart_conversion_rate',
            'conversion_rate', 'report_date',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

