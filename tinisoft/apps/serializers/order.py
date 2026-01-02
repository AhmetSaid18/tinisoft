"""
Order serializers.
"""
from rest_framework import serializers
from apps.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Order item serializer."""
    product_name = serializers.CharField(read_only=True)
    variant_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'variant', 'product_name', 'variant_name',
            'product_sku', 'quantity', 'unit_price', 'total_price',
            'product_image_url', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'product_name', 'variant_name']


class OrderListSerializer(serializers.ModelSerializer):
    """Order list serializer (lightweight)."""
    customer_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'customer_email',
            'status', 'status_display', 'payment_status', 'payment_status_display',
            'total', 'currency', 'item_count',
            'created_at', 'shipped_at', 'delivered_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_customer_name(self, obj):
        """Müşteri adını döndür."""
        return f"{obj.customer_first_name} {obj.customer_last_name}"
    
    def get_item_count(self, obj):
        """Sipariş kalem sayısı."""
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Order detail serializer (full)."""
    items = OrderItemSerializer(many=True, read_only=True)
    customer = serializers.SerializerMethodField()
    shipping_address = serializers.SerializerMethodField()
    shipping_method = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number',
            'customer', 'customer_email', 'customer_first_name', 'customer_last_name', 'customer_phone',
            'shipping_address', 'billing_address',
            'status', 'status_display', 'payment_status', 'payment_status_display',
            'subtotal', 'shipping_cost', 'tax_amount', 'discount_amount', 'total', 'currency',
            'shipping_method', 'tracking_number',
            'customer_note', 'admin_note',
            'items',
            'shipped_at', 'delivered_at',
            'ip_address', 'user_agent',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'order_number', 'created_at', 'updated_at']
    
    def get_customer(self, obj):
        """Müşteri bilgisini döndür."""
        if obj.customer:
            return {
                'id': str(obj.customer.id),
                'email': obj.customer.email,
                'first_name': obj.customer.first_name,
                'last_name': obj.customer.last_name,
            }
        return None
    
    def get_shipping_address(self, obj):
        """Kargo adresini döndür."""
        if obj.shipping_address:
            return {
                'id': str(obj.shipping_address.id),
                'first_name': obj.shipping_address.first_name,
                'last_name': obj.shipping_address.last_name,
                'phone': obj.shipping_address.phone,
                'address_line_1': obj.shipping_address.address_line_1,
                'address_line_2': obj.shipping_address.address_line_2,
                'city': obj.shipping_address.city,
                'state': obj.shipping_address.state,
                'postal_code': obj.shipping_address.postal_code,
                'country': obj.shipping_address.country,
            }
        return None
    
    def get_shipping_method(self, obj):
        """Kargo yöntemini döndür."""
        if obj.shipping_method:
            return {
                'id': str(obj.shipping_method.id),
                'name': obj.shipping_method.name,
                'code': obj.shipping_method.code,
            }
        return None


class CreateOrderSerializer(serializers.Serializer):
    """Create order serializer."""
    cart_id = serializers.UUIDField(required=False)
    selected_cart_item_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_null=True,
        help_text="Siparişe eklenecek sepet kalemlerinin ID'leri. Boşsa tüm sepet eklenir."
    )
    customer_email = serializers.EmailField()
    customer_first_name = serializers.CharField(max_length=100)
    customer_last_name = serializers.CharField(max_length=100)
    customer_phone = serializers.CharField(max_length=20, required=False)
    currency = serializers.CharField(max_length=3, required=False, default='TRY')
    shipping_address_id = serializers.UUIDField(required=False, allow_null=True)
    shipping_address = serializers.JSONField(required=False, allow_null=True)  # Direct shipping address data
    shipping_method_id = serializers.UUIDField(required=False, allow_null=True)
    customer_note = serializers.CharField(required=False, allow_blank=True)
    billing_address = serializers.JSONField(required=False, default=dict)
    items = serializers.ListField(required=False, allow_null=True)  # Items array (if provided, will be ignored - cart_id is used instead)

