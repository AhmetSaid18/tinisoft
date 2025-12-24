"""
Product Image Upload views - Toplu görsel yükleme.
Fotoğraf adından ürün slug'ını çıkarıp eşleştirme yapar.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.utils.text import slugify
from apps.models import Product, ProductImage
from core.middleware import get_tenant_from_request
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Maksimum görsel sayısı
MAX_IMAGES_PER_PRODUCT = 10


def extract_product_slug_from_filename(filename):
    """
    Dosya adından ürün slug'ını çıkar.
    
    Örnek:
    - animo-combi-line-cb-1x5-l-silindirik-filtre-kahve-makinesi-5-l-5256.jpg
    -> animo-combi-line-cb-1x5-l-silindirik-filtre-kahve-makinesi-5-l-5256
    
    - animo-combi-line-cb-1x5-l-silindirik-filtre-kahve-makinesi-5-l-5256-1.jpg
    -> animo-combi-line-cb-1x5-l-silindirik-filtre-kahve-makinesi-5-l-5256
    """
    # Dosya uzantısını kaldır
    name_without_ext = Path(filename).stem
    
    # Sonundaki sayıları kaldır (örn: -1, -2, -01, vb.)
    # Ama sadece sonunda ise
    import re
    # Sonundaki -sayı veya -0sayı formatını kaldır
    name_without_ext = re.sub(r'-\d+$', '', name_without_ext)
    
    return name_without_ext


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_product_image_by_slug(request):
    """
    Ürün slug'ı ile görsel yükle.
    
    POST: /api/products/images/upload/
    Content-Type: multipart/form-data
    Body: {
        "file": <image_file>,
        "product_slug": "urun-slug"  // Opsiyonel, yoksa dosya adından çıkarılır
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece tenant owner veya admin
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if 'file' not in request.FILES:
        return Response({
            'success': False,
            'message': 'Görsel dosyası yüklenmedi.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    image_file = request.FILES['file']
    product_slug = request.data.get('product_slug')
    
    # Dosya adından slug çıkar (eğer product_slug verilmemişse)
    if not product_slug:
        product_slug = extract_product_slug_from_filename(image_file.name)
    
    try:
        # Ürünü bul
        product = Product.objects.get(
            tenant=tenant,
            slug=product_slug,
            is_deleted=False
        )
    except Product.DoesNotExist:
        return Response({
            'success': False,
            'message': f'Ürün bulunamadı: {product_slug}',
            'suggested_slug': product_slug,
        }, status=status.HTTP_404_NOT_FOUND)
    except Product.MultipleObjectsReturned:
        return Response({
            'success': False,
            'message': f'Birden fazla ürün bulundu: {product_slug}',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Maksimum görsel sayısı kontrolü
    existing_images_count = product.images.filter(is_deleted=False).count()
    if existing_images_count >= MAX_IMAGES_PER_PRODUCT:
        return Response({
            'success': False,
            'message': f'Ürün için maksimum {MAX_IMAGES_PER_PRODUCT} görsel yüklenebilir.',
            'current_count': existing_images_count,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Dosyayı kaydet
        file_path = f'products/{product.id}/{image_file.name}'
        saved_path = default_storage.save(file_path, image_file)
        file_url = default_storage.url(saved_path)
        
        # ProductImage oluştur
        # Position: mevcut görsellerin sayısı (0-based)
        position = existing_images_count
        is_primary = (position == 0)  # İlk görsel primary
        
        product_image = ProductImage.objects.create(
            product=product,
            image_url=file_url,
            alt_text=product.name,
            position=position,
            is_primary=is_primary
        )
        
        return Response({
            'success': True,
            'message': 'Görsel başarıyla yüklendi.',
            'image': {
                'id': str(product_image.id),
                'image_url': product_image.image_url,
                'position': product_image.position,
                'is_primary': product_image.is_primary,
            },
            'product': {
                'id': str(product.id),
                'name': product.name,
                'slug': product.slug,
                'total_images': product.images.filter(is_deleted=False).count(),
            }
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Image upload error: {str(e)}")
        return Response({
            'success': False,
            'message': f'Görsel yükleme hatası: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def bulk_upload_product_images(request):
    """
    Toplu görsel yükleme - Birden fazla görsel yükle.
    Dosya adlarından ürün slug'larını otomatik çıkarır.
    
    POST: /api/products/images/bulk-upload/
    Content-Type: multipart/form-data
    Body: {
        "files": [<image_file1>, <image_file2>, ...]  // Çoklu dosya
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece tenant owner veya admin
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if 'files' not in request.FILES:
        return Response({
            'success': False,
            'message': 'Görsel dosyaları yüklenmedi.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    files = request.FILES.getlist('files')
    
    if not files:
        return Response({
            'success': False,
            'message': 'Görsel dosyası bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    results = {
        'success_count': 0,
        'failed_count': 0,
        'success': [],
        'failed': [],
    }
    
    for image_file in files:
        try:
            # Dosya adından slug çıkar
            product_slug = extract_product_slug_from_filename(image_file.name)
            
            # Ürünü bul
            try:
                product = Product.objects.get(
                    tenant=tenant,
                    slug=product_slug,
                    is_deleted=False
                )
            except Product.DoesNotExist:
                results['failed_count'] += 1
                results['failed'].append({
                    'filename': image_file.name,
                    'error': f'Ürün bulunamadı: {product_slug}',
                    'suggested_slug': product_slug,
                })
                continue
            except Product.MultipleObjectsReturned:
                results['failed_count'] += 1
                results['failed'].append({
                    'filename': image_file.name,
                    'error': f'Birden fazla ürün bulundu: {product_slug}',
                })
                continue
            
            # Maksimum görsel sayısı kontrolü
            existing_images_count = product.images.filter(is_deleted=False).count()
            if existing_images_count >= MAX_IMAGES_PER_PRODUCT:
                results['failed_count'] += 1
                results['failed'].append({
                    'filename': image_file.name,
                    'product_slug': product_slug,
                    'error': f'Maksimum {MAX_IMAGES_PER_PRODUCT} görsel limiti aşıldı',
                })
                continue
            
            # Dosyayı kaydet
            file_path = f'products/{product.id}/{image_file.name}'
            saved_path = default_storage.save(file_path, image_file)
            file_url = default_storage.url(saved_path)
            
            # ProductImage oluştur
            position = existing_images_count
            is_primary = (position == 0)
            
            product_image = ProductImage.objects.create(
                product=product,
                image_url=file_url,
                alt_text=product.name,
                position=position,
                is_primary=is_primary
            )
            
            results['success_count'] += 1
            results['success'].append({
                'filename': image_file.name,
                'product_slug': product_slug,
                'product_name': product.name,
                'image_url': product_image.image_url,
                'position': product_image.position,
            })
        
        except Exception as e:
            logger.error(f"Bulk image upload error for {image_file.name}: {str(e)}")
            results['failed_count'] += 1
            results['failed'].append({
                'filename': image_file.name,
                'error': str(e),
            })
    
    return Response({
        'success': True,
        'message': f'{results["success_count"]} görsel başarıyla yüklendi, {results["failed_count"]} görsel yüklenemedi.',
        'results': results,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_product_image_by_sku(request):
    """
    SKU ile görsel yükle (alternatif yöntem).
    
    POST: /api/products/images/upload-by-sku/
    Content-Type: multipart/form-data
    Body: {
        "file": <image_file>,
        "sku": "SKU-001"  // Opsiyonel, yoksa dosya adından çıkarılır
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece tenant owner veya admin
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if 'file' not in request.FILES:
        return Response({
            'success': False,
            'message': 'Görsel dosyası yüklenmedi.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    image_file = request.FILES['file']
    sku = request.data.get('sku')
    
    if not sku:
        return Response({
            'success': False,
            'message': 'SKU gereklidir.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Ürünü SKU ile bul
        product = Product.objects.get(
            tenant=tenant,
            sku=sku,
            is_deleted=False
        )
    except Product.DoesNotExist:
        return Response({
            'success': False,
            'message': f'SKU ile ürün bulunamadı: {sku}',
        }, status=status.HTTP_404_NOT_FOUND)
    except Product.MultipleObjectsReturned:
        return Response({
            'success': False,
            'message': f'Birden fazla ürün bulundu (SKU: {sku})',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Maksimum görsel sayısı kontrolü
    existing_images_count = product.images.filter(is_deleted=False).count()
    if existing_images_count >= MAX_IMAGES_PER_PRODUCT:
        return Response({
            'success': False,
            'message': f'Ürün için maksimum {MAX_IMAGES_PER_PRODUCT} görsel yüklenebilir.',
            'current_count': existing_images_count,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Dosyayı kaydet
        file_path = f'products/{product.id}/{image_file.name}'
        saved_path = default_storage.save(file_path, image_file)
        file_url = default_storage.url(saved_path)
        
        # ProductImage oluştur
        position = existing_images_count
        is_primary = (position == 0)
        
        product_image = ProductImage.objects.create(
            product=product,
            image_url=file_url,
            alt_text=product.name,
            position=position,
            is_primary=is_primary
        )
        
        return Response({
            'success': True,
            'message': 'Görsel başarıyla yüklendi.',
            'image': {
                'id': str(product_image.id),
                'image_url': product_image.image_url,
                'position': product_image.position,
                'is_primary': product_image.is_primary,
            },
            'product': {
                'id': str(product.id),
                'name': product.name,
                'sku': product.sku,
                'total_images': product.images.filter(is_deleted=False).count(),
            }
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Image upload error: {str(e)}")
        return Response({
            'success': False,
            'message': f'Görsel yükleme hatası: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

