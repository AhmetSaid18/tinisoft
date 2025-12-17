"""
Discount serializers.
"""
from rest_framework import serializers
from apps.models import Coupon, Promotion, Category, Product
from apps.serializers.product import ProductListSerializer, CategorySerializer


class CouponSerializer(serializers.ModelSerializer):
    """Coupon serializer."""
    applicable_categories = CategorySerializer(many=True, read_only=True)
    applicable_products = ProductListSerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.none(),
        write_only=True,
        required=False,
        source='applicable_categories'
    )
    product_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Product.objects.none(),
        write_only=True,
        required=False,
        source='applicable_products'
    )
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'name', 'description',
            'discount_type', 'discount_value', 'max_discount_amount',
            'applicable_to', 'applicable_categories', 'applicable_products',
            'category_ids', 'product_ids', 'applicable_collections',
            'minimum_order_amount', 'usage_limit', 'usage_count',
            'usage_limit_per_customer', 'valid_from', 'valid_until',
            'is_active', 'customer_emails', 'customer_groups',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamic queryset for category_ids and product_ids
        if self.context.get('request'):
            tenant = self.context['request'].user.tenant if hasattr(self.context['request'].user, 'tenant') else None
            if tenant:
                from apps.models import Category, Product
                self.fields['category_ids'].queryset = Category.objects.filter(tenant=tenant, is_deleted=False)
                self.fields['product_ids'].queryset = Product.objects.filter(tenant=tenant, is_deleted=False)


class CouponValidateSerializer(serializers.Serializer):
    """Coupon validation serializer."""
    code = serializers.CharField(required=True, max_length=50)
    order_amount = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, default=0.00)
    customer_email = serializers.EmailField(required=False, allow_null=True)


class PromotionSerializer(serializers.ModelSerializer):
    """Promotion serializer."""
    applicable_products = ProductListSerializer(many=True, read_only=True)
    applicable_categories = CategorySerializer(many=True, read_only=True)
    gift_product = ProductListSerializer(read_only=True)
    product_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Product.objects.none(),
        write_only=True,
        required=False,
        source='applicable_products'
    )
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.none(),
        write_only=True,
        required=False,
        source='applicable_categories'
    )
    gift_product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.none(),
        write_only=True,
        required=False,
        source='gift_product'
    )
    
    class Meta:
        model = Promotion
        fields = [
            'id', 'name', 'description', 'promotion_type',
            'minimum_quantity', 'minimum_order_amount',
            'applicable_products', 'applicable_categories',
            'product_ids', 'category_ids',
            'discount_percentage', 'gift_product', 'gift_product_id',
            'valid_from', 'valid_until', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamic queryset
        if self.context.get('request'):
            tenant = self.context['request'].user.tenant if hasattr(self.context['request'].user, 'tenant') else None
            if tenant:
                from apps.models import Product, Category
                self.fields['product_ids'].queryset = Product.objects.filter(tenant=tenant, is_deleted=False)
                self.fields['category_ids'].queryset = Category.objects.filter(tenant=tenant, is_deleted=False)
                self.fields['gift_product_id'].queryset = Product.objects.filter(tenant=tenant, is_deleted=False)

