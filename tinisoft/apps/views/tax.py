"""
Tax views - KDV/Vergi yönetimi.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.models import Tax
from apps.serializers.tax import TaxSerializer
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def tax_list_create(request):
    """
    Vergi listesi (GET) veya yeni vergi oluştur (POST).
    
    GET: /api/taxes/
    POST: /api/taxes/
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
    
    if request.method == 'GET':
        queryset = Tax.objects.filter(tenant=tenant, is_deleted=False)
        
        # Aktif/pasif filtresi
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        queryset = queryset.order_by('-is_default', 'name')
        
        serializer = TaxSerializer(queryset, many=True)
        logger.info(f"[TAX] GET /api/taxes/ | 200 | Count: {queryset.count()}")
        return Response({
            'success': True,
            'taxes': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = TaxSerializer(data=request.data)
        if serializer.is_valid():
            tax = serializer.save(tenant=tenant)
            logger.info(f"[TAX] POST /api/taxes/ | 201 | Created | Name: {tax.name}, Rate: {tax.rate}%")
            return Response({
                'success': True,
                'message': 'Vergi oluşturuldu.',
                'tax': TaxSerializer(tax).data,
            }, status=status.HTTP_201_CREATED)
        
        logger.error(f"[TAX] POST /api/taxes/ | 400 | Validation failed | Errors: {list(serializer.errors.keys())}")
        return Response({
            'success': False,
            'message': 'Vergi oluşturulamadı.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def tax_detail(request, tax_id):
    """
    Vergi detayı, güncelleme veya silme.
    
    GET: /api/taxes/{tax_id}/
    PUT/PATCH: /api/taxes/{tax_id}/
    DELETE: /api/taxes/{tax_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        tax = Tax.objects.get(id=tax_id, tenant=tenant, is_deleted=False)
    except Tax.DoesNotExist:
        logger.warning(f"[TAX] {request.method} /api/taxes/{tax_id}/ | 404 | Tax not found")
        return Response({
            'success': False,
            'message': 'Vergi bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = TaxSerializer(tax)
        logger.info(f"[TAX] GET /api/taxes/{tax_id}/ | 200 | Name: {tax.name}")
        return Response({
            'success': True,
            'tax': serializer.data,
        })
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = TaxSerializer(
            tax,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            logger.info(
                f"[TAX] {request.method} /api/taxes/{tax_id}/ | 200 | Updated | "
                f"Name: {tax.name}, Rate: {tax.rate}%, Active: {tax.is_active}"
            )
            return Response({
                'success': True,
                'message': 'Vergi güncellendi.',
                'tax': serializer.data,
            })
        
        logger.warning(f"[TAX] {request.method} /api/taxes/{tax_id}/ | 400 | Validation failed | Errors: {serializer.errors}")
        return Response({
            'success': False,
            'message': 'Vergi güncellenemedi.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        tax.soft_delete()
        logger.info(f"[TAX] DELETE /api/taxes/{tax_id}/ | 200 | Deleted | Name: {tax.name}")
        return Response({
            'success': True,
            'message': 'Vergi silindi.',
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tax_activate(request, tax_id):
    """
    Vergiyi aktif et.
    
    POST: /api/taxes/{tax_id}/activate/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        tax = Tax.objects.get(id=tax_id, tenant=tenant, is_deleted=False)
    except Tax.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Vergi bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    tax.is_active = True
    tax.save()
    
    logger.info(
        f"[TAX] POST /api/taxes/{tax_id}/activate/ | 200 | Activated | "
        f"Name: {tax.name}, Rate: {tax.rate}%"
    )
    
    return Response({
        'success': True,
        'message': 'Vergi aktif edildi. Tüm ürünlerin KDV dahil fiyatları güncelleniyor...',
        'tax': TaxSerializer(tax).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tax_deactivate(request, tax_id):
    """
    Vergiyi pasif et.
    
    POST: /api/taxes/{tax_id}/deactivate/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        tax = Tax.objects.get(id=tax_id, tenant=tenant, is_deleted=False)
    except Tax.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Vergi bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    tax.is_active = False
    tax.save()
    
    logger.info(
        f"[TAX] POST /api/taxes/{tax_id}/deactivate/ | 200 | Deactivated | "
        f"Name: {tax.name}, Rate: {tax.rate}%"
    )
    
    return Response({
        'success': True,
        'message': 'Vergi pasif edildi. Tüm ürünlerin KDV dahil fiyatları güncelleniyor...',
        'tax': TaxSerializer(tax).data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tax_active(request):
    """
    Aktif vergiyi getir.
    
    GET: /api/taxes/active/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Aktif vergiyi bul (varsayılan öncelikli)
    tax = Tax.objects.filter(
        tenant=tenant,
        is_active=True,
        is_deleted=False
    ).order_by('-is_default', '-created_at').first()
    
    if not tax:
        return Response({
            'success': True,
            'message': 'Aktif vergi bulunamadı.',
            'tax': None,
        })
    
    serializer = TaxSerializer(tax)
    return Response({
        'success': True,
        'tax': serializer.data,
    })

