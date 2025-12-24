"""
Product views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from apps.models import Product, Category
from apps.serializers.product import (
    ProductListSerializer, ProductDetailSerializer,
    CategorySerializer
)
from apps.permissions import IsTenantOwnerOfObject
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def product_list_create(request):
    """
    Ürün listesi (GET) veya yeni ürün oluştur (POST).
    
    GET: /api/products/
    POST: /api/products/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        logger.warning(f"[PRODUCTS] {request.method} /api/products/ | 400 | Tenant not found")
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        logger.warning(f"[PRODUCTS] {request.method} /api/products/ | 403 | Permission denied")
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        # Filtreleme
        queryset = Product.objects.filter(tenant=tenant, is_deleted=False)
        
        # Status filtresi
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Görünürlük filtresi
        is_visible = request.query_params.get('is_visible')
        if is_visible is not None:
            queryset = queryset.filter(is_visible=is_visible.lower() == 'true')
        
        # Kategori filtresi
        category_id = request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(categories__id=category_id)
        
        # Arama
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(sku__icontains=search)
            )
        
        # Sıralama
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        paginator = ProductPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            response = paginator.get_paginated_response(serializer.data)
            logger.info(f"[PRODUCTS] GET /api/products/ | 200 | Count: {len(page)}/{paginator.page.paginator.count}")
            return response
        
        serializer = ProductListSerializer(queryset, many=True)
        logger.info(f"[PRODUCTS] GET /api/products/ | 200 | Count: {queryset.count()}")
        return Response({
            'success': True,
            'products': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = ProductDetailSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save(tenant=tenant)
            logger.info(f"[PRODUCTS] POST /api/products/ | 201 | Created | SKU: {product.sku}")
            return Response({
                'success': True,
                'message': 'Ürün oluşturuldu.',
                'product': ProductDetailSerializer(product).data,
            }, status=status.HTTP_201_CREATED)
        logger.error(f"[PRODUCTS] POST /api/products/ | 400 | Validation failed | Errors: {list(serializer.errors.keys())}")
        return Response({
            'success': False,
            'message': 'Ürün oluşturulamadı.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def product_detail(request, product_id):
    """
    Ürün detayı, güncelleme veya silme.
    
    GET: /api/products/{product_id}/
    PUT/PATCH: /api/products/{product_id}/
    DELETE: /api/products/{product_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        product = Product.objects.get(id=product_id, tenant=tenant, is_deleted=False)
    except Product.DoesNotExist:
        logger.warning(f"[PRODUCTS] {request.method} /api/products/{product_id}/ | 404 | Product not found")
        return Response({
            'success': False,
            'message': 'Ürün bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        logger.warning(f"[PRODUCTS] {request.method} /api/products/{product_id}/ | 403 | Permission denied")
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = ProductDetailSerializer(product)
        logger.info(
            f"[PRODUCTS] GET /api/products/{product_id}/ - SUCCESS | "
            f"Tenant: {tenant.name} ({tenant.id}) | "
            f"User: {request.user.email} | "
            f"ProductID: {product.id} | "
            f"ProductName: {product.name} | "
            f"Status: {status.HTTP_200_OK}"
        )
        return Response({
            'success': True,
            'product': serializer.data,
        })
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = ProductDetailSerializer(
            product,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            logger.info(
                f"[PRODUCTS] {request.method} /api/products/{product_id}/ - SUCCESS | "
                f"Tenant: {tenant.name} ({tenant.id}) | "
                f"User: {request.user.email} | "
                f"ProductID: {product.id} | "
                f"ProductName: {product.name} | "
                f"Status: {status.HTTP_200_OK}"
            )
            return Response({
                'success': True,
                'message': 'Ürün güncellendi.',
                'product': serializer.data,
            })
        logger.warning(
            f"[PRODUCTS] {request.method} /api/products/{product_id}/ - VALIDATION ERROR | "
            f"Tenant: {tenant.name} ({tenant.id}) | "
            f"User: {request.user.email} | "
            f"ProductID: {product.id} | "
            f"Errors: {serializer.errors} | "
            f"Status: {status.HTTP_400_BAD_REQUEST}"
        )
        return Response({
            'success': False,
            'message': 'Ürün güncellenemedi.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        product.soft_delete()
        logger.info(
            f"[PRODUCTS] DELETE /api/products/{product_id}/ - SUCCESS | "
            f"Tenant: {tenant.name} ({tenant.id}) | "
            f"User: {request.user.email} | "
            f"ProductID: {product.id} | "
            f"ProductName: {product.name} | "
            f"Status: {status.HTTP_200_OK}"
        )
        return Response({
            'success': True,
            'message': 'Ürün silindi.',
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def product_list_public(request):
    """
    Public ürün listesi (frontend için).
    
    GET: /api/public/products/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    queryset = Product.objects.filter(
        tenant=tenant,
        is_deleted=False,
        status='active',
        is_visible=True,
    )
    
    # Kategori filtresi
    category_slug = request.query_params.get('category')
    if category_slug:
        queryset = queryset.filter(categories__slug=category_slug, categories__is_active=True)
    
    # Arama
    search = request.query_params.get('search')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Sıralama
    ordering = request.query_params.get('ordering', '-created_at')
    queryset = queryset.order_by(ordering)
    
    # Pagination
    paginator = ProductPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = ProductListSerializer(page, many=True)
        response = paginator.get_paginated_response(serializer.data)
        logger.info(f"[PRODUCTS] GET /api/public/products/ | 200 | Count: {len(page)}/{paginator.page.paginator.count}")
        return response
    
    serializer = ProductListSerializer(queryset, many=True)
    logger.info(f"[PRODUCTS] GET /api/public/products/ | 200 | Count: {queryset.count()}")
    return Response({
        'success': True,
        'products': serializer.data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def product_activate(request, product_id):
    """
    Ürünü aktif yap (status='active', is_visible=True).
    
    POST: /api/products/{product_id}/activate/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        product = Product.objects.get(id=product_id, tenant=tenant, is_deleted=False)
    except Product.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Ürün bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    product.status = 'active'
    product.is_visible = True
    product.save()
    
    logger.info(f"[PRODUCTS] POST /api/products/{product_id}/activate/ | 200 | Activated | SKU: {product.sku}")
    
    return Response({
        'success': True,
        'message': 'Ürün aktif edildi.',
        'product': ProductDetailSerializer(product).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def product_deactivate(request, product_id):
    """
    Ürünü pasif yap (status='archived', is_visible=False).
    
    POST: /api/products/{product_id}/deactivate/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        product = Product.objects.get(id=product_id, tenant=tenant, is_deleted=False)
    except Product.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Ürün bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    product.status = 'archived'
    product.is_visible = False
    product.save()
    
    logger.info(
        f"[PRODUCTS] POST /api/products/{product_id}/deactivate/ - SUCCESS | "
        f"Tenant: {tenant.name} ({tenant.id}) | "
        f"User: {request.user.email} | "
        f"ProductID: {product.id} | "
        f"ProductName: {product.name} | "
        f"Status: {status.HTTP_200_OK}"
    )
    
    return Response({
        'success': True,
        'message': 'Ürün pasif edildi.',
        'product': ProductDetailSerializer(product).data,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def product_detail_public(request, product_slug):
    """
    Public ürün detayı (frontend için).
    
    GET: /api/public/products/{product_slug}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        product = Product.objects.get(
            slug=product_slug,
            tenant=tenant,
            is_deleted=False,
            status='active',
            is_visible=True,
        )
    except Product.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Ürün bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Görüntüleme sayısını artır
    product.view_count += 1
    product.save(update_fields=['view_count'])
    
    serializer = ProductDetailSerializer(product)
    logger.info(
        f"[PRODUCTS] GET /api/public/products/{product_slug}/ - SUCCESS | "
        f"Tenant: {tenant.name} ({tenant.id}) | "
        f"ProductID: {product.id} | "
        f"ProductName: {product.name} | "
        f"ViewCount: {product.view_count} | "
        f"Status: {status.HTTP_200_OK}"
    )
    return Response({
        'success': True,
        'product': serializer.data,
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def category_list_create(request):
    """
    Kategori listesi (GET) veya yeni kategori oluştur (POST).
    
    GET: /api/categories/
    POST: /api/categories/
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
        queryset = Category.objects.filter(tenant=tenant, is_deleted=False, parent=None)
        serializer = CategorySerializer(queryset, many=True)
        return Response({
            'success': True,
            'categories': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save(tenant=tenant)
            return Response({
                'success': True,
                'message': 'Kategori oluşturuldu.',
                'category': CategorySerializer(category).data,
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Kategori oluşturulamadı.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

