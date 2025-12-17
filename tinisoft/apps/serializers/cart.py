"""
Cart serializers.
"""
from rest_framework import serializers
from apps.models import Cart, CartItem
from apps.serializers.product import ProductListSerializer, ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Cart item serializer."""
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    variant_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'variant', 'product_id', 'variant_id',
            'quantity', 'unit_price', 'total_price',
            'created_at',
        ]
        read_only_fields = ['id', 'product', 'variant', 'unit_price', 'total_price', 'created_at']
    
    def create(self, validated_data):
        """Sepet kalemi oluştur."""
        product_id = validated_data.pop('product_id')
        variant_id = validated_data.pop('variant_id', None)
        
        from apps.models import Product, ProductVariant
        
        product = Product.objects.get(id=product_id)
        variant = ProductVariant.objects.get(id=variant_id) if variant_id else None
        
        cart = self.context['cart']
        
        # Aynı ürün/varyant zaten sepette var mı?
        existing_item = CartItem.objects.filter(
            cart=cart,
            product=product,
            variant=variant,
            is_deleted=False
        ).first()
        
        if existing_item:
            # Miktarı artır
            existing_item.quantity += validated_data.get('quantity', 1)
            existing_item.save()
            return existing_item
        
        # Yeni kalem oluştur
        return CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variant,
            **validated_data
        )


class CartSerializer(serializers.ModelSerializer):
    """Cart serializer."""
    items = CartItemSerializer(many=True, read_only=True)
    shipping_method = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = [
            'id', 'customer', 'session_id', 'is_active',
            'subtotal', 'shipping_cost', 'tax_amount', 'discount_amount', 'total',
            'shipping_method', 'currency', 'expires_at',
            'items',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'subtotal', 'shipping_cost', 'tax_amount', 'total']
    
    def get_shipping_method(self, obj):
        """Kargo yöntemini döndür."""
        if obj.shipping_method:
            return {
                'id': str(obj.shipping_method.id),
                'name': obj.shipping_method.name,
                'code': obj.shipping_method.code,
                'price': str(obj.shipping_method.price),
                'free_shipping_threshold': str(obj.shipping_method.free_shipping_threshold) if obj.shipping_method.free_shipping_threshold else None,
            }
        return None


class AddToCartSerializer(serializers.Serializer):
    """Add to cart serializer."""
    product_id = serializers.UUIDField()
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)

