"""
Aras Kargo API endpoints.
Integration modelinden API bilgilerini alır ve kullanır.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.models import Order, IntegrationProvider
from apps.services.aras_cargo_service import ArasCargoService
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aras_create_shipment(request, order_id):
    """
    Gönderi oluştur (Aras Kargo).
    
    POST: /api/orders/{order_id}/aras/create-shipment/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece tenant owner veya owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        order = Order.objects.get(id=order_id, tenant=tenant, is_deleted=False)
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Sipariş bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Kargo adresi bilgilerini hazırla
    shipping_address = {}
    addr = None
    
    # Önce order'ın shipping_address'ini kontrol et
    if order.shipping_address:
        addr = order.shipping_address
        logger.info(f"Order shipping_address kullanılıyor: {addr.id}")
    elif order.customer:
        # Order'da shipping_address yoksa ama customer varsa, customer'ın default address'ini kullan
        from apps.models import ShippingAddress
        try:
            addr = ShippingAddress.objects.filter(
                tenant=tenant,
                user=order.customer,
                is_default=True,
                is_deleted=False
            ).first()
            if addr:
                logger.info(f"Order'da shipping_address yok, customer'ın default address'i kullanılıyor: {addr.id}")
        except Exception as e:
            logger.warning(f"Customer default address alınamadı: {str(e)}")
    
    if addr:
        # ShippingAddress modelinden al
        shipping_address = {
            'first_name': addr.first_name or order.customer_first_name or '',
            'last_name': addr.last_name or order.customer_last_name or '',
            'phone': addr.phone or order.customer_phone or '',
            'address_line_1': addr.address_line_1 or '',
            'address_line_2': addr.address_line_2 or '',
            'city': addr.city or '',
            'state': addr.state or '',
            'postal_code': addr.postal_code or '',
            'country': addr.country or 'TR',
        }
        logger.info(f"Shipping address: address_line_1={shipping_address.get('address_line_1')}, city={shipping_address.get('city')}")
    else:
        # Shipping address yoksa customer bilgilerinden oluştur
        shipping_address = {
            'first_name': order.customer_first_name or '',
            'last_name': order.customer_last_name or '',
            'phone': order.customer_phone or '',
            'address_line_1': '',
            'address_line_2': '',
            'city': '',
            'state': '',
            'postal_code': '',
            'country': 'TR',
        }
        logger.warning(f"Order {order.id} için shipping_address bulunamadı, customer bilgilerinden oluşturuldu.")
    
    # Adres bilgileri kontrolü
    if not shipping_address.get('address_line_1') or not shipping_address.get('city'):
        logger.error(f"Order {order.id} için eksik adres bilgisi: address_line_1={shipping_address.get('address_line_1')}, city={shipping_address.get('city')}")
        return Response({
            'success': False,
            'message': 'Sipariş için kargo adresi eksik veya geçersiz. Lütfen sipariş adres bilgilerini kontrol edin.',
            'details': {
                'has_shipping_address': order.shipping_address is not None,
                'address_line_1': shipping_address.get('address_line_1'),
                'city': shipping_address.get('city'),
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Gönderi oluştur
    result = ArasCargoService.create_shipment(tenant, order, shipping_address)
    
    if result.get('success'):
        # Takip numarasını siparişe kaydet
        tracking_number = result.get('tracking_number', '')
        if tracking_number:
            order.tracking_number = tracking_number
            order.status = Order.OrderStatus.SHIPPED
            if not order.shipped_at:
                from django.utils import timezone
                order.shipped_at = timezone.now()
            order.save()
        
        return Response({
            'success': True,
            'message': 'Gönderi oluşturuldu.',
            'tracking_number': tracking_number,
            'label_url': result.get('label_url', ''),
            'order': {
                'id': str(order.id),
                'order_number': order.order_number,
                'tracking_number': tracking_number,
                'status': order.status,
            }
        }, status=status.HTTP_201_CREATED)
    else:
        return Response({
            'success': False,
            'message': result.get('error', 'Gönderi oluşturulamadı.'),
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def aras_track_shipment(request, tracking_number):
    """
    Gönderi takip (Aras Kargo).
    
    GET: /api/aras/track/{tracking_number}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece tenant owner veya owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    result = ArasCargoService.track_shipment(tenant, tracking_number)
    
    if result.get('success'):
        return Response({
            'success': True,
            'tracking_number': tracking_number,
            'status': result.get('status', ''),
            'events': result.get('events', []),
            'data': result.get('data', {}),
        })
    else:
        return Response({
            'success': False,
            'message': result.get('error', 'Takip bilgisi alınamadı.'),
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def aras_print_label(request, tracking_number):
    """
    Kargo etiketi yazdır (Aras Kargo).
    
    GET: /api/aras/label/{tracking_number}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece tenant owner veya owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    result = ArasCargoService.print_label(tenant, tracking_number)
    
    if result.get('success'):
        label_url = result.get('label_url', '')
        label_pdf = result.get('label_pdf', b'')
        
        # PDF varsa direkt döndür
        if label_pdf:
            from django.http import HttpResponse
            response = HttpResponse(label_pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="label_{tracking_number}.pdf"'
            return response
        
        # URL varsa döndür
        return Response({
            'success': True,
            'tracking_number': tracking_number,
            'label_url': label_url,
        })
    else:
        return Response({
            'success': False,
            'message': result.get('error', 'Etiket alınamadı.'),
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aras_cancel_shipment(request, tracking_number):
    """
    Gönderi iptal et (Aras Kargo).
    
    POST: /api/aras/cancel/{tracking_number}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece tenant owner veya owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    result = ArasCargoService.cancel_shipment(tenant, tracking_number)
    
    if result.get('success'):
        return Response({
            'success': True,
            'message': result.get('message', 'Gönderi iptal edildi.'),
        })
    else:
        return Response({
            'success': False,
            'message': result.get('error', 'Gönderi iptal edilemedi.'),
        }, status=status.HTTP_400_BAD_REQUEST)

