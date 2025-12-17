"""
Bundle views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from apps.models import ProductBundle, ProductBundleItem
from apps.serializers.bundle import (
    ProductBundleSerializer, ProductBundleCreateSerializer,
    ProductBundleItemSerializer, ProductBundleItemCreateSerializer
)
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class BundlePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def bundle_list_create(request):
    """
    Bundle listesi (GET) veya yeni bundle oluştur (POST).
    
    GET: /api/bundles/
    POST: /api/bundles/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        # Bundle listesi
        queryset = ProductBundle.objects.filter(tenant=tenant, is_deleted=False)
        
        # Public endpoint için AllowAny kullanılabilir
        if request.user.is_authenticated:
            # Tenant owner/admin ise tüm bundle'ları göster
            if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
                # Tenant user ise sadece aktif bundle'ları göster
                queryset = queryset.filter(is_active=True)
        else:
            # Public erişim için sadece aktif bundle'lar
            queryset = queryset.filter(is_active=True)
        
        # Filtreleme
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        # Sıralama
        ordering = request.query_params.get('ordering', 'sort_order')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        paginator = BundlePagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = ProductBundleSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response({
                'success': True,
                'bundles': serializer.data,
            })
        
        serializer = ProductBundleSerializer(queryset, many=True, context={'request': request})
        return Response({
            'success': True,
            'bundles': serializer.data,
        })
    
    elif request.method == 'POST':
        # Sadece admin veya tenant owner
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ProductBundleCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            bundle = serializer.save(tenant=tenant)
            
            return Response({
                'success': True,
                'message': 'Bundle oluşturuldu.',
                'bundle': ProductBundleSerializer(bundle, context={'request': request}).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def bundle_detail(request, bundle_id):
    """
    Bundle detayı (GET), güncelle (PATCH) veya sil (DELETE).
    
    GET: /api/bundles/<bundle_id>/
    PATCH: /api/bundles/<bundle_id>/
    DELETE: /api/bundles/<bundle_id>/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        bundle = ProductBundle.objects.get(tenant=tenant, id=bundle_id, is_deleted=False)
    except ProductBundle.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Bundle bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ProductBundleSerializer(bundle, context={'request': request})
        return Response({
            'success': True,
            'bundle': serializer.data,
        })
    
    elif request.method == 'PATCH':
        # Sadece admin veya tenant owner
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ProductBundleCreateSerializer(bundle, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            bundle = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Bundle güncellendi.',
                'bundle': ProductBundleSerializer(bundle, context={'request': request}).data,
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Sadece admin veya tenant owner
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        bundle.is_deleted = True
        bundle.save()
        
        return Response({
            'success': True,
            'message': 'Bundle silindi.',
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bundle_item_add(request, bundle_id):
    """
    Bundle'a ürün ekle.
    
    POST: /api/bundles/<bundle_id>/items/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        bundle = ProductBundle.objects.get(tenant=tenant, id=bundle_id, is_deleted=False)
    except ProductBundle.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Bundle bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = ProductBundleItemCreateSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        # Aynı ürün/variant zaten var mı kontrol et
        product = serializer.validated_data['product']
        variant = serializer.validated_data.get('variant')
        
        if ProductBundleItem.objects.filter(
            bundle=bundle,
            product=product,
            variant=variant,
            is_deleted=False
        ).exists():
            return Response({
                'success': False,
                'message': 'Bu ürün zaten bundle\'da mevcut.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        item = serializer.save(bundle=bundle)
        
        return Response({
            'success': True,
            'message': 'Ürün bundle\'a eklendi.',
            'item': ProductBundleItemSerializer(item, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'errors': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE', 'PATCH'])
@permission_classes([IsAuthenticated])
def bundle_item_detail(request, bundle_id, item_id):
    """
    Bundle item sil (DELETE) veya güncelle (PATCH).
    
    DELETE: /api/bundles/<bundle_id>/items/<item_id>/
    PATCH: /api/bundles/<bundle_id>/items/<item_id>/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        bundle = ProductBundle.objects.get(tenant=tenant, id=bundle_id, is_deleted=False)
        item = ProductBundleItem.objects.get(bundle=bundle, id=item_id, is_deleted=False)
    except (ProductBundle.DoesNotExist, ProductBundleItem.DoesNotExist):
        return Response({
            'success': False,
            'message': 'Bundle veya item bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'DELETE':
        item.is_deleted = True
        item.save()
        
        return Response({
            'success': True,
            'message': 'Ürün bundle\'dan kaldırıldı.',
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        serializer = ProductBundleItemCreateSerializer(item, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            item = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Bundle item güncellendi.',
                'item': ProductBundleItemSerializer(item, context={'request': request}).data,
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

