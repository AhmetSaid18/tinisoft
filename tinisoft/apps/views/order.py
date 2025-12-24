"""
Order views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from apps.models import Order, Cart, ShippingAddress, ShippingMethod
from apps.serializers.order import OrderListSerializer, OrderDetailSerializer, CreateOrderSerializer
from apps.services.order_service import OrderService
from apps.services.customer_service import CustomerService
from apps.permissions import IsTenantOwnerOfObject
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class OrderPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def order_list_create(request):
    """
    Sipariş listesi (GET) veya yeni sipariş oluştur (POST).
    
    GET: /api/orders/
    POST: /api/orders/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        # Permission kontrolü
        # TenantUser sadece kendi siparişlerini görebilir
        # TenantOwner/Admin tüm siparişleri görebilir
        if request.user.is_tenant_user and request.user.tenant == tenant:
            # Müşteri - sadece kendi siparişleri
            queryset = Order.objects.filter(
                tenant=tenant,
                customer=request.user,
                is_deleted=False
            )
        elif request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant):
            # Owner/TenantOwner - tüm siparişler
            queryset = Order.objects.filter(tenant=tenant, is_deleted=False)
        else:
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Status filtresi
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Payment status filtresi
        payment_status = request.query_params.get('payment_status')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        
        # Müşteri email filtresi
        customer_email = request.query_params.get('customer_email')
        if customer_email:
            queryset = queryset.filter(customer_email__icontains=customer_email)
        
        # Sipariş numarası filtresi
        order_number = request.query_params.get('order_number')
        if order_number:
            queryset = queryset.filter(order_number__icontains=order_number)
        
        # Sıralama
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        paginator = OrderPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = OrderListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = OrderListSerializer(queryset, many=True)
        return Response({
            'success': True,
            'orders': serializer.data,
        })
    
    elif request.method == 'POST':
        # Müşteri siparişi oluşturabilir
        serializer = CreateOrderSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Sepet kontrolü
            cart_id = data.get('cart_id')
            if not cart_id:
                return Response({
                    'success': False,
                    'message': 'Sepet ID gereklidir.',
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                cart = Cart.objects.get(
                    id=cart_id,
                    tenant=tenant,
                    is_active=True,
                )
            except Cart.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Sepet bulunamadı veya aktif değil.',
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Kargo adresi
            shipping_address = None
            if data.get('shipping_address_id'):
                try:
                    shipping_address = ShippingAddress.objects.get(
                        id=data['shipping_address_id'],
                        tenant=tenant,
                    )
                except ShippingAddress.DoesNotExist:
                    pass
            
            # Kargo yöntemi
            shipping_method = None
            if data.get('shipping_method_id'):
                try:
                    shipping_method = ShippingMethod.objects.get(
                        id=data['shipping_method_id'],
                        tenant=tenant,
                        is_active=True,
                    )
                except ShippingMethod.DoesNotExist:
                    pass
            
            # Müşteri user'ı
            customer_user = None
            if request.user.is_tenant_user and request.user.tenant == tenant:
                customer_user = request.user
                # Müşteri profili oluştur/güncelle
                try:
                    CustomerService.get_or_create_customer(tenant, customer_user)
                except:
                    pass
            
            try:
                order = OrderService.create_order_from_cart(
                    cart=cart,
                    customer_email=data['customer_email'],
                    customer_first_name=data['customer_first_name'],
                    customer_last_name=data['customer_last_name'],
                    customer_phone=data.get('customer_phone'),
                    shipping_address=shipping_address,
                    shipping_method=shipping_method,
                    customer_note=data.get('customer_note', ''),
                    billing_address=data.get('billing_address', {}),
                    customer_user=customer_user,
                )
                
                return Response({
                    'success': True,
                    'message': 'Sipariş oluşturuldu.',
                    'order': OrderDetailSerializer(order).data,
                }, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e),
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'message': 'Sipariş oluşturulamadı.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def order_detail(request, order_id):
    """
    Sipariş detayı (GET) veya güncelleme (PATCH).
    
    GET: /api/orders/{order_id}/
    PATCH: /api/orders/{order_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        order = Order.objects.get(id=order_id, tenant=tenant, is_deleted=False)
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Sipariş bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Permission kontrolü
    # Owner veya TenantOwner erişebilir
    # TenantUser sadece kendi siparişlerine erişebilir
    if request.user.is_tenant_user:
        if order.customer != request.user:
            return Response({
                'success': False,
                'message': 'Bu siparişe erişim yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
    elif not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = OrderDetailSerializer(order)
        return Response({
            'success': True,
            'order': serializer.data,
        })
    
    elif request.method == 'PATCH':
        # Sadece TenantOwner veya Owner durum güncelleyebilir
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            return Response({
                'success': False,
                'message': 'Sipariş durumunu güncelleme yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        new_status = request.data.get('status')
        if new_status:
            try:
                order = OrderService.update_order_status(order, new_status, request.user)
            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e),
                }, status=status.HTTP_400_BAD_REQUEST)
        
        tracking_number = request.data.get('tracking_number')
        if tracking_number:
            order.tracking_number = tracking_number
            order.save()
        
        serializer = OrderDetailSerializer(order)
        return Response({
            'success': True,
            'message': 'Sipariş güncellendi.',
            'order': serializer.data,
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def order_track(request, order_number):
    """
    Sipariş takip - Müşteriler sipariş numarası ile sipariş durumunu görebilir.
    
    GET: /api/orders/track/{order_number}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        order = Order.objects.get(
            order_number=order_number,
            tenant=tenant,
            is_deleted=False
        )
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Sipariş bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece temel bilgileri döndür (güvenlik için)
    return Response({
        'success': True,
        'order': {
            'order_number': order.order_number,
            'status': order.status,
            'status_display': order.get_status_display(),
            'payment_status': order.payment_status,
            'payment_status_display': order.get_payment_status_display(),
            'tracking_number': order.tracking_number,
            'shipped_at': order.shipped_at.isoformat() if order.shipped_at else None,
            'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
            'created_at': order.created_at.isoformat(),
            'total': str(order.total),
            'currency': order.currency,
        },
    })
