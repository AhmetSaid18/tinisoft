"""
Product Image Delete views - Ürün resimlerini silme.
Hard delete - R2'den de siler.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.models import Product, ProductImage
from apps.permissions import IsTenantOwnerOfObject
from core.middleware import get_tenant_from_request
import logging
import os
import boto3
from botocore.config import Config
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def delete_from_r2(image_url):
    """
    R2'den görseli sil.
    
    Args:
        image_url: Silinecek görsel URL'i
        
    Returns:
        bool: Başarılı ise True, değilse False
    """
    try:
        # R2 credentials
        access_key_id = os.environ.get('R2_ACCESS_KEY_ID', '')
        secret_access_key = os.environ.get('R2_SECRET_ACCESS_KEY', '')
        bucket_name = os.environ.get('R2_BUCKET_NAME', '')
        endpoint_url = os.environ.get('R2_ENDPOINT_URL', '')
        custom_domain = os.environ.get('R2_CUSTOM_DOMAIN', '')
        
        if not all([access_key_id, secret_access_key, bucket_name, endpoint_url]):
            logger.warning("R2 credentials not configured, skipping R2 deletion")
            return False
        
        # URL'den dosya yolunu çıkar
        # Örnek: https://cdn.tinisoft.com.tr/tenant-slug/products/image.jpg
        # veya: https://endpoint-url/bucket-name/tenant-slug/products/image.jpg
        parsed_url = urlparse(image_url)
        path = parsed_url.path.lstrip('/')
        
        # Eğer custom domain kullanılıyorsa, path direkt dosya yolu
        # Değilse, bucket name'i path'den çıkar
        if custom_domain and custom_domain in image_url:
            # Custom domain kullanılıyor, path direkt dosya yolu
            r2_key = path
        else:
            # Endpoint URL kullanılıyor, bucket name'i çıkar
            # Örnek: bucket-name/tenant-slug/products/image.jpg -> tenant-slug/products/image.jpg
            parts = path.split('/', 1)
            if len(parts) > 1:
                r2_key = parts[1]
            else:
                r2_key = path
        
        logger.info(f"Deleting from R2: {r2_key}")
        
        # S3-compatible client oluştur
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(signature_version='s3v4')
        )
        
        # R2'den sil
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=r2_key
        )
        
        logger.info(f"✓ Deleted from R2: {r2_key}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error deleting from R2: {str(e)}")
        return False


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_product_image(request, product_id, image_id):
    """
    Ürüne ait bir görseli sil (hard delete - R2'den de siler).
    
    DELETE: /api/products/{product_id}/images/{image_id}/
    
    Response:
    {
        "message": "Görsel başarıyla silindi",
        "deleted_image_id": "uuid",
        "deleted_from_r2": true
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response(
            {'error': 'Tenant bilgisi bulunamadı'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Ürünü bul
        product = Product.objects.get(
            id=product_id,
            tenant=tenant,
            is_deleted=False
        )
    except Product.DoesNotExist:
        return Response(
            {'error': 'Ürün bulunamadı'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Permission check - sadece ürünün sahibi silebilir
    permission = IsTenantOwnerOfObject()
    if not permission.has_object_permission(request, None, product):
        return Response(
            {'error': 'Bu işlem için yetkiniz yok'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Görseli bul
        product_image = ProductImage.objects.get(
            id=image_id,
            product=product,
            is_deleted=False
        )
    except ProductImage.DoesNotExist:
        return Response(
            {'error': 'Görsel bulunamadı'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # R2'den sil
    image_url = product_image.image_url
    was_primary = product_image.is_primary
    deleted_from_r2 = delete_from_r2(image_url)
    
    # DB'den hard delete
    product_image.delete()
    
    logger.info(f"Product image {image_id} HARD DELETED for product {product_id} by tenant {tenant.slug}")
    
    # Eğer silinen görsel primary ise, başka bir görseli primary yap
    if was_primary:
        remaining_images = ProductImage.objects.filter(
            product=product,
            is_deleted=False
        ).order_by('position', 'created_at')
        
        if remaining_images.exists():
            first_image = remaining_images.first()
            first_image.is_primary = True
            first_image.save()
            logger.info(f"New primary image set: {first_image.id}")
    
    return Response({
        'message': 'Görsel başarıyla silindi',
        'deleted_image_id': str(image_id),
        'deleted_from_r2': deleted_from_r2
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def bulk_delete_product_images(request, product_id):
    """
    Ürüne ait birden fazla görseli toplu sil (hard delete - R2'den de siler).
    
    DELETE: /api/products/{product_id}/images/bulk-delete/
    Body: {
        "image_ids": ["uuid1", "uuid2", "uuid3"]
    }
    
    Response:
    {
        "message": "3 görsel başarıyla silindi",
        "deleted_count": 3,
        "deleted_image_ids": ["uuid1", "uuid2", "uuid3"],
        "r2_deleted_count": 3
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response(
            {'error': 'Tenant bilgisi bulunamadı'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Ürünü bul
        product = Product.objects.get(
            id=product_id,
            tenant=tenant,
            is_deleted=False
        )
    except Product.DoesNotExist:
        return Response(
            {'error': 'Ürün bulunamadı'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Permission check - sadece ürünün sahibi silebilir
    permission = IsTenantOwnerOfObject()
    if not permission.has_object_permission(request, None, product):
        return Response(
            {'error': 'Bu işlem için yetkiniz yok'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Request body'den image_ids al
    image_ids = request.data.get('image_ids', [])
    
    if not image_ids:
        return Response(
            {'error': 'image_ids listesi boş olamaz'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not isinstance(image_ids, list):
        return Response(
            {'error': 'image_ids bir liste olmalıdır'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Görselleri bul
    images_to_delete = ProductImage.objects.filter(
        id__in=image_ids,
        product=product,
        is_deleted=False
    )
    
    if not images_to_delete.exists():
        return Response(
            {'error': 'Silinecek görsel bulunamadı'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Primary görsel var mı kontrol et
    has_primary = images_to_delete.filter(is_primary=True).exists()
    
    # Görselleri sil (R2'den ve DB'den)
    deleted_ids = []
    r2_deleted_count = 0
    
    for image in images_to_delete:
        # R2'den sil
        if delete_from_r2(image.image_url):
            r2_deleted_count += 1
        
        deleted_ids.append(str(image.id))
        
        # DB'den hard delete
        image.delete()
    
    deleted_count = len(deleted_ids)
    
    logger.info(f"{deleted_count} product images HARD DELETED for product {product_id} by tenant {tenant.slug}")
    logger.info(f"{r2_deleted_count} images deleted from R2")
    
    # Eğer primary görsel silindiyse, başka bir görseli primary yap
    if has_primary:
        remaining_images = ProductImage.objects.filter(
            product=product,
            is_deleted=False
        ).order_by('position', 'created_at')
        
        if remaining_images.exists():
            first_image = remaining_images.first()
            first_image.is_primary = True
            first_image.save()
            logger.info(f"New primary image set: {first_image.id}")
    
    return Response({
        'message': f'{deleted_count} görsel başarıyla silindi',
        'deleted_count': deleted_count,
        'deleted_image_ids': deleted_ids,
        'r2_deleted_count': r2_deleted_count
    }, status=status.HTTP_200_OK)
