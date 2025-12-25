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

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def basket(request):
    """
    Sepeti getir (GET) veya sepete ürün ekle (POST).
    
    GET: /api/basket/
    POST: /api/basket/
    Body: {
        "product_id": "uuid",
        "variant_id": "uuid",  // opsiyonel
        "quantity": 1
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Mağaza bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Para birimi
    currency = request.headers.get('X-Currency-Code') or request.query_params.get('currency', 'TRY')
    currency = currency.upper()
    
    # Kullanıcı veya session
    customer = None
    session_id = None
    
    if request.user.is_authenticated and request.user.is_tenant_user and request.user.tenant == tenant:
        customer = request.user
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
    
    try:
        cart = CartService.get_or_create_cart(tenant, customer, session_id, currency)
        
        if request.method == 'GET':
            # Sepeti getir
            serializer = CartSerializer(cart, context={'request': request})
            return Response({
                'success': True,
                'basket': serializer.data,
            })
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
            cart = CartService.get_or_create_cart(tenant, customer, session_id, currency)
            serializer = CartSerializer(cart, context={'request': request})
            return Response({
                'success': True,
                'message': 'Ürün sepete eklendi.',
                'basket': serializer.data,
            })
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
        "quantity": 3
    }
    
    DELETE: /api/basket/{item_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Mağaza bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Para birimi
    currency = request.headers.get('X-Currency-Code') or request.query_params.get('currency', 'TRY')
    currency = currency.upper()
    
    # Kullanıcı veya session
    customer = None
    session_id = None
    
    if request.user.is_authenticated and request.user.is_tenant_user and request.user.tenant == tenant:
        customer = request.user
    else:
        session_id = request.session.session_key
        if not session_id:
            return Response({
                'success': False,
                'message': 'Sepet bulunamadı.',
            }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        cart = CartService.get_or_create_cart(tenant, customer, session_id, currency)
        
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
        cart = CartService.get_or_create_cart(tenant, customer, session_id, currency)
        serializer = CartSerializer(cart, context={'request': request})
        
        return Response({
            'success': True,
            'message': message,
            'basket': serializer.data,
        })
    except ValueError as e:
        return Response({
            'success': False,
            'message': str(e),
        }, status=status.HTTP_400_BAD_REQUEST)

