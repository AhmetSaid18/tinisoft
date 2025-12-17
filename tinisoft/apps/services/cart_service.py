"""
Cart service - Business logic for carts.
"""
from django.utils import timezone
from datetime import timedelta
from apps.models import Cart, CartItem, Product, ProductVariant
import logging

logger = logging.getLogger(__name__)


class CartService:
    """Cart business logic."""
    
    @staticmethod
    def get_or_create_cart(tenant, customer=None, session_id=None):
        """
        Sepeti al veya oluştur.
        
        Args:
            tenant: Tenant instance
            customer: User instance (opsiyonel)
            session_id: Session ID (guest checkout için)
        
        Returns:
            Cart: Sepet instance
        """
        if customer:
            # Müşteri sepeti
            cart, created = Cart.objects.get_or_create(
                tenant=tenant,
                customer=customer,
                is_active=True,
                defaults={
                    'expires_at': timezone.now() + timedelta(days=30),
                }
            )
        else:
            # Guest sepeti
            if not session_id:
                raise ValueError("Guest checkout için session_id gereklidir.")
            
            cart, created = Cart.objects.get_or_create(
                tenant=tenant,
                session_id=session_id,
                is_active=True,
                defaults={
                    'expires_at': timezone.now() + timedelta(days=30),
                }
            )
        
        if created:
            logger.info(f"Cart created for tenant {tenant.name}")
        
        return cart
    
    @staticmethod
    def add_to_cart(cart, product_id, variant_id=None, quantity=1):
        """
        Sepete ürün ekle.
        
        Args:
            cart: Cart instance
            product_id: Product UUID
            variant_id: ProductVariant UUID (opsiyonel)
            quantity: Miktar
        
        Returns:
            CartItem: Eklenen veya güncellenen sepet kalemi
        """
        # Ürün kontrolü
        try:
            product = Product.objects.get(id=product_id, tenant=cart.tenant, is_deleted=False)
        except Product.DoesNotExist:
            raise ValueError("Ürün bulunamadı.")
        
        # Varyant kontrolü
        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(
                    id=variant_id,
                    product=product,
                    is_deleted=False
                )
            except ProductVariant.DoesNotExist:
                raise ValueError("Varyant bulunamadı.")
        
        # Stok kontrolü
        if variant:
            if variant.track_inventory and variant.inventory_quantity < quantity:
                raise ValueError(f"Yeterli stok yok. Mevcut stok: {variant.inventory_quantity}")
        else:
            if product.track_inventory and product.inventory_quantity < quantity:
                raise ValueError(f"Yeterli stok yok. Mevcut stok: {product.inventory_quantity}")
        
        # Aynı ürün/varyant zaten sepette var mı?
        existing_item = CartItem.objects.filter(
            cart=cart,
            product=product,
            variant=variant,
            is_deleted=False
        ).first()
        
        if existing_item:
            # Miktarı artır
            new_quantity = existing_item.quantity + quantity
            
            # Stok kontrolü
            if variant:
                if variant.track_inventory and variant.inventory_quantity < new_quantity:
                    raise ValueError(f"Yeterli stok yok. Mevcut stok: {variant.inventory_quantity}")
            else:
                if product.track_inventory and product.inventory_quantity < new_quantity:
                    raise ValueError(f"Yeterli stok yok. Mevcut stok: {product.inventory_quantity}")
            
            existing_item.quantity = new_quantity
            existing_item.save()
            return existing_item
        
        # Yeni kalem oluştur
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variant,
            quantity=quantity,
        )
        
        logger.info(f"Product added to cart: {product.name} (qty: {quantity})")
        return cart_item
    
    @staticmethod
    def update_cart_item_quantity(cart_item, quantity):
        """Sepet kalemi miktarını güncelle."""
        if quantity <= 0:
            cart_item.delete()
            return None
        
        # Stok kontrolü
        if cart_item.variant:
            if cart_item.variant.track_inventory and cart_item.variant.inventory_quantity < quantity:
                raise ValueError(f"Yeterli stok yok. Mevcut stok: {cart_item.variant.inventory_quantity}")
        else:
            if cart_item.product.track_inventory and cart_item.product.inventory_quantity < quantity:
                raise ValueError(f"Yeterli stok yok. Mevcut stok: {cart_item.product.inventory_quantity}")
        
        cart_item.quantity = quantity
        cart_item.save()
        return cart_item
    
    @staticmethod
    def remove_from_cart(cart_item):
        """Sepetten ürün çıkar."""
        cart_item.delete()
        logger.info(f"Product removed from cart: {cart_item.product.name}")
    
    @staticmethod
    def clear_cart(cart):
        """Sepeti temizle."""
        cart.items.all().delete()
        cart.calculate_totals()
        logger.info(f"Cart cleared for tenant {cart.tenant.name}")

