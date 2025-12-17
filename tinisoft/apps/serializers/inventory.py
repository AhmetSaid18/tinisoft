"""
Inventory serializers.
"""
from rest_framework import serializers
from apps.models import InventoryMovement


class InventoryMovementSerializer(serializers.ModelSerializer):
    """Inventory movement serializer."""
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)
    product_name = serializers.SerializerMethodField()
    variant_name = serializers.SerializerMethodField()
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = InventoryMovement
        fields = [
            'id', 'movement_type', 'movement_type_display',
            'product', 'product_name', 'variant', 'variant_name',
            'quantity', 'previous_quantity', 'new_quantity',
            'order', 'order_number', 'order_item',
            'reason', 'notes',
            'created_by', 'created_by_email',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'product_name', 'variant_name', 'order_number', 'created_by_email']
    
    def get_product_name(self, obj):
        """Ürün adını döndür."""
        if obj.product:
            return obj.product.name
        return None
    
    def get_variant_name(self, obj):
        """Varyant adını döndür."""
        if obj.variant:
            return obj.variant.name
        return None


class CreateInventoryMovementSerializer(serializers.Serializer):
    """Create inventory movement serializer."""
    product_id = serializers.UUIDField(required=False, allow_null=True)
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    movement_type = serializers.ChoiceField(choices=InventoryMovement.MovementType.choices)
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    order_id = serializers.UUIDField(required=False, allow_null=True)

