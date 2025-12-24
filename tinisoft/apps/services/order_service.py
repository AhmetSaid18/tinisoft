"""
Order service - Business logic for orders.
"""
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import uuid
import logging
from apps.models import Order, OrderItem, Cart, CartItem, InventoryMovement

logger = logging.getLogger(__name__)


class OrderService:
    """Order business logic."""
    
    @staticmethod
    def generate_order_number(tenant):
        """Benzersiz sipariş numarası oluştur."""
        # Format: ORD-{tenant_slug}-{timestamp}-{random}
        timestamp = int(timezone.now().timestamp())
        random_part = str(uuid.uuid4())[:8].upper()
        return f"ORD-{tenant.slug.upper()}-{timestamp}-{random_part}"
    
    @staticmethod
    @transaction.atomic
    def create_order_from_cart(
        cart,
        customer_email,
        customer_first_name,
        customer_last_name,
        customer_phone=None,
        shipping_address=None,
        shipping_method=None,
        customer_note='',
        billing_address=None,
        customer_user=None,
    ):
        """
        Sepetten sipariş oluştur.
        
        Returns:
            Order: Oluşturulan sipariş
        """
        # Sepet kontrolü
        if not cart.is_active:
            raise ValueError("Sepet aktif değil.")
        
        cart_items = cart.items.filter(is_deleted=False)
        if not cart_items.exists():
            raise ValueError("Sepet boş.")
        
        # Sipariş numarası oluştur
        order_number = OrderService.generate_order_number(cart.tenant)
        
        # Sipariş oluştur
        order = Order.objects.create(
            tenant=cart.tenant,
            order_number=order_number,
            customer=customer_user,
            customer_email=customer_email,
            customer_first_name=customer_first_name,
            customer_last_name=customer_last_name,
            customer_phone=customer_phone or '',
            shipping_address=shipping_address,
            shipping_method=shipping_method,
            customer_note=customer_note,
            billing_address=billing_address or {},
            subtotal=cart.subtotal,
            shipping_cost=cart.shipping_cost,
            tax_amount=cart.tax_amount,
            discount_amount=cart.discount_amount,
            total=cart.total,
            currency=cart.currency,
            ip_address=cart.tenant.__dict__.get('ip_address'),  # TODO: request'ten al
            user_agent=cart.tenant.__dict__.get('user_agent'),  # TODO: request'ten al
        )
        
        # Sipariş kalemlerini oluştur
        for cart_item in cart_items:
            # Ürün bilgilerini snapshot olarak kaydet
            product_name = cart_item.product.name
            variant_name = cart_item.variant.name if cart_item.variant else ''
            product_sku = cart_item.variant.sku if cart_item.variant else cart_item.product.sku
            product_image_url = ''
            
            # Ana görseli al
            primary_image = cart_item.product.images.filter(is_primary=True, is_deleted=False).first()
            if not primary_image:
                primary_image = cart_item.product.images.filter(is_deleted=False).first()
            if primary_image:
                product_image_url = primary_image.image_url
            
            # Varyant görseli varsa onu kullan
            if cart_item.variant and cart_item.variant.image_url:
                product_image_url = cart_item.variant.image_url
            
            order_item = OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                product_name=product_name,
                variant_name=variant_name,
                product_sku=product_sku,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                total_price=cart_item.total_price,
                product_image_url=product_image_url,
            )
            
            # Stok düşür
            if cart_item.variant:
                if cart_item.variant.track_inventory:
                    previous_qty = cart_item.variant.inventory_quantity
                    cart_item.variant.inventory_quantity -= cart_item.quantity
                    cart_item.variant.save()
                    
                    # Stok hareketi kaydet
                    InventoryMovement.objects.create(
                        tenant=cart.tenant,
                        product=cart_item.product,
                        variant=cart_item.variant,
                        movement_type=InventoryMovement.MovementType.OUT,
                        quantity=cart_item.quantity,
                        previous_quantity=previous_qty,
                        new_quantity=cart_item.variant.inventory_quantity,
                        order=order,
                        order_item=order_item,
                        reason='Sipariş',
                        created_by=customer_user,
                    )
            else:
                if cart_item.product.track_inventory:
                    previous_qty = cart_item.product.inventory_quantity
                    cart_item.product.inventory_quantity -= cart_item.quantity
                    cart_item.product.save()
                    
                    # Stok hareketi kaydet
                    InventoryMovement.objects.create(
                        tenant=cart.tenant,
                        product=cart_item.product,
                        variant=None,
                        movement_type=InventoryMovement.MovementType.OUT,
                        quantity=cart_item.quantity,
                        previous_quantity=previous_qty,
                        new_quantity=cart_item.product.inventory_quantity,
                        order=order,
                        order_item=order_item,
                        reason='Sipariş',
                        created_by=customer_user,
                    )
        
        # Sepeti pasif yap
        cart.is_active = False
        cart.save()
        
        # Müşteri istatistiklerini güncelle
        if customer_user:
            try:
                customer_profile = customer_user.customer_profile
                customer_profile.update_statistics()
            except:
                pass  # Customer profile yoksa skip
        
        logger.info(f"Order created: {order_number} for tenant {cart.tenant.name}")
        return order
    
    @staticmethod
    @transaction.atomic
    def apply_loyalty_points(order, points_to_use):
        """
        Siparişe sadakat puanı uygula.
        
        Args:
            order: Order instance
            points_to_use: Kullanılacak puan miktarı
        
        Returns:
            dict: Sonuç bilgisi
        """
        from apps.services.loyalty_service import LoyaltyService
        
        result = LoyaltyService.use_points_for_order(order, points_to_use)
        
        if result['success']:
            # Sipariş indirimini güncelle
            order.discount_amount += result['discount_amount']
            order.calculate_total()
            order.save()
        
        return result
    
    @staticmethod
    def update_order_status(order, new_status, admin_user=None):
        """Sipariş durumunu güncelle."""
        from apps.services.email_service import EmailService
        
        old_status = order.status
        order.status = new_status
        
        # Durum değişikliklerine göre tarihleri güncelle
        if new_status == Order.OrderStatus.SHIPPED and not order.shipped_at:
            order.shipped_at = timezone.now()
        elif new_status == Order.OrderStatus.DELIVERED and not order.delivered_at:
            order.delivered_at = timezone.now()
        
        order.save()
        
        logger.info(f"Order {order.order_number} status changed: {old_status} -> {new_status}")
        
        # Email gönder (asenkron olarak)
        try:
            if new_status == Order.OrderStatus.CONFIRMED:
                EmailService.send_order_confirmation_email(order.tenant, order)
            elif new_status == Order.OrderStatus.SHIPPED:
                EmailService.send_order_shipped_email(order.tenant, order)
            elif new_status == Order.OrderStatus.DELIVERED:
                EmailService.send_order_delivered_email(order.tenant, order)
            elif new_status == Order.OrderStatus.CANCELLED:
                EmailService.send_order_cancelled_email(order.tenant, order)
        except Exception as e:
            logger.error(f"Email send error for order {order.order_number}: {str(e)}")
            # Email hatası sipariş güncellemesini engellemez
        
        return order
    
    @staticmethod
    def update_payment_status(order, new_status):
        """Ödeme durumunu güncelle."""
        old_status = order.payment_status
        order.payment_status = new_status
        order.save()
        
        # Ödeme tamamlandığında sadakat puanı kazandır
        if new_status == Order.PaymentStatus.PAID and old_status != Order.PaymentStatus.PAID:
            from apps.services.loyalty_service import LoyaltyService
            try:
                LoyaltyService.award_points_for_order(order)
            except Exception as e:
                logger.error(f"Error awarding loyalty points: {e}")
        
        # İade durumunda puanları geri al
        if new_status == Order.PaymentStatus.REFUNDED:
            from apps.services.loyalty_service import LoyaltyService
            try:
                LoyaltyService.refund_points_for_order(order)
            except Exception as e:
                logger.error(f"Error refunding loyalty points: {e}")
        
        logger.info(f"Order {order.order_number} payment status changed: {old_status} -> {new_status}")
        return order

