"""
Payment serializers.
"""
from rest_framework import serializers
from apps.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Payment serializer."""
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_number', 'order', 'order_number',
            'method', 'method_display', 'status', 'status_display',
            'amount', 'currency',
            'provider', 'transaction_id', 'payment_intent_id',
            'paid_at', 'failed_at', 'refunded_at',
            'error_message', 'error_code',
            'ip_address', 'user_agent', 'metadata',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'payment_number', 'created_at', 'updated_at',
            'paid_at', 'failed_at', 'refunded_at',
        ]


class CreatePaymentSerializer(serializers.Serializer):
    """Create payment serializer."""
    order_id = serializers.UUIDField()
    method = serializers.ChoiceField(choices=Payment.PaymentMethod.choices)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    provider = serializers.CharField(max_length=50, required=False, allow_blank=True)

