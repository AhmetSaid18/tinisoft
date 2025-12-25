"""
Basket views - Basit sepet CRUD işlemleri.
Redis'te guest sepetleri, DB'de kayıtlı kullanıcı sepetleri.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.serializers.cart import CartSerializer, AddToCartSerializer
from apps.services.cart_service import CartService
from core.middleware import get_tenant_from_request
import logging
import uuid

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def basket(request):
    """
    Sepeti getir (GET) veya sepete ürün ekle (POST).
    
    GET: /api/basket/
    Query params veya body: {
        "guest_id": "uuid",  // opsiyonel, yoksa yeni oluşturulur
        "currency": "TRY"    // opsiyonel, default: TRY
    }
    
    POST: /api/basket/
    Body: {
        "product_id": "uuid",
        "variant_id": "uuid",  // opsiyonel
        "quantity": 1,
        "guest_id": "uuid",    // opsiyonel
        "currency": "TRY"      // opsiyonel
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Mağaza bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Para birimi - önce body'den, sonra query params'tan, sonra default
    if request.method == 'POST':
        currency = request.data.get('currency') or request.query_params.get('currency', 'TRY')
    else:
        currency = request.query_params.get('currency') or request.data.get('currency', 'TRY')
    currency = str(currency).upper() if currency else 'TRY'
    
    # Kullanıcı veya guest ID
    customer = None
    guest_id = None
    
    if request.user.is_authenticated and request.user.is_tenant_user and request.user.tenant == tenant:
        customer = request.user
    else:
        # Frontend'den gelen guest ID'yi al - önce body'den, sonra query params'tan
        if request.method == 'POST':
            guest_id = request.data.get('guest_id') or request.query_params.get('guest_id')
        else:
            guest_id = request.query_params.get('guest_id') or request.data.get('guest_id')
        
        if not guest_id:
            # Yeni guest ID oluştur (frontend response'da alacak)
            guest_id = str(uuid.uuid4())
    
    try:
        cart = CartService.get_or_create_cart(tenant, customer, guest_id, currency)
        
        if request.method == 'GET':
            # Sepeti getir
            serializer = CartSerializer(cart, context={'request': request})
            response_data = {
                'success': True,
                'basket': serializer.data,
            }
            # Guest ID'yi response body'ye ekle (frontend localStorage'a kaydedecek)
            if guest_id and not customer:
                response_data['guest_id'] = guest_id
            return Response(response_data)
        else:
            # Sepete ürün ekle
            serializer = AddToCartSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': 'Geçersiz veri.',
                    'errors': serializer.errors,
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            CartService.add_to_cart(
                cart=cart,
                product_id=data['product_id'],
                variant_id=data.get('variant_id'),
                quantity=data.get('quantity', 1),
                target_currency=currency,
            )
            
            # Sepeti yeniden yükle
            cart = CartService.get_or_create_cart(tenant, customer, guest_id, currency)
            serializer = CartSerializer(cart, context={'request': request})
            response_data = {
                'success': True,
                'message': 'Ürün sepete eklendi.',
                'basket': serializer.data,
            }
            # Guest ID'yi response body'ye ekle
            if guest_id and not customer:
                response_data['guest_id'] = guest_id
            return Response(response_data)
    except ValueError as e:
        return Response({
            'success': False,
            'message': str(e),
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH', 'DELETE'])
@permission_classes([AllowAny])
def basket_item(request, item_id):
    """
    Sepetteki ürünü güncelle (PATCH) veya sil (DELETE).
    
    PATCH: /api/basket/{item_id}/
    Body: {
        "quantity": 3,
        "guest_id": "uuid",  // gerekli (guest ise)
        "currency": "TRY"     // opsiyonel
    }
    
    DELETE: /api/basket/{item_id}/
    Body: {
        "guest_id": "uuid",  // gerekli (guest ise)
        "currency": "TRY"   // opsiyonel
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Mağaza bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Para birimi - body'den veya query params'tan
    currency = request.data.get('currency') or request.query_params.get('currency', 'TRY')
    currency = str(currency).upper() if currency else 'TRY'
    
    # Kullanıcı veya guest ID
    customer = None
    guest_id = None
    
    if request.user.is_authenticated and request.user.is_tenant_user and request.user.tenant == tenant:
        customer = request.user
    else:
        # Frontend'den gelen guest ID'yi al - body'den veya query params'tan
        guest_id = request.data.get('guest_id') or request.query_params.get('guest_id')
        if not guest_id:
            return Response({
                'success': False,
                'message': 'Sepet bulunamadı. Guest ID gerekli.',
            }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        cart = CartService.get_or_create_cart(tenant, customer, guest_id, currency)
        
        # Redis sepeti mi DB sepeti mi?
        is_redis_cart = isinstance(cart, dict)
        
        if is_redis_cart:
            # Redis sepeti - item'ı bul
            items = cart.get('items', [])
            cart_item = None
            for item in items:
                if str(item.get('id')) == str(item_id):
                    cart_item = item
                    break
            
            if not cart_item:
                return Response({
                    'success': False,
                    'message': 'Sepet kalemi bulunamadı.',
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # DB sepeti
            from apps.models import CartItem
            try:
                cart_item = CartItem.objects.get(id=item_id, cart=cart, is_deleted=False)
            except CartItem.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Sepet kalemi bulunamadı.',
                }, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'PATCH':
            # Güncelle
            quantity = request.data.get('quantity')
            if not quantity or quantity < 1:
                return Response({
                    'success': False,
                    'message': 'Geçerli bir miktar giriniz.',
                }, status=status.HTTP_400_BAD_REQUEST)
            
            CartService.update_cart_item_quantity(cart, cart_item, quantity)
            message = 'Sepet kalemi güncellendi.'
        else:
            # Sil
            CartService.remove_from_cart(cart, cart_item)
            message = 'Ürün sepetten çıkarıldı.'
        
        # Sepeti yeniden yükle
        cart = CartService.get_or_create_cart(tenant, customer, guest_id, currency)
        serializer = CartSerializer(cart, context={'request': request})
        
        response_data = {
            'success': True,
            'message': message,
            'basket': serializer.data,
        }
        # Guest ID'yi response body'ye ekle
        if guest_id and not customer:
            response_data['guest_id'] = guest_id
        return Response(response_data)
    except ValueError as e:
        return Response({
            'success': False,
            'message': str(e),
        }, status=status.HTTP_400_BAD_REQUEST)

