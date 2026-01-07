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
    def _check_stock_availability(product, variant, quantity):
        """
        Stok kontrolü yap (gerçek stok + sanal stok).
        
        Args:
            product: Product instance
            variant: ProductVariant instance (opsiyonel)
            quantity: İstenen miktar
        
        Returns:
            tuple: (is_available: bool, available_quantity: int, message: str)
        """
        # Varyantlı ürün kontrolü
        if variant:
            if not variant.track_inventory:
                # Stok takibi yapılmıyorsa, her zaman mevcut
                return True, None, None
            
            # Gerçek stok
            real_stock = variant.inventory_quantity
            available_qty = real_stock
            
            # Sanal stok kontrolü
            if variant.allow_backorder:
                # Sanal stok aktif
                if variant.virtual_stock_quantity is not None and variant.virtual_stock_quantity > 0:
                    # Limitli sanal stok: gerçek stok + sanal stok
                    available_qty = real_stock + variant.virtual_stock_quantity
                else:
                    # Sınırsız sanal stok (backorder açık, limit yok)
                    available_qty = None  # Sınırsız
                    return True, None, None
            else:
                # Sanal stok yok, sadece gerçek stok
                pass
            
            # Miktar kontrolü
            if available_qty is not None and available_qty < quantity:
                message = f"Yeterli stok yok. Mevcut stok: {real_stock}"
                if variant.allow_backorder and variant.virtual_stock_quantity and variant.virtual_stock_quantity > 0:
                    message += f" (Toplam: {available_qty} - Gerçek: {real_stock}, Sanal: {variant.virtual_stock_quantity})"
                return False, available_qty, message
            
            return True, available_qty, None
        else:
            # Basit ürün kontrolü
            if not product.track_inventory:
                # Stok takibi yapılmıyorsa, her zaman mevcut
                return True, None, None
            
            # Gerçek stok
            real_stock = product.inventory_quantity
            available_qty = real_stock
            
            # Sanal stok kontrolü
            if product.allow_backorder:
                # Sanal stok aktif
                if product.virtual_stock_quantity is not None and product.virtual_stock_quantity > 0:
                    # Limitli sanal stok: gerçek stok + sanal stok
                    available_qty = real_stock + product.virtual_stock_quantity
                else:
                    # Sınırsız sanal stok (backorder açık, limit yok)
                    available_qty = None  # Sınırsız
                    return True, None, None
            else:
                # Sanal stok yok, sadece gerçek stok
                pass
            
            # Miktar kontrolü
            if available_qty is not None and available_qty < quantity:
                message = f"Yeterli stok yok. Mevcut stok: {real_stock}"
                if product.allow_backorder and product.virtual_stock_quantity and product.virtual_stock_quantity > 0:
                    message += f" (Toplam: {available_qty} - Gerçek: {real_stock}, Sanal: {product.virtual_stock_quantity})"
                return False, available_qty, message
            
            return True, available_qty, None
    
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
        Giriş yapan kullanıcı için DB, guest için Redis kullanılır.
        """
        if customer:
            # Müşteri sepeti - DB'de tutulur
            cart = Cart.objects.filter(
                tenant=tenant,
                customer=customer,
                is_deleted=False
            ).order_by('-created_at').first()
            
            if not cart:
                cart = Cart.objects.create(
                    tenant=tenant,
                    customer=customer,
                    currency=currency,
                    expires_at=timezone.now() + timedelta(days=30),
                )
            else:
                cart.currency = currency
                cart.expires_at = timezone.now() + timedelta(days=30)
                cart.save()
            return cart
            
        elif session_id:
            # Guest sepeti - Redis'te tutulur
            cart_data = CartService._get_redis_cart(tenant.id, session_id)
            if not cart_data:
                cart_data = {
                    'id': str(uuid.uuid4()),
                    'tenant_id': str(tenant.id),
                    'session_id': session_id,
                    'items': [],
                    'subtotal': '0.00',
                    'total': '0.00',
                    'currency': currency,
                    'created_at': timezone.now().isoformat(),
                    'updated_at': timezone.now().isoformat(),
                }
                CartService._save_redis_cart(tenant.id, session_id, cart_data)
            return cart_data
        
        raise ValueError("Sepet için müşteri bilgisi veya oturum ID gereklidir.")

    @staticmethod
    def merge_carts(tenant, customer, session_id):
        """
        Guest sepetini (Redis) kullanıcı sepetine (DB) aktar.
        """
        if not customer or not session_id:
            return
            
        guest_cart = CartService._get_redis_cart(tenant.id, session_id)
        if not guest_cart or not guest_cart.get('items'):
            return
            
        # Kullanıcı sepetini al
        user_cart = CartService.get_or_create_cart(tenant, customer=customer)
        
        # Öğeleri aktar
        for item in guest_cart.get('items', []):
            try:
                CartService.add_to_cart(
                    cart=user_cart,
                    product_id=item['product_id'],
                    variant_id=item.get('variant_id'),
                    quantity=int(item['quantity']),
                    target_currency=user_cart.currency
                )
            except Exception as e:
                logger.error(f"Error merging cart item: {e}")
        
        # Guest sepetini sil
        CartService._delete_redis_cart(tenant.id, session_id)
        user_cart.calculate_totals()
        return user_cart
    
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
        
        # Stok kontrolü (gerçek + sanal stok)
        is_available, available_qty, message = CartService._check_stock_availability(
            product,
            variant,
            quantity
        )
        if not is_available:
            raise ValueError(message)
        
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
        
        # Vergi (Dinamik - Tenant bazlı)
        from apps.models import Tax, Tenant
        try:
            tenant = Tenant.objects.get(id=cart_data.get('tenant_id'))
            active_tax = Tax.objects.filter(
                tenant=tenant,
                is_active=True,
                is_deleted=False
            ).order_by('-is_default', '-created_at').first()
            tax_rate = active_tax.rate if active_tax else Decimal('0.00')
        except:
            tax_rate = Decimal('0.00')
            
        tax_amount = subtotal * (tax_rate / Decimal('100'))
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
            
            # Stok kontrolü (gerçek + sanal stok)
            is_available, available_qty, message = CartService._check_stock_availability(
                cart_item.product,
                cart_item.variant,
                quantity
            )
            if not is_available:
                raise ValueError(message)
            
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

