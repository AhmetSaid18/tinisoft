from rest_framework import serializers
from apps.models import Product, ProductImage, Category, ProductVariant, ProductOption
from apps.services.currency_service import CurrencyService

class StorefrontImageSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source='image_url')
    altText = serializers.CharField(source='alt_text', allow_blank=True)

    class Meta:
        model = ProductImage
        fields = ['url', 'altText', 'width', 'height']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Default dimensions if not present (logic can be improved)
        if 'width' not in data or not data['width']:
            data['width'] = 800
        if 'height' not in data or not data['height']:
            data['height'] = 800
        return data


class StorefrontCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class StorefrontVariantOptionSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = serializers.CharField()


class StorefrontVariantSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='name', allow_blank=True)
    inventoryQuantity = serializers.IntegerField(source='inventory_quantity')
    options = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'title', 'price', 'sku', 'inventoryQuantity', 'options']

    def get_options(self, obj):
        # Return list of {name: "Size", value: "S"}
        return [
            {'name': ov.option.name, 'value': ov.value}
            for ov in obj.option_values.all()
        ]


class StorefrontOptionSerializer(serializers.ModelSerializer):
    values = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='value'
    )

    class Meta:
        model = ProductOption
        fields = ['name', 'values']


class ProductStorefrontListSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='name')
    compareAtPrice = serializers.DecimalField(source='compare_at_price', max_digits=10, decimal_places=2)
    images = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'price', 'compareAtPrice', 'currency',
            'images', 'category'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Karşılaştırma fiyatı gizleme: ürün bazlı VEYA tenant global toggle
        if not instance.show_compare_at_price or not instance.tenant.show_compare_at_price:
            data['compareAtPrice'] = None
        return data

    def get_images(self, obj):
        images = obj.images.filter(is_deleted=False).order_by('position', 'created_at')
        return StorefrontImageSerializer(images, many=True).data

    def get_category(self, obj):
        first_cat = obj.categories.filter(is_deleted=False, is_active=True).first()
        if first_cat:
            return StorefrontCategorySerializer(first_cat).data
        return None


class ProductStorefrontDetailSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='name')
    shortDescription = serializers.CharField(source='description', allow_blank=True) # Assuming description is short
    sKU = serializers.CharField(source='sku')
    compareAtPrice = serializers.DecimalField(source='compare_at_price', max_digits=10, decimal_places=2)
    inventoryQuantity = serializers.IntegerField(source='inventory_quantity')
    allowBackorder = serializers.BooleanField(source='allow_backorder')
    requiresShipping = serializers.BooleanField(source='is_visible') # Placeholder logic? Usually strictly DB field
    isDigital = serializers.BooleanField(default=False) # Placeholder
    metaTitle = serializers.CharField(source='meta_title', allow_blank=True)
    vendor = serializers.CharField(source='brand', allow_blank=True)
    productType = serializers.SerializerMethodField()
    
    images = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'description_html', 'shortDescription', 'slug', 'sKU',
            'price', 'compareAtPrice', 'currency', 'inventoryQuantity',
            'allowBackorder', 'weight', 'requiresShipping', 'isDigital',
            'metaTitle', 'vendor', 'productType',
            'images', 'categories', 'variants', 'options', 'tags', 'created_at'
        ]
        extra_kwargs = {
            'created_at': {'source': 'createdAt'} # This mapping needs to be handled in to_representation or field rename
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['createdAt'] = instance.created_at
        # Karşılaştırma fiyatı gizleme: ürün bazlı VEYA tenant global toggle
        if not instance.show_compare_at_price or not instance.tenant.show_compare_at_price:
            data['compareAtPrice'] = None
        return data

    def get_images(self, obj):
        images = obj.images.filter(is_deleted=False).order_by('position', 'created_at')
        return StorefrontImageSerializer(images, many=True).data

    def get_categories(self, obj):
        cats = obj.categories.filter(is_deleted=False, is_active=True)
        return StorefrontCategorySerializer(cats, many=True).data

    def get_variants(self, obj):
        if not obj.is_variant_product:
            return []
        vars = obj.variants.filter(is_deleted=False)
        return StorefrontVariantSerializer(vars, many=True).data

    def get_options(self, obj):
        opts = obj.options.all()
        return StorefrontOptionSerializer(opts, many=True).data
    
    def get_tags(self, obj):
        # obj.tags is ArrayField or list
        return obj.tags if obj.tags else []

    def get_productType(self, obj):
        # Assuming first category name as type for now
        cat = obj.categories.filter(is_deleted=False).first()
        return cat.name if cat else "General"
