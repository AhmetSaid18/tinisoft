"""
Inventory views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from apps.models import InventoryMovement
from apps.serializers.inventory import InventoryMovementSerializer, CreateInventoryMovementSerializer
from apps.services.inventory_service import InventoryService
from apps.permissions import IsTenantOwnerOfObject, HasStaffPermission
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class InventoryMovementPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasStaffPermission])
def inventory_movement_list_create(request):
    """
    Stok hareketi listesi (GET) veya yeni stok hareketi oluştur (POST).
    
    GET: /api/inventory/movements/
    POST: /api/inventory/movements/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Permission kontrolü
    if not (request.user.is_owner or ((request.user.is_tenant_owner or request.user.is_tenant_staff) and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        queryset = InventoryMovement.objects.filter(tenant=tenant, is_deleted=False)
        
        # Ürün filtresi
        product_id = request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Varyant filtresi
        variant_id = request.query_params.get('variant_id')
        if variant_id:
            queryset = queryset.filter(variant_id=variant_id)
        
        # Hareket tipi filtresi
        movement_type = request.query_params.get('movement_type')
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
        
        # Sipariş filtresi
        order_id = request.query_params.get('order_id')
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        
        queryset = queryset.order_by('-created_at')
        
        # Pagination
        paginator = InventoryMovementPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = InventoryMovementSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = InventoryMovementSerializer(queryset, many=True)
        return Response({
            'success': True,
            'movements': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = CreateInventoryMovementSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            try:
                movement = InventoryService.adjust_inventory(
                    tenant=tenant,
                    product_id=data.get('product_id'),
                    variant_id=data.get('variant_id'),
                    movement_type=data['movement_type'],
                    quantity=data['quantity'],
                    reason=data.get('reason', ''),
                    notes=data.get('notes', ''),
                    created_by=request.user,
                )
                
                # Activity Log
                from apps.services.activity_log_service import ActivityLogService
                ActivityLogService.log(
                    tenant=tenant,
                    user=request.user,
                    action="inventory_adjustment",
                    description=f"Stok güncellemesi yapıldı: {movement.product.name} ({movement.get_movement_type_display()}: {movement.quantity})",
                    content_type="InventoryMovement",
                    object_id=movement.id,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                return Response({
                    'success': True,
                    'message': 'Stok hareketi oluşturuldu.',
                    'movement': InventoryMovementSerializer(movement).data,
                }, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e),
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'message': 'Stok hareketi oluşturulamadı.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated, HasStaffPermission])
def inventory_movement_detail(request, movement_id):
    """
    Stok hareketi detayı.
    
    GET: /api/inventory/movements/{movement_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        movement = InventoryMovement.objects.get(id=movement_id, tenant=tenant, is_deleted=False)
    except InventoryMovement.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Stok hareketi bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Permission kontrolü
    if not (request.user.is_owner or ((request.user.is_tenant_owner or request.user.is_tenant_staff) and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = InventoryMovementSerializer(movement)
    return Response({
        'success': True,
        'movement': serializer.data,
    })


# Set staff permissions
inventory_movement_list_create.staff_permission = 'inventory'
inventory_movement_detail.staff_permission = 'inventory'
