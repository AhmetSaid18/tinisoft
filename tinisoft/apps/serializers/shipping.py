"""
Shipping serializers.
"""
from rest_framework import serializers
from apps.models import ShippingMethod, ShippingAddress, ShippingZone, ShippingZoneRate


class ShippingMethodSerializer(serializers.ModelSerializer):
    """Shipping method serializer."""
    
    class Meta:
        model = ShippingMethod
        fields = [
            'id', 'name', 'code', 'is_active', 'price',
            'free_shipping_threshold', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ShippingAddressSerializer(serializers.ModelSerializer):
    """Shipping address serializer."""
    
    # Fatura adresi için opsiyonel alanlar
    tax_id = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    tax_office = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    company_name = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = ShippingAddress
        fields = [
            'id', 'user', 'address_type', 'first_name', 'last_name', 'phone',
            'address_line_1', 'address_line_2', 'city', 'state',
            'postal_code', 'country', 'is_default',
            'tax_id', 'tax_office', 'company_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Fatura adresi için vergi bilgilerini kontrol et."""
        address_type = data.get('address_type', 'shipping')
        
        # Eğer kargo adresi ise, vergi alanlarını temizle
        if address_type == 'shipping':
            data['tax_id'] = None
            data['tax_office'] = None
            data['company_name'] = None
        
        return data


class ShippingZoneRateSerializer(serializers.ModelSerializer):
    """Shipping zone rate serializer."""
    shipping_method = ShippingMethodSerializer(read_only=True)
    shipping_method_id = serializers.PrimaryKeyRelatedField(
        queryset=ShippingMethod.objects.none(),
        write_only=True,
        required=False,
        source='shipping_method'
    )
    
    class Meta:
        model = ShippingZoneRate
        fields = [
            'id', 'zone', 'shipping_method', 'shipping_method_id',
            'price', 'free_shipping_threshold', 'weight_based_pricing',
            'base_weight', 'base_price', 'additional_weight_price',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'zone', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get('request'):
            tenant = self.context['request'].user.tenant if hasattr(self.context['request'].user, 'tenant') else None
            if tenant:
                self.fields['shipping_method_id'].queryset = ShippingMethod.objects.filter(tenant=tenant, is_deleted=False)


class ShippingZoneSerializer(serializers.ModelSerializer):
    """Shipping zone serializer."""
    rates = ShippingZoneRateSerializer(many=True, read_only=True)
    
    class Meta:
        model = ShippingZone
        fields = [
            'id', 'name', 'description', 'countries', 'cities',
            'postal_codes', 'is_active', 'rates',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ShippingCalculateSerializer(serializers.Serializer):
    """Shipping cost calculation serializer."""
    shipping_method_id = serializers.UUIDField(required=True)
    country = serializers.CharField(required=True, max_length=100)
    city = serializers.CharField(required=False, allow_null=True, max_length=100)
    postal_code = serializers.CharField(required=False, allow_null=True, max_length=20)
    order_amount = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, default=0.00)
    total_weight = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, default=0.00)

