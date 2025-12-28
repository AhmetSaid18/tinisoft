"""
Cart serializers.
"""
from rest_framework import serializers
from apps.models import Cart, CartItem
from apps.serializers.product import ProductListSerializer, ProductVariantSerializer
import logging

logger = logging.getLogger(__name__)


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


class CartSerializer(serializers.Serializer):
    """Cart serializer - DB ve Redis sepetlerini destekler."""
    id = serializers.CharField(read_only=True)
    customer_id = serializers.UUIDField(read_only=True, allow_null=True)
    session_id = serializers.CharField(read_only=True, allow_null=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    shipping_method = serializers.SerializerMethodField()
    currency = serializers.CharField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True, allow_null=True)
    items = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def get_items(self, obj):
        """Sepet kalemlerini döndür."""
        is_redis_cart = isinstance(obj, dict)
        
        if is_redis_cart:
            # Redis sepeti - dict'lerden oluştur
            items = obj.get('items', [])
            result = []
            for item in items:
                # Ürün bilgilerini DB'den çek
                try:
                    from apps.models import Product, ProductVariant
                    product = Product.objects.get(id=item.get('product_id'), is_deleted=False)
                    variant = None
                    if item.get('variant_id'):
                        variant = ProductVariant.objects.get(id=item.get('variant_id'), is_deleted=False)
                    
                    result.append({
                        'id': item.get('id'),
                        'product': ProductListSerializer(product, context=self.context).data,
                        'variant': ProductVariantSerializer(variant, context=self.context).data if variant else None,
                        'quantity': item.get('quantity'),
                        'unit_price': item.get('unit_price'),
                        'total_price': item.get('total_price'),
                        'created_at': obj.get('created_at'),
                    })
                except Exception as e:
                    logger.warning(f"Error serializing cart item: {e}")
                    # Hata durumunda basit format
                    result.append({
                        'id': item.get('id'),
                        'product': {'id': item.get('product_id'), 'name': item.get('product_name')},
                        'variant': {'id': item.get('variant_id'), 'name': item.get('variant_name')} if item.get('variant_id') else None,
                        'quantity': item.get('quantity'),
                        'unit_price': item.get('unit_price'),
                        'total_price': item.get('total_price'),
                        'created_at': obj.get('created_at'),
                    })
            return result
        else:
            # DB sepeti - normal serializer
            return CartItemSerializer(obj.items.filter(is_deleted=False), many=True, context=self.context).data
    
    def get_shipping_method(self, obj):
        """Kargo yöntemini döndür."""
        is_redis_cart = isinstance(obj, dict)
        
        if is_redis_cart:
            shipping_method_id = obj.get('shipping_method_id')
            if not shipping_method_id:
                return None
            
            try:
                from apps.models import ShippingMethod
                shipping_method = ShippingMethod.objects.get(id=shipping_method_id, is_deleted=False)
                return {
                    'id': str(shipping_method.id),
                    'name': shipping_method.name,
                    'code': shipping_method.code,
                    'price': str(shipping_method.price),
                    'free_shipping_threshold': str(shipping_method.free_shipping_threshold) if shipping_method.free_shipping_threshold else None,
                }
            except Exception:
                return None
        else:
            if obj.shipping_method:
                return {
                    'id': str(obj.shipping_method.id),
                    'name': obj.shipping_method.name,
                    'code': obj.shipping_method.code,
                    'price': str(obj.shipping_method.price),
                    'free_shipping_threshold': str(obj.shipping_method.free_shipping_threshold) if obj.shipping_method.free_shipping_threshold else None,
                }
            return None
    
    def to_representation(self, instance):
        """DB veya Redis sepetini serialize et."""
        is_redis_cart = isinstance(instance, dict)
        
        if is_redis_cart:
            # Redis sepeti
            return {
                'id': instance.get('id'),
                'customer_id': instance.get('customer_id'),
                'session_id': instance.get('session_id'),
                'subtotal': instance.get('subtotal', '0.00'),
                'shipping_cost': instance.get('shipping_cost', '0.00'),
                'tax_amount': instance.get('tax_amount', '0.00'),
                'discount_amount': instance.get('discount_amount', '0.00'),
                'total': instance.get('total', '0.00'),
                'shipping_method': self.get_shipping_method(instance),
                'currency': instance.get('currency', 'TRY'),
                'expires_at': instance.get('expires_at'),
                'items': self.get_items(instance),
                'created_at': instance.get('created_at'),
                'updated_at': instance.get('updated_at'),
            }
        else:
            # DB sepeti
            return {
                'id': str(instance.id),
                'customer_id': str(instance.customer.id) if instance.customer else None,
                'session_id': instance.session_id,
                'subtotal': str(instance.subtotal),
                'shipping_cost': str(instance.shipping_cost),
                'tax_amount': str(instance.tax_amount),
                'discount_amount': str(instance.discount_amount),
                'total': str(instance.total),
                'shipping_method': self.get_shipping_method(instance),
                'currency': instance.currency,
                'expires_at': instance.expires_at.isoformat() if instance.expires_at else None,
                'items': self.get_items(instance),
                'created_at': instance.created_at.isoformat() if instance.created_at else None,
                'updated_at': instance.updated_at.isoformat() if instance.updated_at else None,
            }


class AddToCartSerializer(serializers.Serializer):
    """Add to cart serializer."""
    product_id = serializers.UUIDField()
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)

