"""
ProductImage ve metadata karşılaştırması için debug script.
Bir ürün için metadata'daki image_paths ile ProductImage kayıtlarını karşılaştırır.
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tinisoft.settings')
django.setup()

from apps.models import Product, ProductImage, Tenant
from core.db_router import set_tenant_schema
from django.db import connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_product_images(product_slug=None, product_id=None, tenant_slug='avrupamutfak'):
    """
    Bir ürün için metadata ve ProductImage kayıtlarını karşılaştır.
    """
    # Tenant'ı bul
    tenant = Tenant.objects.filter(slug=tenant_slug, is_deleted=False).first()
    if not tenant:
        tenant = Tenant.objects.filter(subdomain=tenant_slug, is_deleted=False).first()
    
    if not tenant:
        logger.error(f"Tenant bulunamadı: {tenant_slug}")
        return
    
    # Schema'yı set et
    schema = f"tenant_{tenant.subdomain}"
    set_tenant_schema(schema)
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{schema}", public;')
    
    # Ürünü bul
    if product_id:
        product = Product.objects.get(id=product_id, tenant=tenant, is_deleted=False)
    elif product_slug:
        product = Product.objects.get(slug=product_slug, tenant=tenant, is_deleted=False)
    else:
        logger.error("product_slug veya product_id belirtilmeli!")
        return
    
    logger.info("="*60)
    logger.info(f"ÜRÜN: {product.name}")
    logger.info(f"Slug: {product.slug}")
    logger.info(f"ID: {product.id}")
    logger.info("="*60)
    
    # Metadata'daki image_paths
    image_paths = product.metadata.get('image_paths', [])
    logger.info(f"\nMETADATA image_paths ({len(image_paths)} adet):")
    for idx, path in enumerate(image_paths, 1):
        filename = os.path.basename(path)
        logger.info(f"  [{idx}] {path}")
        logger.info(f"      → Dosya adı: {filename}")
    
    # Mevcut ProductImage kayıtları
    existing_images = product.images.filter(is_deleted=False).order_by('position', 'created_at')
    logger.info(f"\nPRODUCTIMAGE kayıtları ({existing_images.count()} adet):")
    for idx, img in enumerate(existing_images, 1):
        filename = os.path.basename(img.image_url)
        logger.info(f"  [{idx}] {img.image_url}")
        logger.info(f"      → Dosya adı: {filename}")
        logger.info(f"      → Position: {img.position}")
        logger.info(f"      → Primary: {img.is_primary}")
        logger.info(f"      → ID: {img.id}")
    
    # Karşılaştırma
    logger.info("\n" + "="*60)
    logger.info("KARŞILAŞTIRMA:")
    logger.info("="*60)
    
    # Metadata'daki dosya adlarını çıkar
    metadata_filenames = {os.path.basename(path).lower() for path in image_paths}
    
    # ProductImage'daki dosya adlarını çıkar
    existing_filenames = {os.path.basename(img.image_url).lower() for img in existing_images}
    
    logger.info(f"\nMetadata'daki dosya adları ({len(metadata_filenames)}):")
    for fname in sorted(metadata_filenames):
        logger.info(f"  - {fname}")
    
    logger.info(f"\nProductImage'daki dosya adları ({len(existing_filenames)}):")
    for fname in sorted(existing_filenames):
        logger.info(f"  - {fname}")
    
    # Eşleşenler
    matched = metadata_filenames & existing_filenames
    logger.info(f"\n✓ Eşleşenler ({len(matched)}):")
    for fname in sorted(matched):
        logger.info(f"  - {fname}")
    
    # Metadata'da var ama ProductImage'da yok
    missing_in_db = metadata_filenames - existing_filenames
    logger.info(f"\n✗ Metadata'da var ama ProductImage'da YOK ({len(missing_in_db)}):")
    for fname in sorted(missing_in_db):
        logger.info(f"  - {fname}")
    
    # ProductImage'da var ama metadata'da yok
    extra_in_db = existing_filenames - metadata_filenames
    logger.info(f"\n⚠ ProductImage'da var ama metadata'da YOK ({len(extra_in_db)}):")
    for fname in sorted(extra_in_db):
        logger.info(f"  - {fname}")
    
    logger.info("\n" + "="*60)
    logger.info("ÖZET:")
    logger.info(f"  Metadata'da {len(image_paths)} image_path var")
    logger.info(f"  ProductImage'da {existing_images.count()} kayıt var")
    logger.info(f"  Eşleşen: {len(matched)}")
    logger.info(f"  Eksik (metadata'da var ama DB'de yok): {len(missing_in_db)}")
    logger.info(f"  Fazla (DB'de var ama metadata'da yok): {len(extra_in_db)}")
    logger.info("="*60)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='ProductImage ve metadata karşılaştırması')
    parser.add_argument('--product-slug', type=str, help='Ürün slug (örn: lavion-b8-8-litre-setustu-stand-mikser-hz-kontrollu)')
    parser.add_argument('--product-id', type=str, help='Ürün ID (UUID)')
    parser.add_argument('--tenant-slug', type=str, default='avrupamutfak', help='Tenant slug')
    
    args = parser.parse_args()
    
    if not args.product_slug and not args.product_id:
        # Örnek ürün için çalıştır
        logger.info("Ürün belirtilmedi, örnek ürün için çalıştırılıyor...")
        debug_product_images(product_slug='lavion-b8-8-litre-setustu-stand-mikser-hz-kontrollu', tenant_slug=args.tenant_slug)
    else:
        debug_product_images(
            product_slug=args.product_slug,
            product_id=args.product_id,
            tenant_slug=args.tenant_slug
        )

