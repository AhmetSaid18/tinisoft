from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.db.models import Q
from apps.models import Product, Category, Tenant
from apps.serializers.storefront_product import ProductStorefrontListSerializer, ProductStorefrontDetailSerializer
import logging

logger = logging.getLogger(__name__)

class StorefrontPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'pageSize'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response({
            'items': data,
            'totalCount': self.page.paginator.count,
            'page': self.page.number,
            'pageSize': self.get_page_size(self.request),
            'displayCurrency': 'TRY' # TODO: Make dynamic based on tenant currency
        })

def get_tenant_from_request_or_header(request):
    # Try header first (Standard for API)
    tenant_id = request.headers.get('X-Tenant-Id') or request.headers.get('X-Tenant-ID')
    tenant_slug_header = request.headers.get('X-Tenant-Slug')
    
    tenant = None
    if tenant_id:
        try:
            tenant = Tenant.objects.get(id=tenant_id, is_deleted=False)
        except Tenant.DoesNotExist:
            pass
            
    if not tenant and tenant_slug_header:
        try:
            tenant = Tenant.objects.get(slug=tenant_slug_header, is_deleted=False)
        except Tenant.DoesNotExist:
            pass
            
    # If not in header, try query param (e.g. debugging)
    if not tenant:
        t_slug = request.query_params.get('tenant_slug')
        if t_slug:
            try:
                tenant = Tenant.objects.get(slug=t_slug, is_deleted=False)
            except Tenant.DoesNotExist:
                pass

    return tenant

@api_view(['GET'])
@permission_classes([AllowAny])
def storefront_product_list(request):
    """
    GET /api/storefront/products
    """
    tenant = get_tenant_from_request_or_header(request)
    if not tenant:
        return Response({'message': 'Tenant header (X-Tenant-Id) required'}, status=400)

    queryset = Product.objects.filter(
        tenant=tenant, 
        is_deleted=False, 
        status='active', 
        is_visible=True
    )

    # 1. Search
    search_query = request.query_params.get('search')
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(sku__icontains=search_query)
        )

    # 2. Category Filter
    category_id = request.query_params.get('categoryId')
    if category_id:
        # Include subcategories logic? For now strict match or recursive if needed
        # Assuming simple ID match first
        queryset = queryset.filter(categories__id=category_id)

    # 3. Sort
    sort_param = request.query_params.get('sort')
    if sort_param:
        if sort_param == 'price-asc':
            queryset = queryset.order_by('price')
        elif sort_param == 'price-desc':
            queryset = queryset.order_by('-price')
        elif sort_param == 'created-desc':
            queryset = queryset.order_by('-created_at')
        elif sort_param == 'created-asc':
            queryset = queryset.order_by('created_at')
    else:
        queryset = queryset.order_by('-created_at')

    # Pagination
    paginator = StorefrontPagination()
    page = paginator.paginate_queryset(queryset, request)
    if page is not None:
        serializer = ProductStorefrontListSerializer(page, many=True)
        # Update displayCurrency based on tenant
        response = paginator.get_paginated_response(serializer.data)
        response.data['displayCurrency'] = tenant.currency or 'TRY'
        return response

    serializer = ProductStorefrontListSerializer(queryset, many=True)
    return Response({
        'items': serializer.data,
        'totalCount': queryset.count(),
        'page': 1,
        'pageSize': queryset.count(),
        'displayCurrency': tenant.currency or 'TRY'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def storefront_product_detail(request, id):
    """
    GET /api/storefront/products/{id}
    """
    tenant = get_tenant_from_request_or_header(request)
    if not tenant:
        return Response({'message': 'Tenant header (X-Tenant-Id) required'}, status=400)

    try:
        # Try finding by ID first
        product = Product.objects.get(id=id, tenant=tenant, is_deleted=False)
    except (Product.DoesNotExist, ValueError): # ValueError in case id is not UUID
        # Try finding by slug if ID failed (fallback logic)
        try:
             product = Product.objects.get(slug=id, tenant=tenant, is_deleted=False)
        except Product.DoesNotExist:
            return Response({'message': 'Product not found'}, status=404)

    if not product.is_visible or product.status != 'active':
         return Response({'message': 'Product not found'}, status=404)

    product.view_count += 1
    product.save(update_fields=['view_count'])

    serializer = ProductStorefrontDetailSerializer(product)
    return Response(serializer.data)
