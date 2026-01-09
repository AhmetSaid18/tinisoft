"""
Bulk operations views - Toplu işlemler.
İkas benzeri toplu işlem sistemi.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from apps.models import Product, Category, Order
from apps.permissions import IsTenantOwnerOfObject
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_create_products(request):
    """
    Toplu ürün oluşturma.
    
    POST: /api/bulk/products/create/
    Body: [
        {
            "name": "Product 1",
            ...
        },
        {
            "name": "Product 2",
            ...
        }
    ]
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    products_data = request.data
    if not isinstance(products_data, list):
         # If not a list, maybe wrapped in a key?
        products_data = request.data.get('products', [])
    
    if not products_data or not isinstance(products_data, list):
        return Response({
            'success': False,
            'message': 'Ürün listesi gereklidir. Body: [{"name": "...", ...}, ...]',
        }, status=status.HTTP_400_BAD_REQUEST)

    created_products = []
    errors = []
    
    from apps.serializers.product import ProductDetailSerializer
    
    try:
        with transaction.atomic():
            for index, product_data in enumerate(products_data):
                serializer = ProductDetailSerializer(data=product_data, context={'request': request})
                if serializer.is_valid():
                    product = serializer.save(tenant=tenant)
                    created_products.append(serializer.data)
                else:
                    errors.append({
                        'index': index,
                        'name': product_data.get('name', 'Unknown'),
                        'errors': serializer.errors
                    })
            
            if errors:
                # If any error causes transaction rollback?
                # For bulk operations, usually we want all or nothing OR partial success.
                # Here let's go with "all or nothing" if critical, but user might prefer partial?
                # Given strict atomic block, if I raise exception, all rollback.
                # If I don't raise, valid ones are saved.
                # Let's check user intent later. For now, let's rollback if ANY error to be safe/clean?
                # Or just let valid ones pass?
                # The user usually wants "transactional" for variant groups.
                # If 1 of 3 variants fail, the group is incomplete.
                # So maybe rollback is better if errors exist?
                # But typically bulk APIs might return 207 Multi-Status.
                # Let's stick to "All or Nothing" for SAFETY if there are errors, raise exception to rollback?
                # OR return success for valid ones and errors for invalid ones.
                # transaction.atomic() rolls back on exception.
                pass 

            if errors:
                # Rollback manually if we want all-or-nothing
                raise Exception(f"{len(errors)} ürün oluşturulamadı. Detaylar: {errors}")

            logger.info(f"Bulk create: {len(created_products)} products created by {request.user.email}")
            
            return Response({
                'success': True,
                'message': f'{len(created_products)} ürün oluşturuldu.',
                'products': created_products
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Bulk create error: {e}")
        return Response({
            'success': False,
            'message': f'Oluşturma hatası: {str(e)}',
            'errors': errors if errors else str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_products(request):
    """
    Toplu ürün güncelleme.
    
    POST: /api/bulk/products/update/
    Body: {
        "product_ids": ["uuid1", "uuid2", ...],
        "updates": {
            "status": "active",
            "is_visible": true,
            "is_featured": false,
            ...
        }
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Debug: Log incoming data immediately
    logger.warning(f"Bulk update request received from {request.user.email} | Data: {request.data}")

    product_ids = request.data.get('product_ids', [])
    updates = request.data.get('updates', {})
    update_all = request.data.get('all', False)
    
    if not update_all and not product_ids:
        logger.warning(f"Bulk update failed - Missing 'product_ids' and 'all'=False. Data: {request.data}")
        return Response({
            'success': False,
            'message': 'Ürün ID\'leri gereklidir veya "all": true parametresi gönderilmelidir.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not updates:
        # Debugging: Log the request data to see what was missing or malformed
        logger.warning(
            f"Bulk update failed - Missing 'updates' field. "
            f"User: {request.user.email} | "
            f"Data keys: {list(request.data.keys())} | "
            f"Data: {request.data}"
        )
        return Response({
            'success': False,
            'message': 'Güncelleme verileri gereklidir.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # İzin verilen alanlar
    allowed_fields = [
        'status', 'is_visible', 'is_featured', 'is_new', 'is_bestseller', 'is_reviewed',
        'sort_order', 'price', 'compare_at_price',
        'track_inventory', 'inventory_quantity',
        'variant_group_sku',  # <--- Added this
    ]
    
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not filtered_updates:
        return Response({
            'success': False,
            'message': 'Geçersiz güncelleme alanları.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Ürünleri filtrele
            if update_all:
                products = Product.objects.filter(
                    tenant=tenant,
                    is_deleted=False,
                )
            else:
                products = Product.objects.filter(
                    id__in=product_ids,
                    tenant=tenant,
                    is_deleted=False,
                )
            
            updated_count = products.update(**filtered_updates)
            
            logger.info(f"Bulk update: {updated_count} products updated by {request.user.email}")
            
            return Response({
                'success': True,
                'message': f'{updated_count} ürün güncellendi.',
                'updated_count': updated_count,
            })
    except Exception as e:
        logger.error(f"Bulk update error: {e}")
        return Response({
            'success': False,
            'message': f'Güncelleme hatası: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_delete_products(request):
    """
    Toplu ürün silme (soft delete).
    
    POST: /api/bulk/products/delete/
    Body: {
        "product_ids": ["uuid1", "uuid2", ...]
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    product_ids = request.data.get('product_ids', [])
    
    if not product_ids:
        return Response({
            'success': False,
            'message': 'Ürün ID\'leri gereklidir.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            products = Product.objects.filter(
                id__in=product_ids,
                tenant=tenant,
                is_deleted=False,
            )
            
            deleted_count = 0
            for product in products:
                product.soft_delete()
                deleted_count += 1
            
            logger.info(f"Bulk delete: {deleted_count} products deleted by {request.user.email}")
            
            return Response({
                'success': True,
                'message': f'{deleted_count} ürün silindi.',
                'deleted_count': deleted_count,
            })
    except Exception as e:
        logger.error(f"Bulk delete error: {e}")
        return Response({
            'success': False,
            'message': f'Silme hatası: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_order_status(request):
    """
    Toplu sipariş durumu güncelleme.
    
    POST: /api/bulk/orders/update-status/
    Body: {
        "order_ids": ["uuid1", "uuid2", ...],
        "status": "shipped"
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    order_ids = request.data.get('order_ids', [])
    new_status = request.data.get('status')
    
    if not order_ids:
        return Response({
            'success': False,
            'message': 'Sipariş ID\'leri gereklidir.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not new_status:
        return Response({
            'success': False,
            'message': 'Yeni durum gereklidir.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Geçerli durum kontrolü
    valid_statuses = [choice[0] for choice in Order.OrderStatus.choices]
    if new_status not in valid_statuses:
        return Response({
            'success': False,
            'message': 'Geçersiz durum.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from apps.services.order_service import OrderService
        
        with transaction.atomic():
            orders = Order.objects.filter(
                id__in=order_ids,
                tenant=tenant,
                is_deleted=False,
            )
            
            updated_count = 0
            for order in orders:
                OrderService.update_order_status(order, new_status, request.user)
                updated_count += 1
            
            logger.info(f"Bulk order status update: {updated_count} orders updated by {request.user.email}")
            
            return Response({
                'success': True,
                'message': f'{updated_count} sipariş durumu güncellendi.',
                'updated_count': updated_count,
            })
    except Exception as e:
        logger.error(f"Bulk order status update error: {e}")
        return Response({
            'success': False,
            'message': f'Güncelleme hatası: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_export_products(request):
    """
    Toplu ürün export (CSV/JSON).
    
    POST: /api/bulk/products/export/
    Body: {
        "product_ids": ["uuid1", "uuid2", ...],  # Boş = tümü
        "format": "csv"  # csv veya json
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    product_ids = request.data.get('product_ids', [])
    export_format = request.data.get('format', 'json')
    
    try:
        products = Product.objects.filter(
            tenant=tenant,
            is_deleted=False,
        )
        
        if product_ids:
            products = products.filter(id__in=product_ids)
        
        # TODO: CSV/JSON export implementasyonu
        # Şimdilik sadece JSON döndür
        from apps.serializers.product import ProductListSerializer
        serializer = ProductListSerializer(products, many=True)
        
        return Response({
            'success': True,
            'message': f'{products.count()} ürün export edildi.',
            'format': export_format,
            'data': serializer.data,
        })
    except Exception as e:
        logger.error(f"Bulk export error: {e}")
        return Response({
            'success': False,
            'message': f'Export hatası: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

