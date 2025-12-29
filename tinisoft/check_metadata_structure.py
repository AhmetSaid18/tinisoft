"""
Metadata yapısını kontrol et - image_paths dışında görsel bilgisi var mı?
"""
import os
import sys
import django
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tinisoft.settings')
django.setup()

from apps.models import Product, Tenant
from core.db_router import set_tenant_schema
from django.db import connection
import logging
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_metadata_structure(tenant_slug='avrupamutfak', sample_size=20):
    """
    Metadata yapısını kontrol et - image_paths dışında görsel bilgisi var mı?
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
    logger.info(f"İlk {sample_size} ürünün metadata yapısı inceleniyor...\n")
    
    # Metadata key'lerini topla
    all_keys = set()
    image_paths_count = Counter()
    image_name_keys = []
    
    sample_products = products[:sample_size]
    
    for idx, product in enumerate(sample_products, 1):
        metadata = product.metadata or {}
        
        # Tüm key'leri topla
        all_keys.update(metadata.keys())
        
        # image_paths kontrolü
        image_paths = metadata.get('image_paths', [])
        if isinstance(image_paths, list):
            image_paths_count[len(image_paths)] += 1
        
        # ImageName1, ImageName2 gibi key'ler var mı?
        for key in metadata.keys():
            if 'image' in key.lower() or 'name' in key.lower():
                if key not in image_name_keys:
                    image_name_keys.append(key)
    
    logger.info("="*60)
    logger.info("METADATA KEY'LERİ:")
    logger.info("="*60)
    logger.info(f"\nTüm metadata key'leri ({len(all_keys)} adet):")
    for key in sorted(all_keys):
        logger.info(f"  - {key}")
    
    logger.info(f"\nImage/Name içeren key'ler ({len(image_name_keys)} adet):")
    for key in sorted(image_name_keys):
        logger.info(f"  - {key}")
    
    logger.info("\n" + "="*60)
    logger.info("IMAGE_PATHS İSTATİSTİKLERİ:")
    logger.info("="*60)
    logger.info(f"\nİlk {sample_size} ürün için image_paths sayısı dağılımı:")
    for count, freq in sorted(image_paths_count.items()):
        logger.info(f"  {count} adet image_path: {freq} ürün")
    
    # Örnek ürünlerin metadata'sını göster
    logger.info("\n" + "="*60)
    logger.info("ÖRNEK ÜRÜNLERİN METADATA'SI:")
    logger.info("="*60)
    
    for idx, product in enumerate(sample_products[:5], 1):
        logger.info(f"\n[{idx}] {product.name}")
        logger.info(f"    Slug: {product.slug}")
        logger.info(f"    Metadata:")
        metadata = product.metadata or {}
        for key, value in sorted(metadata.items()):
            if isinstance(value, list):
                logger.info(f"      {key}: {len(value)} adet - {value[:3]}...")
            elif isinstance(value, dict):
                logger.info(f"      {key}: {json.dumps(value, ensure_ascii=False)[:100]}...")
            else:
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                logger.info(f"      {key}: {value_str}")
    
    # Tüm ürünlerde image_paths sayısını kontrol et
    logger.info("\n" + "="*60)
    logger.info("TÜM ÜRÜNLER İÇİN İSTATİSTİKLER:")
    logger.info("="*60)
    
    total_image_paths_count = Counter()
    products_with_multiple = 0
    
    for product in products:
        image_paths = product.metadata.get('image_paths', [])
        if isinstance(image_paths, list):
            count = len(image_paths)
            total_image_paths_count[count] += 1
            if count > 1:
                products_with_multiple += 1
    
    logger.info(f"\nTüm {total_products} ürün için image_paths sayısı dağılımı:")
    for count, freq in sorted(total_image_paths_count.items()):
        percentage = (freq / total_products) * 100
        logger.info(f"  {count} adet image_path: {freq} ürün ({percentage:.1f}%)")
    
    logger.info(f"\nBirden fazla image_path olan ürünler: {products_with_multiple} adet")
    
    logger.info("\n" + "="*60)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Metadata yapısını kontrol et')
    parser.add_argument('--tenant-slug', type=str, default='avrupamutfak', help='Tenant slug')
    parser.add_argument('--sample-size', type=int, default=20, help='İncelenecek örnek ürün sayısı')
    
    args = parser.parse_args()
    
    check_metadata_structure(tenant_slug=args.tenant_slug, sample_size=args.sample_size)

