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
    try:
        # Request bilgilerini log'la
        user_email = request.user.email if request.user.is_authenticated else 'Anonymous'
        user_role = request.user.role if request.user.is_authenticated else 'None'
        tenant_slug_header = request.headers.get('X-Tenant-Slug', 'Not provided')
        tenant_id_header = request.headers.get('X-Tenant-ID', 'Not provided')
        
        logger.info(
            f"[ORDERS] {request.method} /api/orders/ | "
            f"User: {user_email} (Role: {user_role}) | "
            f"Tenant-Slug: {tenant_slug_header} | "
            f"Tenant-ID: {tenant_id_header} | "
            f"Authenticated: {request.user.is_authenticated}"
        )
        
        tenant = get_tenant_from_request(request)
        if not tenant:
            logger.warning(
                f"[ORDERS] {request.method} /api/orders/ | 400 | "
                f"Tenant not found | User: {user_email} | "
                f"Headers: X-Tenant-Slug={tenant_slug_header}, X-Tenant-ID={tenant_id_header}"
            )
            return Response({
                'success': False,
                'message': 'Tenant bulunamadı.',
                'error': 'Tenant bilgisi eksik. Lütfen X-Tenant-ID veya X-Tenant-Slug header\'ı gönderin.',
                'hint': 'Request headers\'da X-Tenant-ID veya X-Tenant-Slug olmalı, veya subdomain kullanılmalı.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"[ORDERS] Tenant found: {tenant.name} ({tenant.slug})")
        
        if request.method == 'GET':
            try:
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
                    logger.info(f"[ORDERS] GET - TenantUser filtering own orders")
                elif request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant):
                    # Owner/TenantOwner - tüm siparişler
                    queryset = Order.objects.filter(tenant=tenant, is_deleted=False)
                    logger.info(f"[ORDERS] GET - Owner/TenantOwner viewing all orders")
                else:
                    logger.warning(
                        f"[ORDERS] GET /api/orders/ | 403 | "
                        f"Permission denied | User: {user_email} (Role: {user_role}) | "
                        f"Tenant: {tenant.name}"
                    )
                    return Response({
                        'success': False,
                        'message': 'Bu işlem için yetkiniz yok.',
                        'error': f'User role ({user_role}) bu işlem için yeterli yetkiye sahip değil.',
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
                    logger.info(
                        f"[ORDERS] GET /api/orders/ | 200 | "
                        f"Count: {len(page)}/{paginator.page.paginator.count} | "
                        f"Tenant: {tenant.name}"
                    )
                    return paginator.get_paginated_response(serializer.data)
                
                serializer = OrderListSerializer(queryset, many=True)
                logger.info(
                    f"[ORDERS] GET /api/orders/ | 200 | "
                    f"Count: {queryset.count()} | "
                    f"Tenant: {tenant.name}"
                )
                return Response({
                    'success': True,
                    'orders': serializer.data,
                })
            
            except Exception as e:
                logger.error(
                    f"[ORDERS] GET /api/orders/ | 500 | "
                    f"Error: {str(e)} | "
                    f"User: {user_email} | "
                    f"Tenant: {tenant.name if tenant else 'None'}",
                    exc_info=True
                )
                return Response({
                    'success': False,
                    'message': 'Sipariş listesi alınırken bir hata oluştu.',
                    'error': str(e),
                    'error_type': type(e).__name__,
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        elif request.method == 'POST':
            try:
                # Müşteri siparişi oluşturabilir
                # Request data'yı güvenli şekilde al
                request_data = None
                try:
                    request_data = request.data
                    logger.info(f"[ORDERS] POST /api/orders/ | Request data keys: {list(request_data.keys()) if request_data else 'Empty'}")
                    logger.debug(f"[ORDERS] POST /api/orders/ | Request data: {request_data}")
                except Exception as data_exception:
                    logger.error(
                        f"[ORDERS] POST /api/orders/ | Error accessing request.data | "
                        f"Error: {str(data_exception)} | "
                        f"User: {user_email}",
                        exc_info=True
                    )
                    return Response({
                        'success': False,
                        'message': 'Request verisi okunamadı.',
                        'error': str(data_exception),
                        'error_type': type(data_exception).__name__,
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Serializer oluştur
                serializer = None
                try:
                    serializer = CreateOrderSerializer(data=request_data)
                except Exception as serializer_exception:
                    logger.error(
                        f"[ORDERS] POST /api/orders/ | Error creating serializer | "
                        f"Error: {str(serializer_exception)} | "
                        f"User: {user_email} | "
                        f"Tenant: {tenant.name}",
                        exc_info=True
                    )
                    return Response({
                        'success': False,
                        'message': 'Sipariş verisi işlenirken bir hata oluştu.',
                        'error': str(serializer_exception),
                        'error_type': type(serializer_exception).__name__,
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Serializer validation kontrolü
                if serializer is None:
                    logger.error(
                        f"[ORDERS] POST /api/orders/ | Serializer is None | "
                        f"User: {user_email} | "
                        f"Tenant: {tenant.name}"
                    )
                    return Response({
                        'success': False,
                        'message': 'Sipariş verisi işlenirken bir hata oluştu.',
                        'error': 'Serializer oluşturulamadı.',
                        'error_type': 'SerializerError',
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                is_valid = False
                validation_errors = {}
                try:
                    logger.info(f"[ORDERS] POST /api/orders/ | Starting serializer validation...")
                    is_valid = serializer.is_valid()
                    logger.info(f"[ORDERS] POST /api/orders/ | Serializer validation result: {is_valid}")
                    
                    if not is_valid:
                        validation_errors = serializer.errors
                        logger.warning(
                            f"[ORDERS] POST /api/orders/ | Serializer validation failed | "
                            f"Errors: {validation_errors} | "
                            f"User: {user_email} | "
                            f"Tenant: {tenant.name}"
                        )
                except Exception as validation_exception:
                    logger.error(
                        f"[ORDERS] POST /api/orders/ | Serializer validation exception | "
                        f"Error: {str(validation_exception)} | "
                        f"User: {user_email} | "
                        f"Tenant: {tenant.name}",
                        exc_info=True
                    )
                    return Response({
                        'success': False,
                        'message': 'Sipariş verileri işlenirken bir hata oluştu.',
                        'error': str(validation_exception),
                        'error_type': type(validation_exception).__name__,
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                logger.info(f"[ORDERS] POST /api/orders/ | Validation check complete, is_valid={is_valid}")
                
                if is_valid:
                    logger.info(f"[ORDERS] POST /api/orders/ | Processing valid order data...")
                    data = serializer.validated_data
                    logger.info(f"[ORDERS] POST /api/orders/ | Validated data keys: {list(data.keys()) if data else 'Empty'}")
                    
                    # Sepet kontrolü
                    cart_id = data.get('cart_id')
                    logger.info(f"[ORDERS] POST /api/orders/ | Cart ID from validated data: {cart_id}")
                    
                    # Eğer validated_data'da yoksa, request_data'dan al
                    if not cart_id:
                        cart_id = request_data.get('cart_id') if request_data else None
                        logger.info(f"[ORDERS] POST /api/orders/ | Cart ID from request_data: {cart_id}")
                    
                    # Payment method logla (DEBUG için)
                    p_method = data.get('payment_method')
                    logger.info(f"[ORDERS] POST /api/orders/ | Payment Method: '{p_method}' (Type: {type(p_method)})")
                    
                    if not cart_id:
                        logger.warning(
                            f"[ORDERS] POST /api/orders/ | 400 | "
                            f"Cart ID is missing | "
                            f"User: {user_email} | "
                            f"Tenant: {tenant.name}"
                        )
                        return Response({
                            'success': False,
                            'message': 'Sepet ID gereklidir.',
                            'error': 'cart_id field is required',
                            'error_type': 'ValidationError',
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    logger.info(
                        f"[ORDERS] POST /api/orders/ | Looking for cart | "
                        f"Cart ID: {cart_id} | "
                        f"Tenant: {tenant.name} ({tenant.id})"
                    )
                    
                    # Cart'ı bul - sadece ID ve tenant kontrolü yap
                    cart = None
                    cart_exists_anywhere = False
                    cart_tenant_mismatch = False
                    
                    try:
                        # Cart'ı ID ile bul (tenant kontrolü olmadan)
                        temp_cart = Cart.objects.get(id=cart_id)
                        cart_exists_anywhere = True
                        
                        # Tenant kontrolü
                        if temp_cart.tenant != tenant:
                            cart_tenant_mismatch = True
                            logger.warning(
                                f"[ORDERS] POST /api/orders/ | Cart belongs to different tenant | "
                                f"Cart ID: {cart_id} | "
                                f"Cart Tenant: {temp_cart.tenant.name} ({temp_cart.tenant.id}) | "
                                f"Request Tenant: {tenant.name} ({tenant.id})"
                            )
                        else:
                            # Tenant doğru, cart'ı kullan
                            cart = temp_cart
                            logger.info(
                                f"[ORDERS] POST /api/orders/ | Cart found | "
                                f"Cart ID: {cart.id} | "
                                f"Tenant: {cart.tenant.name}"
                            )
                    except Cart.DoesNotExist:
                        logger.warning(
                            f"[ORDERS] POST /api/orders/ | Cart does not exist | "
                            f"Cart ID: {cart_id}"
                        )
                    
                    # Cart bulunamadıysa detaylı hata mesajı döndür
                    if not cart:
                        error_message = 'Sepet bulunamadı.'
                        error_details = []
                        
                        if not cart_exists_anywhere:
                            error_message = 'Sepet bulunamadı. Geçersiz sepet ID.'
                            error_details.append('Cart ID does not exist')
                        elif cart_tenant_mismatch:
                            error_message = 'Sepet başka bir mağazaya ait. Lütfen doğru mağazadan sepet oluşturun.'
                            error_details.append('Cart belongs to different tenant')
                        
                        logger.warning(
                            f"[ORDERS] POST /api/orders/ | 400 | "
                            f"Cart not available | "
                            f"Cart ID: {cart_id} | "
                            f"Details: {error_details} | "
                            f"User: {user_email} | "
                            f"Tenant: {tenant.name}"
                        )
                        
                        response = Response({
                            'success': False,
                            'message': error_message,
                            'error': 'Cart not available',
                            'error_type': 'CartNotFound',
                            'error_details': error_details,
                            'cart_id': str(cart_id),
                        }, status=status.HTTP_400_BAD_REQUEST)
                        
                        logger.info(f"[ORDERS] POST /api/orders/ | Returning cart not found response with status {response.status_code}")
                        return response
                    
                    # Kargo adresi
                    shipping_address = None
                    if data.get('shipping_address_id'):
                        try:
                            # ShippingAddress'i al - tenant ve user kontrolü yap
                            shipping_address_query = ShippingAddress.objects.filter(
                                id=data['shipping_address_id'],
                                tenant=tenant,
                                is_deleted=False
                            )
                            
                            # Eğer tenant_user ise, sadece kendi adreslerine erişebilir
                            if request.user.is_tenant_user and request.user.tenant == tenant:
                                shipping_address_query = shipping_address_query.filter(user=request.user)
                            
                            shipping_address = shipping_address_query.first()
                            if shipping_address:
                                logger.info(f"Order için shipping_address bulundu: {shipping_address.id}")
                            else:
                                logger.warning(f"Order için shipping_address bulunamadı: {data['shipping_address_id']}")
                        except Exception as e:
                            logger.warning(f"Shipping address alınırken hata: {str(e)}")
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
                        except Exception as customer_exception:
                            logger.warning(
                                f"[ORDERS] POST /api/orders/ | Customer service error (non-critical) | "
                                f"Error: {str(customer_exception)}"
                            )
                            pass
                    
                    logger.info(
                        f"[ORDERS] POST /api/orders/ | Creating order from cart | "
                        f"Cart ID: {cart.id} | "
                        f"Customer: {data['customer_email']}"
                    )
                    
                    try:
                        # Seçili sepet kalemlerini al
                        selected_cart_item_ids = data.get('selected_cart_item_ids')
                        if selected_cart_item_ids:
                            logger.info(
                                f"[ORDERS] POST /api/orders/ | Selected cart items: {len(selected_cart_item_ids)} items"
                            )
                        
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
                            request=request,
                            selected_cart_item_ids=selected_cart_item_ids,
                            only_available_items=data.get('only_available_items', False),
                            payment_method=data.get('payment_method'),
                        )
                        
                        logger.info(
                            f"[ORDERS] POST /api/orders/ | 201 | "
                            f"Order created: {order.order_number} | "
                            f"User: {user_email} | "
                            f"Tenant: {tenant.name}"
                        )
                        return Response({
                            'success': True,
                            'message': 'Sipariş oluşturuldu.',
                            'order': OrderDetailSerializer(order).data,
                        }, status=status.HTTP_201_CREATED)
                    except ValueError as e:
                        logger.warning(
                            f"[ORDERS] POST /api/orders/ | 400 | "
                            f"Validation error: {str(e)} | "
                            f"User: {user_email} | "
                            f"Tenant: {tenant.name}"
                        )
                        return Response({
                            'success': False,
                            'message': str(e),
                            'error': str(e),
                            'error_type': 'ValidationError',
                        }, status=status.HTTP_400_BAD_REQUEST)
                    except Exception as e:
                        logger.error(
                            f"[ORDERS] POST /api/orders/ | 500 | "
                            f"Error: {str(e)} | "
                            f"User: {user_email} | "
                            f"Tenant: {tenant.name}",
                            exc_info=True
                        )
                        return Response({
                            'success': False,
                            'message': 'Sipariş oluşturulurken bir hata oluştu.',
                            'error': str(e),
                            'error_type': type(e).__name__,
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    # Serializer validation errors - zaten yukarıda loglandı
                    logger.warning(
                        f"[ORDERS] POST /api/orders/ | 400 | "
                        f"Returning validation error response | "
                        f"Errors: {validation_errors} | "
                        f"User: {user_email} | "
                        f"Tenant: {tenant.name}"
                    )
                    response = Response({
                        'success': False,
                        'message': 'Sipariş oluşturulamadı. Lütfen gönderilen verileri kontrol edin.',
                        'errors': validation_errors,
                        'error_type': 'ValidationError',
                    }, status=status.HTTP_400_BAD_REQUEST)
                    logger.info(f"[ORDERS] POST /api/orders/ | Returning response with status {response.status_code}")
                    return response
            
            except Exception as e:
                logger.error(
                    f"[ORDERS] POST /api/orders/ | 500 | "
                    f"Unexpected error: {str(e)} | "
                    f"User: {user_email} | "
                    f"Tenant: {tenant.name if tenant else 'None'}",
                    exc_info=True
                )
                return Response({
                    'success': False,
                    'message': 'Sipariş oluşturulurken beklenmeyen bir hata oluştu.',
                    'error': str(e),
                    'error_type': type(e).__name__,
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:
            # GET ve POST dışında bir method gelirse
            logger.warning(
                f"[ORDERS] {request.method} /api/orders/ | 405 | "
                f"Method not allowed | User: {user_email} | "
                f"Tenant: {tenant.name if tenant else 'None'}"
            )
            return Response({
                'success': False,
                'message': f'{request.method} method\'u bu endpoint için desteklenmiyor.',
                'error': 'Method not allowed',
                'error_type': 'MethodNotAllowed',
                'allowed_methods': ['GET', 'POST'],
            }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    except Exception as e:
        # En dış exception handler - beklenmeyen tüm hatalar
        logger.error(
            f"[ORDERS] {request.method} /api/orders/ | 500 | "
            f"Critical error: {str(e)} | "
            f"User: {user_email if 'user_email' in locals() else 'Unknown'} | "
            f"Authenticated: {request.user.is_authenticated if request.user else False}",
            exc_info=True
        )
        return Response({
            'success': False,
            'message': 'Bir hata oluştu.',
            'error': str(e),
            'error_type': type(e).__name__,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        
        # Sipariş durumu güncelleme
        new_status = request.data.get('status')
        if new_status:
            try:
                order = OrderService.update_order_status(order, new_status, request.user)
            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e),
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ödeme durumu güncelleme (SADECE havale ödemeleri için)
        new_payment_status = request.data.get('payment_status')
        if new_payment_status:
            # SADECE bank_transfer (havale) için payment_status güncellenebilir
            # Diğer ödeme yöntemleri (kredi kartı vb.) otomatik işlenir
            if order.payment_method != Order.PaymentMethod.BANK_TRANSFER:
                return Response({
                    'success': False,
                    'message': 'Ödeme durumu sadece havale/EFT ödemelerinde manuel olarak güncellenebilir.',
                    'error': f'Bu sipariş {order.get_payment_method_display()} ile ödeniyor. '
                             'Ödeme durumu otomatik olarak güncellenir.',
                    'current_payment_method': order.payment_method,
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Geçerli ödeme durumu mu kontrol et
            valid_payment_statuses = [choice[0] for choice in Order.PaymentStatus.choices]
            if new_payment_status not in valid_payment_statuses:
                return Response({
                    'success': False,
                    'message': f'Geçersiz ödeme durumu: {new_payment_status}',
                    'valid_statuses': valid_payment_statuses,
                }, status=status.HTTP_400_BAD_REQUEST)
            
            old_payment_status = order.payment_status
            order.payment_status = new_payment_status
            order.save()
            
            logger.info(
                f"Order {order.order_number} payment status changed: "
                f"{old_payment_status} -> {new_payment_status} by {request.user.email} "
                f"(Bank Transfer)"
            )
        
        # Kargo takip numarası güncelleme
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
