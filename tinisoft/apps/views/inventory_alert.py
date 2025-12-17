"""
Inventory Alert views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from apps.models import InventoryAlert
from apps.serializers.inventory_alert import InventoryAlertSerializer
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class InventoryAlertPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def inventory_alert_list_create(request):
    """
    Inventory alert listesi (GET) veya yeni alert oluştur (POST).
    
    GET: /api/inventory/alerts/
    POST: /api/inventory/alerts/
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
    
    if request.method == 'GET':
        queryset = InventoryAlert.objects.filter(tenant=tenant, is_deleted=False)
        
        # Filtreleme
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        product_id = request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        variant_id = request.query_params.get('variant_id')
        if variant_id:
            queryset = queryset.filter(variant_id=variant_id)
        
        # Sıralama
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        paginator = InventoryAlertPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = InventoryAlertSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response({
                'success': True,
                'alerts': serializer.data,
            })
        
        serializer = InventoryAlertSerializer(queryset, many=True, context={'request': request})
        return Response({
            'success': True,
            'alerts': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = InventoryAlertSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            alert = serializer.save(tenant=tenant)
            
            return Response({
                'success': True,
                'message': 'Inventory alert oluşturuldu.',
                'alert': InventoryAlertSerializer(alert, context={'request': request}).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def inventory_alert_detail(request, alert_id):
    """
    Inventory alert detayı (GET), güncelle (PATCH) veya sil (DELETE).
    
    GET: /api/inventory/alerts/<alert_id>/
    PATCH: /api/inventory/alerts/<alert_id>/
    DELETE: /api/inventory/alerts/<alert_id>/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        alert = InventoryAlert.objects.get(tenant=tenant, id=alert_id, is_deleted=False)
    except InventoryAlert.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Inventory alert bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = InventoryAlertSerializer(alert, context={'request': request})
        return Response({
            'success': True,
            'alert': serializer.data,
        })
    
    elif request.method == 'PATCH':
        serializer = InventoryAlertSerializer(alert, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            alert = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Inventory alert güncellendi.',
                'alert': InventoryAlertSerializer(alert, context={'request': request}).data,
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        alert.is_deleted = True
        alert.save()
        
        return Response({
            'success': True,
            'message': 'Inventory alert silindi.',
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def inventory_alert_check(request, alert_id):
    """
    Inventory alert kontrol et ve gerekirse bildir.
    
    POST: /api/inventory/alerts/<alert_id>/check/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        alert = InventoryAlert.objects.get(tenant=tenant, id=alert_id, is_deleted=False)
    except InventoryAlert.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Inventory alert bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    notified = alert.check_and_notify()
    
    return Response({
        'success': True,
        'message': 'Alert kontrol edildi.',
        'notified': notified,
        'alert': InventoryAlertSerializer(alert, context={'request': request}).data,
    })

