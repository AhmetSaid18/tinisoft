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
    if order.shipping_address:
        shipping_address = {
            'first_name': order.shipping_address.first_name,
            'last_name': order.shipping_address.last_name,
            'phone': order.shipping_address.phone,
            'address_line_1': order.shipping_address.address_line_1,
            'address_line_2': order.shipping_address.address_line_2 or '',
            'city': order.shipping_address.city,
            'state': order.shipping_address.state or '',
            'postal_code': order.shipping_address.postal_code,
            'country': order.shipping_address.country or 'TR',
        }
    else:
        # Shipping address yoksa customer bilgilerinden oluştur
        shipping_address = {
            'first_name': order.customer_first_name,
            'last_name': order.customer_last_name,
            'phone': order.customer_phone or '',
            'address_line_1': '',
            'address_line_2': '',
            'city': '',
            'state': '',
            'postal_code': '',
            'country': 'TR',
        }
    
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

