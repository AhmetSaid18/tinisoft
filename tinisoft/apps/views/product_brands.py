from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.models import Product
from core.middleware import get_tenant_from_request

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def product_brands(request):
    """
    Mevcut markaları listele (dropdown için).
    
    GET: /api/products/brands/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.'
        }, status=400)
        
    # Sadece silinmemiş ve markası olan ürünlerden markaları çek
    brands = Product.objects.filter(
        tenant=tenant, 
        is_deleted=False
    ).exclude(
        brand__isnull=True
    ).exclude(
        brand=''
    ).values_list('brand', flat=True).distinct().order_by('brand')
    
    return Response({
        'success': True,
        'brands': list(brands)
    })
