"""
Inventory Alert serializers.
"""
from rest_framework import serializers
from apps.models import InventoryAlert, Product, ProductVariant
from apps.serializers.product import ProductListSerializer, ProductVariantSerializer


class InventoryAlertSerializer(serializers.ModelSerializer):
    """Inventory alert serializer."""
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True, allow_null=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
        source='product'
    )
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
        source='variant'
    )
    current_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryAlert
        fields = [
            'id', 'product', 'product_id', 'variant', 'variant_id',
            'threshold', 'notify_email', 'notify_on_low_stock',
            'notify_on_out_of_stock', 'is_active', 'last_notified_at',
            'current_stock', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'last_notified_at', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get('request'):
            tenant = self.context['request'].user.tenant if hasattr(self.context['request'].user, 'tenant') else None
            if tenant:
                from apps.models import Product, ProductVariant
                self.fields['product_id'].queryset = Product.objects.filter(tenant=tenant, is_deleted=False)
                self.fields['variant_id'].queryset = ProductVariant.objects.filter(product__tenant=tenant, is_deleted=False)
    
    def get_current_stock(self, obj):
        """Mevcut stok miktarı."""
        if obj.variant:
            return obj.variant.inventory_quantity
        elif obj.product:
            return obj.product.inventory_quantity
        return 0
    
    def validate(self, data):
        """Validasyon."""
        product = data.get('product')
        variant = data.get('variant')
        
        if not product and not variant:
            raise serializers.ValidationError({
                'product': 'Ürün veya varyant seçilmelidir.'
            })
        
        if product and variant:
            if variant.product != product:
                raise serializers.ValidationError({
                    'variant': 'Varyant seçilen ürüne ait olmalıdır.'
                })
        
        return data

