"""
Gift Card serializers.
"""
from rest_framework import serializers
from apps.models import GiftCard, GiftCardTransaction
from apps.serializers.auth import UserSerializer


class GiftCardTransactionSerializer(serializers.ModelSerializer):
    """Gift card transaction serializer."""
    
    class Meta:
        model = GiftCardTransaction
        fields = [
            'id', 'gift_card', 'transaction_type', 'amount',
            'order', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class GiftCardSerializer(serializers.ModelSerializer):
    """Gift card serializer."""
    customer = UserSerializer(read_only=True)
    transactions = GiftCardTransactionSerializer(many=True, read_only=True)
    
    class Meta:
        model = GiftCard
        fields = [
            'id', 'code', 'type', 'initial_amount', 'current_amount',
            'percentage_value', 'customer', 'customer_email',
            'valid_from', 'valid_until', 'status', 'usage_count',
            'last_used_at', 'note', 'transactions',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'current_amount', 'usage_count', 'last_used_at', 'created_at', 'updated_at']


class GiftCardCreateSerializer(serializers.ModelSerializer):
    """Gift card create serializer."""
    
    class Meta:
        model = GiftCard
        fields = [
            'code', 'type', 'initial_amount', 'percentage_value',
            'customer_email', 'valid_from', 'valid_until', 'note',
        ]
        extra_kwargs = {
            'code': {'required': False, 'allow_blank': True, 'allow_null': True},
        }
    
    def validate_code(self, value):
        """Code unique kontrolü."""
        # Tenant bazında kontrol edilecek view'da
        return value
    
    def validate(self, data):
        """Validasyon."""
        if data.get('type') == 'percentage' and not data.get('percentage_value'):
            raise serializers.ValidationError({
                'percentage_value': 'Yüzde tipinde kart için percentage_value gerekli.'
            })
        return data


class GiftCardValidateSerializer(serializers.Serializer):
    """Gift card validation serializer."""
    code = serializers.CharField(required=True, max_length=50)
    order_amount = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, default=0.00)


class GiftCardApplySerializer(serializers.Serializer):
    """Gift card apply serializer."""
    code = serializers.CharField(required=True, max_length=50)
    order_amount = serializers.DecimalField(required=True, max_digits=10, decimal_places=2)

