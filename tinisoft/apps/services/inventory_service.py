"""
Inventory service - Business logic for inventory.
"""
from django.db import transaction
from apps.models import InventoryMovement, Product, ProductVariant
import logging

logger = logging.getLogger(__name__)


class InventoryService:
    """Inventory business logic."""
    
    @staticmethod
    @transaction.atomic
    def adjust_inventory(
        tenant,
        product_id=None,
        variant_id=None,
        movement_type=InventoryMovement.MovementType.ADJUSTMENT,
        quantity=0,
        reason='',
        notes='',
        created_by=None,
    ):
        """
        Stok düzeltmesi yap.
        
        Args:
            tenant: Tenant instance
            product_id: Product UUID (basit ürün için)
            variant_id: ProductVariant UUID (varyantlı ürün için)
            movement_type: Hareket tipi
            quantity: Miktar (pozitif değer)
            reason: Neden
            notes: Notlar
            created_by: User instance
        
        Returns:
            InventoryMovement: Oluşturulan stok hareketi
        """
        if not product_id and not variant_id:
            raise ValueError("product_id veya variant_id gereklidir.")
        
        product = None
        variant = None
        previous_quantity = 0
        
        if variant_id:
            variant = ProductVariant.objects.get(id=variant_id, product__tenant=tenant)
            product = variant.product
            previous_quantity = variant.inventory_quantity
            
            # Stok güncelle
            if movement_type == InventoryMovement.MovementType.IN:
                variant.inventory_quantity += quantity
            elif movement_type == InventoryMovement.MovementType.OUT:
                variant.inventory_quantity -= quantity
            elif movement_type == InventoryMovement.MovementType.ADJUSTMENT:
                variant.inventory_quantity = quantity
            
            variant.save()
            new_quantity = variant.inventory_quantity
        else:
            product = Product.objects.get(id=product_id, tenant=tenant)
            previous_quantity = product.inventory_quantity
            
            # Stok güncelle
            if movement_type == InventoryMovement.MovementType.IN:
                product.inventory_quantity += quantity
            elif movement_type == InventoryMovement.MovementType.OUT:
                product.inventory_quantity -= quantity
            elif movement_type == InventoryMovement.MovementType.ADJUSTMENT:
                product.inventory_quantity = quantity
            
            product.save()
            new_quantity = product.inventory_quantity
        
        # Stok hareketi kaydet
        movement = InventoryMovement.objects.create(
            tenant=tenant,
            product=product,
            variant=variant,
            movement_type=movement_type,
            quantity=quantity,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            reason=reason,
            notes=notes,
            created_by=created_by,
        )
        
        logger.info(
            f"Inventory adjusted: {product.name} "
            f"({previous_quantity} -> {new_quantity}) - {movement_type}"
        )
        return movement

