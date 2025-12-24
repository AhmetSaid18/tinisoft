"""
Cart views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from apps.models import Cart, ShippingMethod
from apps.serializers.cart import CartSerializer, AddToCartSerializer
from apps.services.cart_service import CartService
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def cart_detail(request):
    """
    Sepet detayı (GET) veya sepet oluştur (POST).
    
    GET: /api/cart/
    POST: /api/cart/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        # Müşteri sepeti veya guest sepeti
        customer = None
        session_id = None
        
        if request.user.is_authenticated and request.user.is_tenant_user and request.user.tenant == tenant:
            customer = request.user
        else:
            # Guest checkout için session_id
            session_id = request.session.session_key
            if not session_id:
                request.session.create()
                session_id = request.session.session_key
        
        try:
            cart = CartService.get_or_create_cart(tenant, customer, session_id)
            serializer = CartSerializer(cart)
            return Response({
                'success': True,
                'cart': serializer.data,
            })
        except ValueError as e:
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'POST':
        # Sepet oluştur (genelde GET ile otomatik oluşturulur)
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
            cart = CartService.get_or_create_cart(tenant, customer, session_id)
            serializer = CartSerializer(cart)
            return Response({
                'success': True,
                'message': 'Sepet oluşturuldu.',
                'cart': serializer.data,
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def add_to_cart(request):
    """
    Sepete ürün ekle.
    
    POST: /api/cart/add/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = AddToCartSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        
        # Sepeti al veya oluştur
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
            cart = CartService.get_or_create_cart(tenant, customer, session_id)
            cart_item = CartService.add_to_cart(
                cart=cart,
                product_id=data['product_id'],
                variant_id=data.get('variant_id'),
                quantity=data.get('quantity', 1),
            )
            
            # Sepeti yeniden yükle
            cart.refresh_from_db()
            serializer = CartSerializer(cart)
            return Response({
                'success': True,
                'message': 'Ürün sepete eklendi.',
                'cart': serializer.data,
            })
        except ValueError as e:
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': False,
        'message': 'Ürün sepete eklenemedi.',
        'errors': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH', 'DELETE'])
@permission_classes([AllowAny])
def cart_item_detail(request, item_id):
    """
    Sepet kalemi güncelle (PATCH) veya sil (DELETE).
    
    PATCH: /api/cart/items/{item_id}/
    DELETE: /api/cart/items/{item_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    from apps.models import CartItem
    
    try:
        cart_item = CartItem.objects.get(
            id=item_id,
            cart__tenant=tenant,
            is_deleted=False,
        )
    except CartItem.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Sepet kalemi bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Permission kontrolü
    if request.user.is_authenticated:
        if cart_item.cart.customer and cart_item.cart.customer != request.user:
            return Response({
                'success': False,
                'message': 'Bu sepet kalemine erişim yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
    else:
        if cart_item.cart.session_id != request.session.session_key:
            return Response({
                'success': False,
                'message': 'Bu sepet kalemine erişim yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'PATCH':
        quantity = request.data.get('quantity')
        if quantity:
            try:
                CartService.update_cart_item_quantity(cart_item, quantity)
                cart_item.cart.refresh_from_db()
                serializer = CartSerializer(cart_item.cart)
                return Response({
                    'success': True,
                    'message': 'Sepet kalemi güncellendi.',
                    'cart': serializer.data,
                })
            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e),
                }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        CartService.remove_from_cart(cart_item)
        cart_item.cart.refresh_from_db()
        serializer = CartSerializer(cart_item.cart)
        return Response({
            'success': True,
            'message': 'Ürün sepetten çıkarıldı.',
            'cart': serializer.data,
        })


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_shipping_method(request):
    """
    Sepet kargo yöntemini güncelle.
    
    PATCH: /api/cart/shipping/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    shipping_method_id = request.data.get('shipping_method_id')
    if not shipping_method_id:
        return Response({
            'success': False,
            'message': 'Kargo yöntemi ID gereklidir.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        shipping_method = ShippingMethod.objects.get(
            id=shipping_method_id,
            tenant=tenant,
            is_active=True,
        )
    except ShippingMethod.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Kargo yöntemi bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sepeti al
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
        cart = CartService.get_or_create_cart(tenant, customer, session_id)
        cart.shipping_method = shipping_method
        cart.save()
        cart.calculate_totals()
        
        serializer = CartSerializer(cart)
        return Response({
            'success': True,
            'message': 'Kargo yöntemi güncellendi.',
            'cart': serializer.data,
        })
    except ValueError as e:
        return Response({
            'success': False,
            'message': str(e),
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'DELETE'])
@permission_classes([AllowAny])
def apply_coupon(request):
    """
    Sepete kupon uygula (POST) veya kaldır (DELETE).
    
    POST: /api/cart/coupon/
    Body: {"coupon_code": "KUPON123"}
    
    DELETE: /api/cart/coupon/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sepeti al
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
        cart = CartService.get_or_create_cart(tenant, customer, session_id)
    except ValueError as e:
        return Response({
            'success': False,
            'message': str(e),
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'POST':
        coupon_code = request.data.get('coupon_code')
        if not coupon_code:
            return Response({
                'success': False,
                'message': 'Kupon kodu gereklidir.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from apps.models import Coupon
        from decimal import Decimal
        
        try:
            coupon = Coupon.objects.get(
                code=coupon_code,
                tenant=tenant,
                is_deleted=False
            )
        except Coupon.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Kupon bulunamadı.',
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Kupon geçerliliğini kontrol et
        customer_email = None
        if customer:
            customer_email = customer.email
        
        is_valid, message = coupon.is_valid(customer_email, cart.subtotal)
        
        if not is_valid:
            return Response({
                'success': False,
                'message': message,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Kuponu sepete uygula
        cart.coupon = coupon
        cart.coupon_code = coupon.code
        cart.save()
        cart.calculate_totals()
        
        serializer = CartSerializer(cart)
        return Response({
            'success': True,
            'message': 'Kupon sepete uygulandı.',
            'cart': serializer.data,
        })
    
    elif request.method == 'DELETE':
        # Kuponu kaldır
        cart.coupon = None
        cart.coupon_code = ''
        cart.save()
        cart.calculate_totals()
        
        serializer = CartSerializer(cart)
        return Response({
            'success': True,
            'message': 'Kupon sepetten kaldırıldı.',
            'cart': serializer.data,
        })
