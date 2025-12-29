"""
Product comparison serializers.
"""
from rest_framework import serializers
from apps.models import ProductCompare, CompareItem, Product


class CompareItemSerializer(serializers.ModelSerializer):
    """Compare item serializer."""
    product = serializers.SerializerMethodField()
    
    class Meta:
        model = CompareItem
        fields = [
            'id', 'product', 'position', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_product(self, obj):
        """Product bilgilerini getir."""
        from apps.serializers.product import ProductListSerializer
        return ProductListSerializer(obj.product, context=self.context).data


class ProductCompareSerializer(serializers.ModelSerializer):
    """Product compare serializer."""
    items = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductCompare
        fields = [
            'id', 'max_items', 'items', 'items_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_items(self, obj):
        """Aktif item'ları getir."""
        items = obj.items.filter(is_deleted=False).order_by('position', 'created_at')
        return CompareItemSerializer(items, many=True, context=self.context).data
    
    def get_items_count(self, obj):
        """Aktif item sayısı."""
        return obj.items.filter(is_deleted=False).count()


class CompareItemCreateSerializer(serializers.Serializer):
    """Compare item create serializer."""
    product_id = serializers.UUIDField(required=True)

