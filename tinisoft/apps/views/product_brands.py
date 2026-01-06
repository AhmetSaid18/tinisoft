from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils.text import slugify
from apps.models import Brand, Product
from apps.serializers.product import BrandSerializer
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def brand_list_create(request):
    """
    Marka listesi (GET) veya yeni marka oluştur (POST).
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({'success': False, 'message': 'Tenant bulunamadı.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        brands = Brand.objects.filter(tenant=tenant)
        serializer = BrandSerializer(brands, many=True)
        return Response({
            'success': True,
            'brands': serializer.data
        })
    
    elif request.method == 'POST':
        data = request.data.copy()
        if 'slug' not in data or not data['slug']:
            data['slug'] = slugify(data.get('name', ''))
            
        serializer = BrandSerializer(data=data)
        if serializer.is_valid():
            serializer.save(tenant=tenant)
            return Response({
                'success': True,
                'message': 'Marka oluşturuldu.',
                'brand': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Marka oluşturulamadı.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def brand_detail(request, brand_id):
    """
    Marka detayı, güncelleme veya silme.
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({'success': False, 'message': 'Tenant bulunamadı.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        brand = Brand.objects.get(id=brand_id, tenant=tenant)
    except Brand.DoesNotExist:
        return Response({'success': False, 'message': 'Marka bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = BrandSerializer(brand)
        return Response({'success': True, 'brand': serializer.data})
    
    elif request.method == 'PATCH':
        serializer = BrandSerializer(brand, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Marka güncellendi.',
                'brand': serializer.data
            })
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Markaya bağlı ürünleri kontrol et? (Opsiyonel, SET_NULL yapıyoruz zaten)
        brand.delete()
        return Response({'success': True, 'message': 'Marka silindi.'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def legacy_product_brands(request):
    """
    Ürünlerdeki string brand alanlarını listele (Legacy support).
    """
    tenant = get_tenant_from_request(request)
    brands = Product.objects.filter(tenant=tenant, is_deleted=False).exclude(brand='').values_list('brand', flat=True).distinct()
    return Response({'success': True, 'brands': list(brands)})

@api_view(['GET'])
@permission_classes([AllowAny])
def brand_list_public(request, tenant_slug=None):
    """
    Public marka listesi.
    """
    from apps.models import Tenant
    tenant = None
    
    # Tenant belirleme (header veya query)
    t_slug = tenant_slug or request.headers.get('X-Tenant-Slug') or request.query_params.get('tenant_slug')
    
    if t_slug:
        tenant = Tenant.objects.filter(slug=t_slug, is_deleted=False).first()
    
    if not tenant:
        return Response({'success': False, 'message': 'Mağaza bulunamadı.'}, status=status.HTTP_400_BAD_REQUEST)
        
    brands = Brand.objects.filter(tenant=tenant, is_active=True)
    serializer = BrandSerializer(brands, many=True)
    return Response({
        'success': True,
        'brands': serializer.data
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def brand_detail_public(request, brand_slug, tenant_slug=None):
    """
    Public marka detayı (slug ile).
    """
    from apps.models import Tenant
    tenant = None
    t_slug = tenant_slug or request.headers.get('X-Tenant-Slug') or request.query_params.get('tenant_slug')
    
    if t_slug:
        tenant = Tenant.objects.filter(slug=t_slug, is_deleted=False).first()
    
    if not tenant:
        return Response({'success': False, 'message': 'Mağaza bulunamadı.'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        brand = Brand.objects.get(slug=brand_slug, tenant=tenant, is_active=True)
        serializer = BrandSerializer(brand)
        return Response({'success': True, 'brand': serializer.data})
    except Brand.DoesNotExist:
        return Response({'success': False, 'message': 'Marka bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)
