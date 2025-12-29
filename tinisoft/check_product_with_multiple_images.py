"""
Metadata'da birden fazla image_path olan bir ürünü detaylı kontrol et.
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


def check_product_with_multiple_images(tenant_slug='avrupamutfak'):
    """
    Metadata'da birden fazla image_path olan bir ürünü bul ve detaylı kontrol et.
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
    
    # Metadata'da birden fazla image_path olan bir ürün bul
    products = Product.objects.filter(tenant=tenant, is_deleted=False)
    
    for product in products:
        image_paths = product.metadata.get('image_paths', [])
        if len(image_paths) > 1:
            # Bu ürünü detaylı kontrol et
            logger.info("="*60)
            logger.info(f"ÜRÜN: {product.name}")
            logger.info(f"Slug: {product.slug}")
            logger.info(f"ID: {product.id}")
            logger.info("="*60)
            
            logger.info(f"\nMETADATA image_paths ({len(image_paths)} adet):")
            for idx, path in enumerate(image_paths, 1):
                filename = os.path.basename(path)
                logger.info(f"  [{idx}] {path}")
                logger.info(f"      → Dosya adı: {filename}")
            
            # ProductImage kayıtları
            existing_images = product.images.filter(is_deleted=False).order_by('position', 'created_at')
            logger.info(f"\nPRODUCTIMAGE kayıtları ({existing_images.count()} adet):")
            for idx, img in enumerate(existing_images, 1):
                filename = os.path.basename(img.image_url)
                logger.info(f"  [{idx}] {img.image_url}")
                logger.info(f"      → Dosya adı: {filename}")
                logger.info(f"      → Position: {img.position}")
                logger.info(f"      → Primary: {img.is_primary}")
                logger.info(f"      → ID: {img.id}")
                logger.info(f"      → Created: {img.created_at}")
            
            # Karşılaştırma
            logger.info("\n" + "="*60)
            logger.info("KARŞILAŞTIRMA:")
            logger.info("="*60)
            
            metadata_filenames = {os.path.basename(path).lower() for path in image_paths}
            existing_filenames = {os.path.basename(img.image_url).lower() for img in existing_images}
            
            matched = metadata_filenames & existing_filenames
            missing = metadata_filenames - existing_filenames
            extra = existing_filenames - metadata_filenames
            
            logger.info(f"\n✓ Eşleşenler ({len(matched)}):")
            for fname in sorted(matched):
                logger.info(f"  - {fname}")
            
            logger.info(f"\n✗ Metadata'da var ama ProductImage'da YOK ({len(missing)}):")
            for fname in sorted(missing):
                logger.info(f"  - {fname}")
            
            logger.info(f"\n⚠ ProductImage'da var ama metadata'da YOK ({len(extra)}):")
            for fname in sorted(extra):
                logger.info(f"  - {fname}")
            
            logger.info("\n" + "="*60)
            logger.info("ÖZET:")
            logger.info(f"  Metadata'da {len(image_paths)} image_path var")
            logger.info(f"  ProductImage'da {existing_images.count()} kayıt var")
            logger.info(f"  Eşleşen: {len(matched)}")
            logger.info(f"  Eksik (metadata'da var ama DB'de yok): {len(missing)}")
            logger.info(f"  Fazla (DB'de var ama metadata'da yok): {len(extra)}")
            logger.info("="*60)
            
            # Eğer eksik varsa, bu ürünü göster ve dur
            if missing:
                logger.info("\n⚠ Bu ürün için eksik ProductImage kayıtları var!")
                return product
            
            # İlk bulunan ürünü göster (eşleşen olsa bile)
            break
    
    return None


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Metadata\'da birden fazla image_path olan bir ürünü kontrol et')
    parser.add_argument('--tenant-slug', type=str, default='avrupamutfak', help='Tenant slug')
    
    args = parser.parse_args()
    
    check_product_with_multiple_images(tenant_slug=args.tenant_slug)

