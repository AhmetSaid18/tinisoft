"""
Wishlist serializers.
"""
from rest_framework import serializers
from apps.models import Wishlist, WishlistItem
from apps.serializers.product import ProductListSerializer, ProductVariantSerializer


class WishlistItemSerializer(serializers.ModelSerializer):
    """Wishlist item serializer."""
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    
    class Meta:
        model = WishlistItem
        fields = [
            'id', 'wishlist', 'product', 'variant', 'note',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'wishlist', 'created_at', 'updated_at']


class WishlistSerializer(serializers.ModelSerializer):
    """Wishlist serializer."""
    items = WishlistItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Wishlist
        fields = [
            'id', 'customer', 'name', 'is_default', 'is_public',
            'items', 'item_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'customer', 'created_at', 'updated_at']
    
    def get_item_count(self, obj):
        """Wishlist'teki ürün sayısı."""
        return obj.items.filter(is_deleted=False).count()


class WishlistCreateSerializer(serializers.ModelSerializer):
    """Wishlist create serializer."""
    
    class Meta:
        model = Wishlist
        fields = ['name', 'is_default', 'is_public']


class WishlistItemCreateSerializer(serializers.Serializer):
    """Wishlist item create serializer."""
    product_id = serializers.UUIDField(required=True)
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True, max_length=1000)

