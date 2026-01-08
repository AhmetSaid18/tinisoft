"""
Wishlist views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from apps.models import Wishlist, WishlistItem, Product, ProductVariant
from apps.serializers.wishlist import (
    WishlistSerializer, WishlistCreateSerializer,
    WishlistItemSerializer, WishlistItemCreateSerializer
)
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def wishlist_list_create(request):
    """
    Wishlist listesi (GET) veya yeni wishlist oluştur (POST).
    
    GET: /api/wishlists/
    POST: /api/wishlists/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece tenant user'lar wishlist oluşturabilir
    if not request.user.is_tenant_user or request.user.tenant != tenant:
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        # Kullanıcının wishlist'lerini getir
        queryset = Wishlist.objects.filter(
            tenant=tenant,
            customer=request.user,
            is_deleted=False
        )
        
        # Public wishlist'ler de görüntülenebilir
        show_public = request.query_params.get('show_public', 'false').lower() == 'true'
        if show_public:
            queryset = queryset | Wishlist.objects.filter(
                tenant=tenant,
                is_public=True,
                is_deleted=False
            )
        
        queryset = queryset.order_by('-is_default', '-created_at')
        
        serializer = WishlistSerializer(queryset, many=True)
        return Response({
            'success': True,
            'wishlists': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = WishlistCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Eğer is_default=True ise, diğer wishlist'leri is_default=False yap
            if serializer.validated_data.get('is_default', False):
                Wishlist.objects.filter(
                    tenant=tenant,
                    customer=request.user,
                    is_default=True
                ).update(is_default=False)
            
            wishlist = Wishlist.objects.create(
                tenant=tenant,
                customer=request.user,
                name=serializer.validated_data.get('name', 'Favorilerim'),
                is_default=serializer.validated_data.get('is_default', False),
                is_public=serializer.validated_data.get('is_public', False),
            )
            
            return Response({
                'success': True,
                'message': 'Wishlist oluşturuldu.',
                'wishlist': WishlistSerializer(wishlist).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def wishlist_detail(request, wishlist_id):
    """
    Wishlist detayı (GET), güncelle (PATCH) veya sil (DELETE).
    
    GET: /api/wishlists/{wishlist_id}/
    PATCH: /api/wishlists/{wishlist_id}/
    DELETE: /api/wishlists/{wishlist_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        wishlist = Wishlist.objects.get(id=wishlist_id, tenant=tenant, is_deleted=False)
    except Wishlist.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Wishlist bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece sahibi veya public ise görüntülenebilir
    if wishlist.customer != request.user and not wishlist.is_public:
        return Response({
            'success': False,
            'message': 'Bu wishlist\'e erişim yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = WishlistSerializer(wishlist)
        return Response({
            'success': True,
            'wishlist': serializer.data,
        })
    
    elif request.method == 'PATCH':
        # Sadece sahibi güncelleyebilir
        if wishlist.customer != request.user:
            return Response({
                'success': False,
                'message': 'Bu wishlist\'i güncelleme yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = WishlistCreateSerializer(wishlist, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Eğer is_default=True yapılıyorsa, diğer wishlist'leri is_default=False yap
            if serializer.validated_data.get('is_default', False):
                Wishlist.objects.filter(
                    tenant=tenant,
                    customer=request.user,
                    is_default=True
                ).exclude(id=wishlist.id).update(is_default=False)
            
            serializer.save()
            return Response({
                'success': True,
                'message': 'Wishlist güncellendi.',
                'wishlist': WishlistSerializer(wishlist).data,
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Sadece sahibi silebilir
        if wishlist.customer != request.user:
            return Response({
                'success': False,
                'message': 'Bu wishlist\'i silme yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        wishlist.soft_delete()
        return Response({
            'success': True,
            'message': 'Wishlist silindi.',
        }, status=status.HTTP_200_OK)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def wishlist_item_add_remove(request, wishlist_id):
    """
    Wishlist'e ürün ekle (POST) veya çıkar (DELETE).
    
    POST: /api/wishlists/{wishlist_id}/items/
    DELETE: /api/wishlists/{wishlist_id}/items/{item_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        wishlist = Wishlist.objects.get(id=wishlist_id, tenant=tenant, is_deleted=False)
    except Wishlist.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Wishlist bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece sahibi ekleme/çıkarma yapabilir
    if wishlist.customer != request.user:
        return Response({
            'success': False,
            'message': 'Bu wishlist\'e erişim yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'POST':
        serializer = WishlistItemCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            variant_id = serializer.validated_data.get('variant_id')
            note = serializer.validated_data.get('note', '')
            
            # Ürünü kontrol et
            try:
                product = Product.objects.get(id=product_id, tenant=tenant, is_deleted=False)
            except Product.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Ürün bulunamadı.',
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Variant kontrolü
            variant = None
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(
                        id=variant_id,
                        product=product,
                        is_deleted=False
                    )
                except ProductVariant.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Varyant bulunamadı.',
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Daha önce eklenmiş mi?
            item, created = WishlistItem.objects.get_or_create(
                wishlist=wishlist,
                product=product,
                variant=variant,
                defaults={'note': note}
            )
            
            if not created:
                return Response({
                    'success': False,
                    'message': 'Bu ürün zaten wishlist\'te.',
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'message': 'Ürün wishlist\'e eklendi.',
                'item': WishlistItemSerializer(item).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        item_id = request.query_params.get('item_id')
        product_id = request.query_params.get('product_id')
        variant_id = request.query_params.get('variant_id')
        
        if item_id:
            try:
                item = WishlistItem.objects.get(
                    id=item_id,
                    wishlist=wishlist,
                    is_deleted=False
                )
            except WishlistItem.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Wishlist kalemi bulunamadı.',
                }, status=status.HTTP_404_NOT_FOUND)
        elif product_id:
            # product_id ve opsiyonel variant_id ile bul
            q = Q(wishlist=wishlist, product_id=product_id, is_deleted=False)
            if variant_id:
                q &= Q(variant_id=variant_id)
            else:
                q &= Q(variant=None)
            
            item = WishlistItem.objects.filter(q).first()
            if not item:
                return Response({
                    'success': False,
                    'message': 'Ürün wishlist\'te bulunamadı.',
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'success': False,
                'message': 'item_id veya product_id parametresi gerekli.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        item.soft_delete()
        return Response({
            'success': True,
            'message': 'Ürün wishlist\'ten çıkarıldı.',
        }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def wishlist_item_remove_generic(request):
    """
    Kullanıcının varsayılan wishlist'inden ürün çıkar.
    Eğer varsayılan yoksa ilkini kullanır.
    
    DELETE: /api/wishlists/items/remove/
    Query Params: ?product_id=...&variant_id=...
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({'success': False, 'message': 'Tenant bulunamadı.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Varsayılan wishlist'i bul
    wishlist = Wishlist.objects.filter(
        tenant=tenant,
        customer=request.user,
        is_default=True,
        is_deleted=False
    ).first()
    
    # Yoksa ilkini al
    if not wishlist:
        wishlist = Wishlist.objects.filter(
            tenant=tenant,
            customer=request.user,
            is_deleted=False
        ).order_by('-created_at').first()
        
    if not wishlist:
        return Response({
            'success': False,
            'message': 'Wishlist bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
        
    product_id = request.query_params.get('product_id')
    variant_id = request.query_params.get('variant_id')
    
    if not product_id:
        return Response({
            'success': False,
            'message': 'product_id parametresi gerekli.',
        }, status=status.HTTP_400_BAD_REQUEST)
        
    q = Q(wishlist=wishlist, product_id=product_id, is_deleted=False)
    if variant_id:
        q &= Q(variant_id=variant_id)
    else:
        q &= Q(variant=None)
        
    item = WishlistItem.objects.filter(q).first()
    if not item:
        return Response({
            'success': False,
            'message': 'Ürün wishlist\'te bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
        
    item.soft_delete()
    return Response({
        'success': True,
        'message': 'Ürün wishlist\'ten çıkarıldı.',
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def wishlist_clear_generic(request):
    """
    Kullanıcının varsayılan wishlist'ini temizle.
    
    DELETE: /api/wishlists/clear-all/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({'success': False, 'message': 'Tenant bulunamadı.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Tüm silinmemiş wishlist'lerin item'larını mı silmek istiyor?
    # "tüm istek listesini silmeyi ekleyelim" -> muhtemelen tüm item'lar.
    
    items = WishlistItem.objects.filter(
        wishlist__tenant=tenant,
        wishlist__customer=request.user,
        is_deleted=False
    )
    
    count = items.count()
    items.update(is_deleted=True)
    
    return Response({
        'success': True,
        'message': f'İstek listesindeki {count} ürün temizlendi.',
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def wishlist_clear(request, wishlist_id):
    """
    Wishlist'i temizle (tüm ürünleri çıkar).
    
    DELETE: /api/wishlists/{wishlist_id}/clear/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        wishlist = Wishlist.objects.get(id=wishlist_id, tenant=tenant, is_deleted=False)
    except Wishlist.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Wishlist bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece sahibi temizleyebilir
    if wishlist.customer != request.user:
        return Response({
            'success': False,
            'message': 'Bu wishlist\'i temizleme yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Tüm item'ları soft delete yap
    WishlistItem.objects.filter(wishlist=wishlist, is_deleted=False).update(is_deleted=True)
    
    return Response({
        'success': True,
        'message': 'Wishlist temizlendi.',
    }, status=status.HTTP_200_OK)

