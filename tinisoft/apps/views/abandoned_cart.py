"""
Abandoned Cart views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from apps.models import AbandonedCart, Cart, Order
from apps.serializers.abandoned_cart import AbandonedCartSerializer
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class AbandonedCartPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def abandoned_cart_list(request):
    """
    Abandoned cart listesi.
    
    GET: /api/abandoned-carts/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    queryset = AbandonedCart.objects.filter(tenant=tenant)
    
    # Filtreleme
    is_recovered = request.query_params.get('is_recovered')
    if is_recovered is not None:
        queryset = queryset.filter(is_recovered=is_recovered.lower() == 'true')
    
    is_ignored = request.query_params.get('is_ignored')
    if is_ignored is not None:
        queryset = queryset.filter(is_ignored=is_ignored.lower() == 'true')
    
    email = request.query_params.get('email')
    if email:
        queryset = queryset.filter(customer_email__icontains=email)
    
    # Sıralama
    ordering = request.query_params.get('ordering', '-abandoned_at')
    queryset = queryset.order_by(ordering)
    
    # Pagination
    paginator = AbandonedCartPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = AbandonedCartSerializer(page, many=True)
        return paginator.get_paginated_response({
            'success': True,
            'abandoned_carts': serializer.data,
        })
    
    serializer = AbandonedCartSerializer(queryset, many=True)
    return Response({
        'success': True,
        'abandoned_carts': serializer.data,
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def abandoned_cart_detail(request, abandoned_cart_id):
    """
    Abandoned cart detayı (GET) veya güncelle (PATCH).
    
    GET: /api/abandoned-carts/<abandoned_cart_id>/
    PATCH: /api/abandoned-carts/<abandoned_cart_id>/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        abandoned_cart = AbandonedCart.objects.get(tenant=tenant, id=abandoned_cart_id)
    except AbandonedCart.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Abandoned cart bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = AbandonedCartSerializer(abandoned_cart)
        return Response({
            'success': True,
            'abandoned_cart': serializer.data,
        })
    
    elif request.method == 'PATCH':
        # Sadece admin veya tenant owner
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AbandonedCartSerializer(abandoned_cart, data=request.data, partial=True)
        
        if serializer.is_valid():
            abandoned_cart = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Abandoned cart güncellendi.',
                'abandoned_cart': AbandonedCartSerializer(abandoned_cart).data,
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def abandoned_cart_recover(request, abandoned_cart_id):
    """
    Abandoned cart'ı recover et (siparişe dönüştür).
    
    POST: /api/abandoned-carts/<abandoned_cart_id>/recover/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        abandoned_cart = AbandonedCart.objects.get(tenant=tenant, id=abandoned_cart_id)
    except AbandonedCart.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Abandoned cart bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if abandoned_cart.is_recovered:
        return Response({
            'success': False,
            'message': 'Bu cart zaten recover edilmiş.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Cart'ı recover et
    abandoned_cart.is_recovered = True
    abandoned_cart.recovered_at = timezone.now()
    abandoned_cart.save()
    
    return Response({
        'success': True,
        'message': 'Abandoned cart recover edildi.',
        'abandoned_cart': AbandonedCartSerializer(abandoned_cart).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def abandoned_cart_send_reminder(request, abandoned_cart_id):
    """
    Abandoned cart için reminder e-postası gönder.
    
    POST: /api/abandoned-carts/<abandoned_cart_id>/send-reminder/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        abandoned_cart = AbandonedCart.objects.get(tenant=tenant, id=abandoned_cart_id)
    except AbandonedCart.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Abandoned cart bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if abandoned_cart.is_recovered or abandoned_cart.is_ignored:
        return Response({
            'success': False,
            'message': 'Bu cart için reminder gönderilemez.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # E-posta gönderim sayısını artır
    abandoned_cart.email_sent_count += 1
    if abandoned_cart.first_email_sent_at is None:
        abandoned_cart.first_email_sent_at = timezone.now()
    abandoned_cart.last_email_sent_at = timezone.now()
    abandoned_cart.save()
    
    # TODO: Burada gerçek e-posta gönderim servisi entegre edilebilir
    # Örnek: send_abandoned_cart_email(abandoned_cart)
    
    return Response({
        'success': True,
        'message': 'Reminder e-postası gönderildi.',
        'abandoned_cart': AbandonedCartSerializer(abandoned_cart).data,
    })

