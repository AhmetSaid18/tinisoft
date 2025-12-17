"""
Bundle serializers.
"""
from rest_framework import serializers
from apps.models import ProductBundle, ProductBundleItem, Product, ProductVariant
from apps.serializers.product import ProductListSerializer, ProductVariantSerializer


class ProductBundleItemSerializer(serializers.ModelSerializer):
    """Product bundle item serializer."""
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True, allow_null=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.none(),
        write_only=True,
        required=False,
        source='product'
    )
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
        source='variant'
    )
    
    class Meta:
        model = ProductBundleItem
        fields = [
            'id', 'product', 'product_id', 'variant', 'variant_id',
            'quantity', 'position', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'product', 'variant', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get('request'):
            tenant = self.context['request'].user.tenant if hasattr(self.context['request'].user, 'tenant') else None
            if tenant:
                self.fields['product_id'].queryset = Product.objects.filter(tenant=tenant, is_deleted=False)
                self.fields['variant_id'].queryset = ProductVariant.objects.filter(product__tenant=tenant, is_deleted=False)


class ProductBundleSerializer(serializers.ModelSerializer):
    """Product bundle serializer."""
    main_product = ProductListSerializer(read_only=True)
    items = ProductBundleItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductBundle
        fields = [
            'id', 'name', 'slug', 'description', 'main_product',
            'bundle_price', 'discount_percentage', 'total_price', 'discount_amount',
            'is_active', 'sort_order', 'items',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_price(self, obj):
        """Bireysel ürün fiyatlarının toplamı."""
        return str(obj.calculate_total_price())
    
    def get_discount_amount(self, obj):
        """İndirim tutarı."""
        return str(obj.calculate_discount())


class ProductBundleCreateSerializer(serializers.ModelSerializer):
    """Product bundle create serializer."""
    main_product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.none(),
        write_only=True,
        required=False,
        source='main_product'
    )
    
    class Meta:
        model = ProductBundle
        fields = [
            'name', 'slug', 'description', 'main_product_id',
            'bundle_price', 'discount_percentage',
            'is_active', 'sort_order',
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get('request'):
            tenant = self.context['request'].user.tenant if hasattr(self.context['request'].user, 'tenant') else None
            if tenant:
                self.fields['main_product_id'].queryset = Product.objects.filter(tenant=tenant, is_deleted=False)
    
    def validate_slug(self, value):
        """Slug unique kontrolü."""
        tenant = self.context['request'].user.tenant if hasattr(self.context['request'].user, 'tenant') else None
        if tenant:
            if self.instance:
                if ProductBundle.objects.filter(tenant=tenant, slug=value, is_deleted=False).exclude(pk=self.instance.pk).exists():
                    raise serializers.ValidationError("Bu slug zaten kullanılıyor.")
            else:
                if ProductBundle.objects.filter(tenant=tenant, slug=value, is_deleted=False).exists():
                    raise serializers.ValidationError("Bu slug zaten kullanılıyor.")
        return value


class ProductBundleItemCreateSerializer(serializers.ModelSerializer):
    """Product bundle item create serializer."""
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.none(),
        write_only=True,
        required=False,
        source='product'
    )
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
        source='variant'
    )
    
    class Meta:
        model = ProductBundleItem
        fields = ['product_id', 'variant_id', 'quantity', 'position']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get('request'):
            tenant = self.context['request'].user.tenant if hasattr(self.context['request'].user, 'tenant') else None
            if tenant:
                self.fields['product_id'].queryset = Product.objects.filter(tenant=tenant, is_deleted=False)
                self.fields['variant_id'].queryset = ProductVariant.objects.filter(product__tenant=tenant, is_deleted=False)

