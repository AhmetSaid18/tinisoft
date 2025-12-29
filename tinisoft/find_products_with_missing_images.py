"""
Metadata'da birden fazla image_path olan ama ProductImage'da eksik olan ürünleri bul.
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


def find_products_with_missing_images(tenant_slug='avrupamutfak', limit=10):
    """
    Metadata'da birden fazla image_path olan ama ProductImage'da eksik olan ürünleri bul.
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
    
    logger.info("="*60)
    logger.info(f"Tenant: {tenant.name} (slug: {tenant.slug})")
    logger.info("="*60)
    
    # Tüm ürünleri al
    products = Product.objects.filter(tenant=tenant, is_deleted=False)
    total_products = products.count()
    
    logger.info(f"Toplam {total_products} ürün bulundu.")
    logger.info("Metadata'da birden fazla image_path olan ürünler aranıyor...\n")
    
    products_with_missing = []
    
    for idx, product in enumerate(products, 1):
        # Metadata'dan image_paths'i al
        image_paths = product.metadata.get('image_paths', [])
        
        # Metadata'da 1'den fazla image_path yoksa atla
        if len(image_paths) <= 1:
            continue
        
        # Mevcut ProductImage kayıtlarını kontrol et
        existing_images = product.images.filter(is_deleted=False)
        existing_filenames = {os.path.basename(img.image_url).lower() for img in existing_images}
        
        # Metadata'daki dosya adlarını çıkar
        metadata_filenames = {os.path.basename(path).lower() for path in image_paths}
        
        # Eksik olanları bul
        missing_filenames = metadata_filenames - existing_filenames
        
        if missing_filenames:
            products_with_missing.append({
                'product': product,
                'metadata_count': len(image_paths),
                'existing_count': existing_images.count(),
                'missing_count': len(missing_filenames),
                'missing_filenames': missing_filenames,
                'metadata_paths': image_paths,
            })
    
    logger.info("="*60)
    logger.info(f"BULUNAN ÜRÜNLER ({len(products_with_missing)} adet):")
    logger.info("="*60)
    
    # İlk N tanesini detaylı göster
    for idx, item in enumerate(products_with_missing[:limit], 1):
        product = item['product']
        logger.info(f"\n[{idx}] {product.name}")
        logger.info(f"    Slug: {product.slug}")
        logger.info(f"    ID: {product.id}")
        logger.info(f"    Metadata'da {item['metadata_count']} image_path var")
        logger.info(f"    ProductImage'da {item['existing_count']} kayıt var")
        logger.info(f"    Eksik: {item['missing_count']} adet")
        logger.info(f"    Metadata image_paths:")
        for i, path in enumerate(item['metadata_paths'], 1):
            filename = os.path.basename(path)
            status = "✓" if filename.lower() in {os.path.basename(img.image_url).lower() for img in product.images.filter(is_deleted=False)} else "✗"
            logger.info(f"      [{i}] {status} {path}")
        logger.info(f"    Eksik dosyalar:")
        for fname in sorted(item['missing_filenames']):
            logger.info(f"      - {fname}")
    
    if len(products_with_missing) > limit:
        logger.info(f"\n... ve {len(products_with_missing) - limit} ürün daha")
    
    logger.info("\n" + "="*60)
    logger.info("ÖZET:")
    logger.info(f"  Toplam ürün: {total_products}")
    logger.info(f"  Metadata'da birden fazla image_path olan ürünler: {len(products_with_missing)}")
    logger.info(f"  Toplam eksik ProductImage kayıtları: {sum(item['missing_count'] for item in products_with_missing)}")
    logger.info("="*60)
    
    return products_with_missing


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Metadata\'da birden fazla image_path olan ama ProductImage\'da eksik olan ürünleri bul')
    parser.add_argument('--tenant-slug', type=str, default='avrupamutfak', help='Tenant slug')
    parser.add_argument('--limit', type=int, default=10, help='Gösterilecek ürün sayısı')
    
    args = parser.parse_args()
    
    find_products_with_missing_images(tenant_slug=args.tenant_slug, limit=args.limit)

