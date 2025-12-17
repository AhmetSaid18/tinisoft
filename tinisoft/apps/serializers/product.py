"""
Product serializers.
"""
from rest_framework import serializers
from apps.models import (
    Product, Category, ProductImage, ProductOption,
    ProductOptionValue, ProductVariant
)


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer."""
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent',
            'is_active', 'children', 'product_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_children(self, obj):
        """Alt kategorileri döndür."""
        children = obj.children.filter(is_deleted=False, is_active=True)
        return CategorySerializer(children, many=True).data
    
    def get_product_count(self, obj):
        """Kategorideki ürün sayısı."""
        return obj.products.filter(is_deleted=False, status='active').count()


class ProductImageSerializer(serializers.ModelSerializer):
    """Product image serializer."""
    
    class Meta:
        model = ProductImage
        fields = [
            'id', 'image_url', 'alt_text', 'position', 'is_primary',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ProductOptionValueSerializer(serializers.ModelSerializer):
    """Product option value serializer."""
    
    class Meta:
        model = ProductOptionValue
        fields = ['id', 'value', 'position', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductOptionSerializer(serializers.ModelSerializer):
    """Product option serializer."""
    values = ProductOptionValueSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductOption
        fields = ['id', 'name', 'position', 'values', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductVariantSerializer(serializers.ModelSerializer):
    """Product variant serializer."""
    option_values = ProductOptionValueSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'price', 'compare_at_price',
            'track_inventory', 'inventory_quantity',
            'sku', 'barcode', 'option_values', 'is_default',
            'image_url', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Product list serializer (lightweight)."""
    primary_image = serializers.SerializerMethodField()
    category_names = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    max_price = serializers.SerializerMethodField()
    has_variants = serializers.BooleanField(source='is_variant_product', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'compare_at_price',
            'primary_image', 'category_names', 'min_price', 'max_price',
            'has_variants', 'is_featured', 'is_new', 'is_bestseller',
            'status', 'is_visible', 'view_count', 'sale_count',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_primary_image(self, obj):
        """Ana görseli döndür."""
        image = obj.images.filter(is_primary=True, is_deleted=False).first()
        if not image:
            image = obj.images.filter(is_deleted=False).first()
        return image.image_url if image else None
    
    def get_category_names(self, obj):
        """Kategori isimlerini döndür."""
        return [cat.name for cat in obj.categories.filter(is_deleted=False, is_active=True)]
    
    def get_min_price(self, obj):
        """Minimum fiyat (varyant varsa varyantların min fiyatı)."""
        if obj.is_variant_product:
            variants = obj.variants.filter(is_deleted=False)
            if variants.exists():
                return min(v.price for v in variants)
        return obj.price
    
    def get_max_price(self, obj):
        """Maximum fiyat (varyant varsa varyantların max fiyatı)."""
        if obj.is_variant_product:
            variants = obj.variants.filter(is_deleted=False)
            if variants.exists():
                return max(v.price for v in variants)
        return obj.price


class ProductDetailSerializer(serializers.ModelSerializer):
    """Product detail serializer (full)."""
    images = ProductImageSerializer(many=True, read_only=True)
    options = ProductOptionSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        write_only=True,
        required=False,
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'price', 'compare_at_price',
            'sku', 'barcode',
            'track_inventory', 'inventory_quantity',
            'is_variant_product',
            'status', 'is_visible',
            'meta_title', 'meta_description', 'meta_keywords',
            'tags', 'collections',
            'weight', 'length', 'width', 'height',
            'is_featured', 'is_new', 'is_bestseller',
            'sort_order',
            'available_from', 'available_until',
            'view_count', 'sale_count',
            'images', 'options', 'variants', 'categories',
            'category_ids',
            'metadata',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'view_count', 'sale_count']
    
    def create(self, validated_data):
        """Ürün oluştur."""
        category_ids = validated_data.pop('category_ids', [])
        product = Product.objects.create(**validated_data)
        if category_ids:
            product.categories.set(category_ids)
        return product
    
    def update(self, instance, validated_data):
        """Ürün güncelle."""
        category_ids = validated_data.pop('category_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if category_ids is not None:
            instance.categories.set(category_ids)
        return instance

