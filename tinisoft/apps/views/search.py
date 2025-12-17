"""
Search views - Arama ve filtreleme.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from apps.serializers.product import ProductListSerializer
from apps.services.search_service import SearchService
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class SearchPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([AllowAny])
def search_products(request):
    """
    Ürün arama ve filtreleme.
    
    GET: /api/search/products/
    Query params:
        - q: Arama sorgusu
        - category_id: Kategori ID
        - category_slug: Kategori slug
        - min_price: Minimum fiyat
        - max_price: Maximum fiyat
        - in_stock: Stokta var mı? (true/false)
        - attributes: JSON string (örn: {"color": ["red", "blue"], "size": ["m"]})
        - tags: Etiketler (virgülle ayrılmış)
        - collections: Koleksiyonlar (virgülle ayrılmış)
        - is_featured: Öne çıkan (true/false)
        - is_new: Yeni (true/false)
        - is_bestseller: Çok satan (true/false)
        - ordering: Sıralama (price_asc, price_desc, newest, popularity, name_asc, name_desc)
        - page: Sayfa numarası
        - page_size: Sayfa boyutu
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Arama sorgusu
    query = request.query_params.get('q', '').strip()
    
    # Filtreler
    filters = {}
    
    category_id = request.query_params.get('category_id')
    if category_id:
        filters['category_id'] = category_id
    
    category_slug = request.query_params.get('category_slug')
    if category_slug:
        filters['category_slug'] = category_slug
    
    min_price = request.query_params.get('min_price')
    if min_price:
        try:
            filters['min_price'] = float(min_price)
        except ValueError:
            pass
    
    max_price = request.query_params.get('max_price')
    if max_price:
        try:
            filters['max_price'] = float(max_price)
        except ValueError:
            pass
    
    in_stock = request.query_params.get('in_stock')
    if in_stock:
        filters['in_stock'] = in_stock.lower() == 'true'
    
    # Attributes (JSON string)
    attributes_str = request.query_params.get('attributes')
    if attributes_str:
        try:
            import json
            filters['attributes'] = json.loads(attributes_str)
        except:
            pass
    
    tags = request.query_params.get('tags')
    if tags:
        filters['tags'] = [tag.strip() for tag in tags.split(',')]
    
    collections = request.query_params.get('collections')
    if collections:
        filters['collections'] = [col.strip() for col in collections.split(',')]
    
    is_featured = request.query_params.get('is_featured')
    if is_featured:
        filters['is_featured'] = is_featured.lower() == 'true'
    
    is_new = request.query_params.get('is_new')
    if is_new:
        filters['is_new'] = is_new.lower() == 'true'
    
    is_bestseller = request.query_params.get('is_bestseller')
    if is_bestseller:
        filters['is_bestseller'] = is_bestseller.lower() == 'true'
    
    # Sıralama
    ordering = request.query_params.get('ordering', 'newest')
    
    # Arama
    try:
        products = SearchService.search_products(
            tenant=tenant,
            query=query,
            filters=filters,
            ordering=ordering,
        )
        
        # Pagination
        paginator = SearchPagination()
        page = paginator.paginate_queryset(products, request)
        
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True)
        return Response({
            'success': True,
            'query': query,
            'filters': filters,
            'count': products.count(),
            'products': serializer.data,
        })
    except Exception as e:
        logger.error(f"Search error: {e}")
        return Response({
            'success': False,
            'message': f'Arama hatası: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_suggestions(request):
    """
    Arama önerileri.
    
    GET: /api/search/suggestions/
    Query params:
        - q: Arama sorgusu
        - limit: Öneri limiti (default: 5)
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    query = request.query_params.get('q', '').strip()
    limit = int(request.query_params.get('limit', 5))
    
    if not query:
        return Response({
            'success': True,
            'suggestions': [],
        })
    
    try:
        suggestions = SearchService.get_search_suggestions(
            tenant=tenant,
            query=query,
            limit=limit,
        )
        
        return Response({
            'success': True,
            'query': query,
            'suggestions': suggestions,
        })
    except Exception as e:
        logger.error(f"Search suggestions error: {e}")
        return Response({
            'success': False,
            'message': f'Öneri hatası: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def filter_options(request):
    """
    Filtreleme seçeneklerini getir.
    
    GET: /api/search/filter-options/
    Query params:
        - category_id: Kategori ID (opsiyonel)
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    category_id = request.query_params.get('category_id')
    
    try:
        options = SearchService.get_filter_options(
            tenant=tenant,
            category_id=category_id,
        )
        
        return Response({
            'success': True,
            'options': options,
        })
    except Exception as e:
        logger.error(f"Filter options error: {e}")
        return Response({
            'success': False,
            'message': f'Filtre seçenekleri hatası: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

