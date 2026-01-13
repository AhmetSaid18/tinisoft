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
    Sadece giriş yapan kullanıcılar için çalışır. Guest sepetleri frontend'de tutulur.
    
    GET: /api/basket/
    Query params: {
        "currency": "TRY"  // opsiyonel, default: TRY
    }
    
    POST: /api/basket/
    Body: {
        "product_id": "uuid",
        "variant_id": "uuid",  // opsiyonel
        "quantity": 1,
        "currency": "TRY"      // opsiyonel
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Mağaza bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece giriş yapan kullanıcılar için
    if not request.user.is_authenticated or not request.user.is_tenant_user or request.user.tenant != tenant:
        return Response({
            'success': False,
            'message': 'Sepet işlemleri için giriş yapmanız gerekiyor.',
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    customer = request.user
    
    # Para birimi
    if request.method == 'POST':
        currency = request.data.get('currency') or request.query_params.get('currency', 'TRY')
    else:
        currency = request.query_params.get('currency', 'TRY')
    currency = str(currency).upper() if currency else 'TRY'
    
    try:
        cart = CartService.get_or_create_cart(tenant, customer, None, currency)
        
        if request.method == 'GET':
            # Sepeti getir
            serializer = CartSerializer(cart, context={'request': request})
            return Response({
                'success': True,
                'basket': serializer.data,
            })
        else:
            # Sepete ürün ekle
            logger.info(f"[BASKET] POST Data: {request.data}")
            serializer = AddToCartSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"[BASKET] Validation Error: {serializer.errors}")
                return Response({
                    'success': False,
                    'message': 'Geçersiz veri.',
                    'errors': serializer.errors,
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            try:
                CartService.add_to_cart(
                    cart=cart,
                    product_id=data['product_id'],
                    variant_id=data.get('variant_id'),
                    quantity=data.get('quantity', 1),
                    target_currency=currency,
                )
            except ValueError as e:
                logger.warning(f"[BASKET] Service Error: {str(e)}")
                return Response({
                    'success': False,
                    'message': str(e),
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Sepeti yeniden yükle
            cart = CartService.get_or_create_cart(tenant, customer, None, currency)
            serializer = CartSerializer(cart, context={'request': request})
            return Response({
                'success': True,
                'message': 'Ürün sepete eklendi.',
                'basket': serializer.data,
            })
    except Exception as e:
        logger.error(f"[BASKET] Unexpected Error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': str(e),
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH', 'DELETE'])
@permission_classes([AllowAny])
def basket_item(request, item_id):
    """
    Sepetteki ürünü güncelle (PATCH) veya sil (DELETE).
    Sadece giriş yapan kullanıcılar için çalışır.
    
    PATCH: /api/basket/{item_id}/
    Body: {
        "quantity": 3,
        "currency": "TRY"  // opsiyonel
    }
    
    DELETE: /api/basket/{item_id}/
    """
    logger.info(f"[BASKET_ITEM] {request.method} /api/basket/{item_id}/ | User: {request.user.email if request.user.is_authenticated else 'Anonymous'}")
    
    tenant = get_tenant_from_request(request)
    if not tenant:
        logger.warning(f"[BASKET_ITEM] Tenant not found for item_id: {item_id}")
        return Response({
            'success': False,
            'message': 'Mağaza bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece giriş yapan kullanıcılar için
    if not request.user.is_authenticated or not request.user.is_tenant_user or request.user.tenant != tenant:
        logger.warning(f"[BASKET_ITEM] Unauthorized access attempt for item_id: {item_id}")
        return Response({
            'success': False,
            'message': 'Sepet işlemleri için giriş yapmanız gerekiyor.',
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    customer = request.user
    
    # Para birimi
    currency = request.data.get('currency') or request.query_params.get('currency', 'TRY')
    currency = str(currency).upper() if currency else 'TRY'
    
    try:
        cart = CartService.get_or_create_cart(tenant, customer, None, currency)
        
        # DB sepeti
        from apps.models import CartItem
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart, is_deleted=False)
            logger.debug(f"[BASKET_ITEM] CartItem found: {cart_item.product.name} (qty: {cart_item.quantity})")
        except CartItem.DoesNotExist:
            logger.warning(f"[BASKET_ITEM] CartItem not found: item_id={item_id}, cart_id={cart.id}, tenant={tenant.slug}")
            return Response({
                'success': False,
                'message': 'Sepet kalemi bulunamadı.',
            }, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'PATCH':
            # Güncelle
            quantity = request.data.get('quantity')
            if quantity is None:
                logger.warning(f"[BASKET_ITEM] PATCH request missing quantity: {request.data} | item_id: {item_id}")
                return Response({
                    'success': False,
                    'message': 'Miktar (quantity) gereklidir.',
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                quantity = int(quantity)
            except (ValueError, TypeError):
                logger.warning(f"[BASKET_ITEM] PATCH request invalid quantity: {quantity} (type: {type(quantity)}) | item_id: {item_id}")
                return Response({
                    'success': False,
                    'message': 'Geçerli bir miktar giriniz (sayı olmalı).',
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if quantity < 1:
                logger.warning(f"[BASKET_ITEM] PATCH request quantity < 1: {quantity} | item_id: {item_id}")
                return Response({
                    'success': False,
                    'message': 'Miktar en az 1 olmalıdır.',
                }, status=status.HTTP_400_BAD_REQUEST)
            
            CartService.update_cart_item_quantity(cart, cart_item.id, quantity)
            logger.info(f"[BASKET_ITEM] CartItem updated: {cart_item.product.name} (qty: {quantity})")
            message = 'Sepet kalemi güncellendi.'
        else:
            # Sil
            CartService.remove_from_cart(cart, cart_item.id)
            logger.info(f"[BASKET_ITEM] CartItem deleted: {cart_item.product.name}")
            message = 'Ürün sepetten çıkarıldı.'
        
        # Sepeti yeniden yükle
        cart = CartService.get_or_create_cart(tenant, customer, None, currency)
        serializer = CartSerializer(cart, context={'request': request})
        
        return Response({
            'success': True,
            'message': message,
            'basket': serializer.data,
        })
    except ValueError as e:
        logger.error(f"[BASKET_ITEM] ValueError: {str(e)} | item_id: {item_id}, method: {request.method}")
        return Response({
            'success': False,
            'message': str(e),
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"[BASKET_ITEM] Unexpected error: {str(e)} | item_id: {item_id}, method: {request.method}", exc_info=True)
        return Response({
            'success': False,
            'message': 'Bir hata oluştu.',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

