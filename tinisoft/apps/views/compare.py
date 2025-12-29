"""
Product comparison views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from apps.models import ProductCompare, CompareItem, Product
from apps.serializers.compare import (
    ProductCompareSerializer, CompareItemSerializer, CompareItemCreateSerializer
)
from core.middleware import get_tenant_from_request
import logging
import uuid

logger = logging.getLogger(__name__)


def get_or_create_compare_list(request, tenant):
    """
    Kullanıcı için karşılaştırma listesini getir veya oluştur.
    Giriş yapmışsa customer'a göre, yoksa session_id'ye göre.
    """
    try:
        if request.user.is_authenticated and request.user.is_tenant_user:
            # Giriş yapmış kullanıcı
            compare_list, created = ProductCompare.objects.get_or_create(
                tenant=tenant,
                customer=request.user,
                defaults={'max_items': 4}
            )
            if created:
                logger.info(f"Compare list created for authenticated user: {request.user.email}")
            else:
                logger.debug(f"Compare list found for authenticated user: {request.user.email}")
        else:
            # Giriş yapmamış kullanıcı - session_id kullan
            # Session middleware aktif değilse, unique bir ID oluştur
            session_id = None
            if hasattr(request, 'session') and request.session:
                session_id = request.session.session_key
                if not session_id:
                    # Session yoksa oluştur
                    request.session.create()
                    session_id = request.session.session_key
                    logger.debug(f"Session created: {session_id}")
            else:
                # Session middleware yoksa, request'ten unique ID oluştur
                # IP + User-Agent kombinasyonu kullan
                import hashlib
                ip = request.META.get('REMOTE_ADDR', '')
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                session_id = hashlib.md5(f"{ip}{user_agent}".encode()).hexdigest()
                logger.debug(f"Session ID generated from IP+UA: {session_id[:8]}...")
            
            if not session_id:
                raise ValueError("Session ID oluşturulamadı.")
            
            compare_list, created = ProductCompare.objects.get_or_create(
                tenant=tenant,
                session_id=session_id,
                customer__isnull=True,
                defaults={'max_items': 4}
            )
            if created:
                logger.info(f"Compare list created for session: {session_id[:8]}...")
            else:
                logger.debug(f"Compare list found for session: {session_id[:8]}...")
        
        return compare_list
    except Exception as e:
        logger.error(f"get_or_create_compare_list error: {str(e)}", exc_info=True)
        raise


@api_view(['GET'])
@permission_classes([AllowAny])
def compare_list(request):
    """
    Karşılaştırma listesini getir.
    
    GET: /api/compare/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        compare_list = get_or_create_compare_list(request, tenant)
        serializer = ProductCompareSerializer(compare_list, context={'request': request})
        
        # Debug log
        items_count = compare_list.items.filter(is_deleted=False).count()
        logger.debug(f"Compare list retrieved: tenant={tenant.slug}, items={items_count}, user_auth={request.user.is_authenticated}")
        
        return Response({
            'success': True,
            'compare': serializer.data,
        })
    except Exception as e:
        logger.error(f"Compare list error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': 'Karşılaştırma listesi alınamadı.',
            'error': str(e),
            'error_type': type(e).__name__,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def compare_add_product(request):
    """
    Karşılaştırma listesine ürün ekle.
    
    POST: /api/compare/add/
    Body: {"product_id": "uuid"}
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = CompareItemCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    product_id = serializer.validated_data['product_id']
    
    # Ürünü kontrol et
    try:
        product = Product.objects.get(id=product_id, tenant=tenant, is_deleted=False)
    except Product.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Ürün bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        compare_list = get_or_create_compare_list(request, tenant)
        
        # Ürün ekle
        try:
            item = compare_list.add_product(product)
            serializer = CompareItemSerializer(item, context={'request': request})
            return Response({
                'success': True,
                'message': 'Ürün karşılaştırma listesine eklendi.',
                'item': serializer.data,
                'items_count': compare_list.items.filter(is_deleted=False).count(),
                'max_items': compare_list.max_items,
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Compare add product error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ürün eklenemedi.',
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE', 'POST'])
@permission_classes([AllowAny])
def compare_remove_product(request, product_id):
    """
    Karşılaştırma listesinden ürün çıkar.
    
    DELETE veya POST: /api/compare/remove/{product_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        compare_list = get_or_create_compare_list(request, tenant)
        
        # Ürünü kontrol et
        try:
            product = Product.objects.get(id=product_id, tenant=tenant, is_deleted=False)
        except Product.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Ürün bulunamadı.',
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Ürünü çıkar
        removed = compare_list.remove_product(product)
        if removed:
            return Response({
                'success': True,
                'message': 'Ürün karşılaştırma listesinden çıkarıldı.',
                'items_count': compare_list.items.filter(is_deleted=False).count(),
            })
        else:
            return Response({
                'success': False,
                'message': 'Ürün karşılaştırma listesinde bulunamadı.',
            }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Compare remove product error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ürün çıkarılamadı.',
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE', 'POST'])
@permission_classes([AllowAny])
def compare_clear(request):
    """
    Karşılaştırma listesini temizle (tüm ürünleri çıkar).
    
    DELETE veya POST: /api/compare/clear/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        compare_list = get_or_create_compare_list(request, tenant)
        compare_list.clear()
        
        return Response({
            'success': True,
            'message': 'Karşılaştırma listesi temizlendi.',
        })
    except Exception as e:
        logger.error(f"Compare clear error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Liste temizlenemedi.',
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def compare_products_detail(request):
    """
    Karşılaştırma listesindeki ürünlerin detaylı bilgilerini getir.
    Karşılaştırma sayfası için optimize edilmiş response.
    
    GET: /api/compare/products/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        compare_list = get_or_create_compare_list(request, tenant)
        items = compare_list.items.filter(is_deleted=False).order_by('position', 'created_at')
        
        # Ürün detaylarını getir
        from apps.serializers.product import ProductDetailSerializer
        products_data = []
        for item in items:
            product_data = ProductDetailSerializer(item.product, context={'request': request}).data
            products_data.append({
                'id': str(item.id),
                'position': item.position,
                'product': product_data
            })
        
        return Response({
            'success': True,
            'products': products_data,
            'count': len(products_data),
            'max_items': compare_list.max_items,
        })
    except Exception as e:
        logger.error(f"Compare products detail error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ürün bilgileri alınamadı.',
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

