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
        request=None,
        selected_cart_item_ids=None,
    ):
        """
        Sepetten sipariş oluştur.
        
        Args:
            cart: Cart instance
            selected_cart_item_ids: Seçili sepet kalemlerinin ID'leri (liste). 
                                   None veya boşsa tüm sepet eklenir.
        
        Returns:
            Order: Oluşturulan sipariş
        """
        # Sepet kontrolü - sepet boş mu?
        all_cart_items = cart.items.filter(is_deleted=False)
        if not all_cart_items.exists():
            raise ValueError("Sepet boş.")
        
        # Seçili item'ları filtrele
        if selected_cart_item_ids:
            cart_items = all_cart_items.filter(id__in=selected_cart_item_ids)
            if not cart_items.exists():
                raise ValueError("Seçili sepet kalemleri bulunamadı.")
        else:
            # Seçim yapılmamışsa tüm sepet
            cart_items = all_cart_items
        
        # Seçili item'lara göre toplamları hesapla
        selected_subtotal = sum(item.total_price for item in cart_items)
        
        # Kargo ücreti hesaplama
        selected_shipping_cost = Decimal('0.00')
        if shipping_method:
            if shipping_method.free_shipping_threshold:
                if selected_subtotal >= shipping_method.free_shipping_threshold:
                    selected_shipping_cost = Decimal('0.00')
                else:
                    selected_shipping_cost = shipping_method.price
            else:
                selected_shipping_cost = shipping_method.price
        
        # Vergi hesaplama (Dinamik - Tenant bazlı)
        from apps.models import Tax
        active_tax = Tax.objects.filter(
            tenant=cart.tenant,
            is_active=True,
            is_deleted=False
        ).order_by('-is_default', '-created_at').first()
        
        tax_rate = active_tax.rate if active_tax else Decimal('0.00')
        selected_tax_amount = selected_subtotal * (tax_rate / Decimal('100'))
        
        # Kupon indirimi hesapla (seçili item'lara göre)
        selected_discount_amount = Decimal('0.00')
        if cart.coupon:
            try:
                selected_discount_amount = cart.coupon.calculate_discount(selected_subtotal)
                # Ücretsiz kargo kontrolü
                if cart.coupon.discount_type == cart.coupon.DiscountType.FREE_SHIPPING:
                    selected_shipping_cost = Decimal('0.00')
            except:
                pass
        
        # Toplam
        selected_total = (
            selected_subtotal +
            selected_shipping_cost +
            selected_tax_amount -
            selected_discount_amount
        )
        
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
            subtotal=selected_subtotal,
            shipping_cost=selected_shipping_cost,
            tax_amount=selected_tax_amount,
            discount_amount=selected_discount_amount,
            total=selected_total,
            currency=cart.currency,
            coupon=cart.coupon,
            coupon_code=cart.coupon_code,
            coupon_discount=selected_discount_amount,
            ip_address=request.META.get('REMOTE_ADDR') if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
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
            
            # Stok düşür (gerçek stok önce, sonra sanal stok)
            if cart_item.variant:
                if cart_item.variant.track_inventory:
                    previous_qty = cart_item.variant.inventory_quantity
                    order_quantity = cart_item.quantity
                    
                    # Önce gerçek stoktan düş
                    if cart_item.variant.inventory_quantity >= order_quantity:
                        # Gerçek stok yeterli
                        cart_item.variant.inventory_quantity -= order_quantity
                        real_stock_used = order_quantity
                        virtual_stock_used = 0
                    else:
                        # Gerçek stok yetmiyor, sanal stoktan düş
                        real_stock_used = cart_item.variant.inventory_quantity
                        remaining_qty = order_quantity - real_stock_used
                        cart_item.variant.inventory_quantity = 0
                        
                        # Sanal stok varsa düş
                        if cart_item.variant.allow_backorder:
                            if cart_item.variant.virtual_stock_quantity is not None:
                                # Limitli sanal stok varsa düş
                                virtual_stock_used = min(remaining_qty, cart_item.variant.virtual_stock_quantity)
                                cart_item.variant.virtual_stock_quantity -= virtual_stock_used
                            else:
                                # Sınırsız sanal stok
                                virtual_stock_used = remaining_qty
                        else:
                            virtual_stock_used = 0
                    
                    cart_item.variant.save()
                    
                    # Stok hareketi kaydet
                    InventoryMovement.objects.create(
                        tenant=cart.tenant,
                        product=cart_item.product,
                        variant=cart_item.variant,
                        movement_type=InventoryMovement.MovementType.OUT,
                        quantity=order_quantity,
                        previous_quantity=previous_qty,
                        new_quantity=cart_item.variant.inventory_quantity,
                        order=order,
                        order_item=order_item,
                        reason=f'Sipariş (Gerçek: {real_stock_used}, Sanal: {virtual_stock_used})',
                        created_by=customer_user,
                    )
            else:
                if cart_item.product.track_inventory:
                    previous_qty = cart_item.product.inventory_quantity
                    order_quantity = cart_item.quantity
                    
                    # Önce gerçek stoktan düş
                    if cart_item.product.inventory_quantity >= order_quantity:
                        # Gerçek stok yeterli
                        cart_item.product.inventory_quantity -= order_quantity
                        real_stock_used = order_quantity
                        virtual_stock_used = 0
                    else:
                        # Gerçek stok yetmiyor, sanal stoktan düş
                        real_stock_used = cart_item.product.inventory_quantity
                        remaining_qty = order_quantity - real_stock_used
                        cart_item.product.inventory_quantity = 0
                        
                        # Sanal stok varsa düş
                        if cart_item.product.allow_backorder:
                            if cart_item.product.virtual_stock_quantity is not None:
                                # Limitli sanal stok varsa düş
                                virtual_stock_used = min(remaining_qty, cart_item.product.virtual_stock_quantity)
                                cart_item.product.virtual_stock_quantity -= virtual_stock_used
                            else:
                                # Sınırsız sanal stok
                                virtual_stock_used = remaining_qty
                        else:
                            virtual_stock_used = 0
                    
                    cart_item.product.save()
                    
                    # Stok hareketi kaydet
                    InventoryMovement.objects.create(
                        tenant=cart.tenant,
                        product=cart_item.product,
                        variant=None,
                        movement_type=InventoryMovement.MovementType.OUT,
                        quantity=order_quantity,
                        previous_quantity=previous_qty,
                        new_quantity=cart_item.product.inventory_quantity,
                        order=order,
                        order_item=order_item,
                        reason=f'Sipariş (Gerçek: {real_stock_used}, Sanal: {virtual_stock_used})',
                        created_by=customer_user,
                    )
        
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

