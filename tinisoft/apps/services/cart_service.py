"""
Cart service - Business logic for carts.
Guest sepetleri Redis'te, kayıtlı kullanıcı sepetleri DB'de tutulur.
"""
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json
import uuid
from django.core.cache import cache
from apps.models import Cart, CartItem, Product, ProductVariant
from apps.services.cache_service import CacheService
from apps.services.currency_service import CurrencyService
import logging

logger = logging.getLogger(__name__)


class CartService:
    """Cart business logic."""
    
    # Redis cart timeout (30 gün)
    CART_TIMEOUT = 60 * 60 * 24 * 30  # 30 gün (saniye)
    
    @staticmethod
    def _get_redis_cart_key(tenant_id, session_id):
        """Redis cart key oluştur."""
        return f"cart:{tenant_id}:{session_id}"
    
    @staticmethod
    def _get_redis_cart(tenant_id, session_id):
        """Redis'ten guest sepeti al."""
        cache_key = CartService._get_redis_cart_key(tenant_id, session_id)
        cart_data = cache.get(cache_key)
        if cart_data:
            try:
                if isinstance(cart_data, str):
                    return json.loads(cart_data)
                return cart_data
            except (json.JSONDecodeError, TypeError):
                logger.error(f"Error parsing cart data from Redis: {cache_key}")
                return None
        return None
    
    @staticmethod
    def _save_redis_cart(tenant_id, session_id, cart_data, timeout=None):
        """Guest sepetini Redis'e kaydet."""
        cache_key = CartService._get_redis_cart_key(tenant_id, session_id)
        try:
            cart_json = json.dumps(cart_data, default=str)
            cache.set(
                cache_key,
                cart_json,
                timeout or CartService.CART_TIMEOUT
            )
            logger.debug(f"Cart saved to Redis: {cache_key}")
        except Exception as e:
            logger.error(f"Error saving cart to Redis: {e}")
    
    @staticmethod
    def _delete_redis_cart(tenant_id, session_id):
        """Redis'ten guest sepeti sil."""
        cache_key = CartService._get_redis_cart_key(tenant_id, session_id)
        cache.delete(cache_key)
        logger.debug(f"Cart deleted from Redis: {cache_key}")
    
    @staticmethod
    def get_or_create_cart(tenant, customer=None, session_id=None, currency='TRY'):
        """
        Sepeti al veya oluştur.
        
        Args:
            tenant: Tenant instance
            customer: User instance (opsiyonel)
            session_id: Session ID (guest checkout için)
            currency: Para birimi kodu (default: TRY)
        
        Returns:
            Cart: Sepet instance (DB'den) veya dict (Redis'ten)
        """
        if customer:
            # Müşteri sepeti - DB'de tutulur
            cart = Cart.objects.filter(
                tenant=tenant,
                customer=customer,
                is_active=True
            ).first()
            
            if not cart:
                # Aktif sepet yoksa, pasif sepeti aktif yap veya yeni oluştur
                cart = Cart.objects.filter(
                    tenant=tenant,
                    customer=customer,
                    is_active=False
                ).order_by('-created_at').first()
                
                if cart:
                    # Pasif sepeti aktif yap
                    cart.is_active = True
                    cart.currency = currency
                    cart.expires_at = timezone.now() + timedelta(days=30)
                    cart.save()
                    logger.info(f"Cart reactivated for tenant {tenant.name}, customer {customer.email}")
                else:
                    # Yeni sepet oluştur
                    cart = Cart.objects.create(
                        tenant=tenant,
                        customer=customer,
                        is_active=True,
                        currency=currency,
                        expires_at=timezone.now() + timedelta(days=30),
                    )
                    logger.info(f"Cart created for tenant {tenant.name}, customer {customer.email}")
            
            return cart
        else:
            # Guest sepeti - Redis'te tutulur
            if not session_id:
                raise ValueError("Guest checkout için session_id gereklidir.")
            
            # Redis'ten sepeti al
            cart_data = CartService._get_redis_cart(str(tenant.id), session_id)
            
            if cart_data:
                # Sepet var, güncelle
                cart_data['currency'] = currency
                cart_data['updated_at'] = timezone.now().isoformat()
                CartService._save_redis_cart(str(tenant.id), session_id, cart_data)
                logger.debug(f"Cart retrieved from Redis: {session_id}")
                return cart_data
            else:
                # Yeni sepet oluştur
                cart_data = {
                    'id': str(uuid.uuid4()),
                    'tenant_id': str(tenant.id),
                    'session_id': session_id,
                    'customer_id': None,
                    'currency': currency,
                    'items': [],
                    'subtotal': '0.00',
                    'shipping_cost': '0.00',
                    'tax_amount': '0.00',
                    'discount_amount': '0.00',
                    'total': '0.00',
                    'shipping_method_id': None,
                    'coupon_code': None,
                    'is_active': True,
                    'created_at': timezone.now().isoformat(),
                    'updated_at': timezone.now().isoformat(),
                    'expires_at': (timezone.now() + timedelta(days=30)).isoformat(),
                }
                CartService._save_redis_cart(str(tenant.id), session_id, cart_data)
                logger.info(f"Cart created in Redis for tenant {tenant.name}, session {session_id}")
                return cart_data
    
    @staticmethod
    def add_to_cart(cart, product_id, variant_id=None, quantity=1, target_currency=None):
        """
        Sepete ürün ekle.
        
        Args:
            cart: Cart instance (DB) veya dict (Redis)
            product_id: Product UUID
            variant_id: ProductVariant UUID (opsiyonel)
            quantity: Miktar
            target_currency: Hedef para birimi (opsiyonel, cart'tan alınır)
        
        Returns:
            CartItem: Eklenen veya güncellenen sepet kalemi (DB) veya dict (Redis)
        """
        # Cart tipini kontrol et (DB mi Redis mi?)
        is_redis_cart = isinstance(cart, dict)
        
        if is_redis_cart:
            tenant_id = cart['tenant_id']
            session_id = cart['session_id']
            currency = target_currency or cart.get('currency', 'TRY')
        else:
            tenant = cart.tenant
            currency = target_currency or cart.currency or 'TRY'
        
        # Ürün kontrolü
        try:
            if is_redis_cart:
                from apps.models import Tenant
                tenant = Tenant.objects.get(id=tenant_id)
            
            product = Product.objects.get(id=product_id, tenant=tenant, is_deleted=False)
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
        
        # Fiyat belirleme
        if variant:
            unit_price = variant.price
            product_currency = product.currency or 'TRY'
        else:
            unit_price = product.price
            product_currency = product.currency or 'TRY'
        
        # Para birimi dönüşümü
        if product_currency != currency:
            try:
                unit_price = CurrencyService.convert_amount(
                    Decimal(str(unit_price)),
                    product_currency,
                    currency
                )
            except Exception as e:
                logger.warning(f"Currency conversion failed: {e}, using original price")
        
        total_price = Decimal(str(unit_price)) * quantity
        
        if is_redis_cart:
            # Redis sepeti - dict olarak işle
            items = cart.get('items', [])
            
            # Aynı ürün/varyant var mı?
            existing_item_index = None
            for idx, item in enumerate(items):
                if (str(item.get('product_id')) == str(product_id) and 
                    str(item.get('variant_id', '')) == str(variant_id or '')):
                    existing_item_index = idx
                    break
            
            if existing_item_index is not None:
                # Miktarı artır
                items[existing_item_index]['quantity'] += quantity
                items[existing_item_index]['total_price'] = str(
                    Decimal(str(items[existing_item_index]['unit_price'])) * 
                    items[existing_item_index]['quantity']
                )
            else:
                # Yeni kalem ekle
                items.append({
                    'id': str(uuid.uuid4()),
                    'product_id': str(product_id),
                    'variant_id': str(variant_id) if variant_id else None,
                    'quantity': quantity,
                    'unit_price': str(unit_price),
                    'total_price': str(total_price),
                    'product_name': product.name,
                    'variant_name': variant.name if variant else None,
                })
            
            cart['items'] = items
            CartService._calculate_redis_cart_totals(cart)
            CartService._save_redis_cart(tenant_id, session_id, cart)
            
            logger.info(f"Product added to Redis cart: {product.name} (qty: {quantity})")
            return items[existing_item_index] if existing_item_index is not None else items[-1]
        else:
            # DB sepeti - normal işlem
            existing_item = CartItem.objects.filter(
                cart=cart,
                product=product,
                variant=variant,
                is_deleted=False
            ).first()
            
            if existing_item:
                # Miktarı artır
                new_quantity = existing_item.quantity + quantity
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
            
            logger.info(f"Product added to DB cart: {product.name} (qty: {quantity})")
            return cart_item
    
    @staticmethod
    def _calculate_redis_cart_totals(cart_data):
        """Redis sepet toplamlarını hesapla."""
        items = cart_data.get('items', [])
        subtotal = sum(Decimal(str(item.get('total_price', '0'))) for item in items)
        
        cart_data['subtotal'] = str(subtotal)
        
        # Kargo ücreti (şimdilik 0)
        shipping_cost = Decimal(cart_data.get('shipping_cost', '0.00'))
        cart_data['shipping_cost'] = str(shipping_cost)
        
        # Vergi (basit %18 KDV)
        tax_amount = subtotal * Decimal('0.18')
        cart_data['tax_amount'] = str(tax_amount)
        
        # İndirim
        discount_amount = Decimal(cart_data.get('discount_amount', '0.00'))
        cart_data['discount_amount'] = str(discount_amount)
        
        # Toplam
        total = subtotal + shipping_cost + tax_amount - discount_amount
        cart_data['total'] = str(total)
        cart_data['updated_at'] = timezone.now().isoformat()
    
    @staticmethod
    def update_cart_item_quantity(cart, item_id, quantity):
        """
        Sepet kalemi miktarını güncelle.
        
        Args:
            cart: Cart instance (DB) veya dict (Redis)
            item_id: CartItem ID (DB) veya item dict (Redis)
            quantity: Yeni miktar
        """
        is_redis_cart = isinstance(cart, dict)
        
        if quantity <= 0:
            return CartService.remove_from_cart(cart, item_id)
        
        if is_redis_cart:
            # Redis sepeti
            items = cart.get('items', [])
            item_index = None
            
            # item_id dict ise id'sini al, string ise direkt kullan
            if isinstance(item_id, dict):
                item_id = item_id.get('id')
            
            for idx, item in enumerate(items):
                if str(item.get('id')) == str(item_id):
                    item_index = idx
                    break
            
            if item_index is None:
                raise ValueError("Sepet kalemi bulunamadı.")
            
            # Stok kontrolü (opsiyonel - şimdilik atlanıyor)
            items[item_index]['quantity'] = quantity
            items[item_index]['total_price'] = str(
                Decimal(str(items[item_index]['unit_price'])) * quantity
            )
            
            cart['items'] = items
            CartService._calculate_redis_cart_totals(cart)
            CartService._save_redis_cart(
                cart['tenant_id'],
                cart['session_id'],
                cart
            )
            return items[item_index]
        else:
            # DB sepeti
            if isinstance(item_id, dict):
                # Redis item dict'ten DB item'a geçiş (olmamalı ama güvenlik için)
                raise ValueError("Invalid item_id for DB cart")
            
            cart_item = CartItem.objects.get(id=item_id, cart=cart, is_deleted=False)
            
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
    def remove_from_cart(cart, item_id):
        """
        Sepetten ürün çıkar.
        
        Args:
            cart: Cart instance (DB) veya dict (Redis)
            item_id: CartItem ID (DB) veya item dict (Redis)
        """
        is_redis_cart = isinstance(cart, dict)
        
        if is_redis_cart:
            # Redis sepeti
            items = cart.get('items', [])
            
            # item_id dict ise id'sini al
            if isinstance(item_id, dict):
                item_id = item_id.get('id')
            
            items = [item for item in items if str(item.get('id')) != str(item_id)]
            cart['items'] = items
            CartService._calculate_redis_cart_totals(cart)
            CartService._save_redis_cart(
                cart['tenant_id'],
                cart['session_id'],
                cart
            )
            logger.info(f"Product removed from Redis cart: {item_id}")
        else:
            # DB sepeti
            if isinstance(item_id, dict):
                raise ValueError("Invalid item_id for DB cart")
            
            cart_item = CartItem.objects.get(id=item_id, cart=cart, is_deleted=False)
            product_name = cart_item.product.name
            cart_item.delete()
            logger.info(f"Product removed from DB cart: {product_name}")
    
    @staticmethod
    def clear_cart(cart):
        """Sepeti temizle."""
        is_redis_cart = isinstance(cart, dict)
        
        if is_redis_cart:
            # Redis sepeti
            cart['items'] = []
            CartService._calculate_redis_cart_totals(cart)
            CartService._save_redis_cart(
                cart['tenant_id'],
                cart['session_id'],
                cart
            )
            logger.info(f"Redis cart cleared: {cart['session_id']}")
        else:
            # DB sepeti
            cart.items.all().delete()
            cart.calculate_totals()
            logger.info(f"DB cart cleared for tenant {cart.tenant.name}")

