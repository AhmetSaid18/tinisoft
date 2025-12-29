"""
Metadata'daki image_paths'leri ProductImage tablosuna aktaran script.
R2'ye zaten yüklenmiş görseller için ProductImage kayıtları oluşturur.

Kullanım:
    python manage.py shell < create_product_images_from_metadata.py
    veya
    python create_product_images_from_metadata.py
"""
import os
import sys
import django
from django.conf import settings

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tinisoft.settings')
django.setup()

from apps.models import Product, ProductImage, Tenant
from core.db_router import set_tenant_schema
from django.db import connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# R2 Custom Domain (settings'ten al veya env'den)
R2_CUSTOM_DOMAIN = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None) or os.environ.get('R2_CUSTOM_DOMAIN', 'cdn.tinisoft.com.tr')


def build_r2_url(tenant_slug, image_path):
    """
    Metadata'daki image_path'den R2 URL'i oluştur.
    
    Args:
        tenant_slug: Tenant slug (örn: "avrupamutfak")
        image_path: Metadata'daki image path (örn: "resimler/lavion-b8-8-litre-setustu-stand-mikser-hiz-kontrollu-130.jpg")
    
    Returns:
        str: R2 URL (örn: "https://cdn.tinisoft.com.tr/avrupamutfak/products/lavion-b8-8-litre-setustu-stand-mikser-hiz-kontrollu-130.jpg")
    """
    # Dosya adını çıkar (path'den)
    filename = os.path.basename(image_path)
    
    # R2 URL formatı: https://{custom_domain}/{tenant_slug}/products/{filename}
    r2_url = f"https://{R2_CUSTOM_DOMAIN}/{tenant_slug}/products/{filename}"
    
    return r2_url


def create_images_from_metadata_for_tenant(tenant_slug=None, tenant_id=None, dry_run=False):
    """
    Belirli bir tenant için metadata'daki image_paths'leri ProductImage tablosuna aktar.
    
    Args:
        tenant_slug: Tenant slug (örn: "avrupamutfak")
        tenant_id: Tenant ID (UUID string)
        dry_run: True ise sadece rapor verir, kayıt oluşturmaz
    
    Returns:
        dict: İstatistikler
    """
    # Tenant'ı bul
    if tenant_id:
        tenant = Tenant.objects.get(id=tenant_id, is_deleted=False)
    elif tenant_slug:
        tenant = Tenant.objects.filter(slug=tenant_slug, is_deleted=False).first()
        if not tenant:
            tenant = Tenant.objects.filter(subdomain=tenant_slug, is_deleted=False).first()
    else:
        logger.error("tenant_slug veya tenant_id belirtilmeli!")
        return None
    
    if not tenant:
        logger.error(f"Tenant bulunamadı: slug={tenant_slug}, id={tenant_id}")
        return None
    
    logger.info(f"Tenant: {tenant.name} (slug: {tenant.slug}, id: {tenant.id})")
    
    # Schema'yı set et
    schema = f"tenant_{tenant.subdomain}"
    set_tenant_schema(schema)
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{schema}", public;')
    
    logger.info(f"Schema set to: {schema}")
    
    # Tüm ürünleri al
    products = Product.objects.filter(tenant=tenant, is_deleted=False)
    total_products = products.count()
    
    logger.info(f"Toplam {total_products} ürün bulundu.")
    logger.info("="*60)
    
    stats = {
        'total_products': total_products,
        'products_with_metadata_images': 0,
        'products_without_metadata_images': 0,
        'images_created': 0,
        'images_skipped': 0,
        'images_already_exist': 0,
        'errors': 0,
    }
    
    for idx, product in enumerate(products, 1):
        # Metadata'dan image_paths'i al
        image_paths = product.metadata.get('image_paths', [])
        
        if not image_paths:
            stats['products_without_metadata_images'] += 1
            continue
        
        stats['products_with_metadata_images'] += 1
        
        # İlk 5 ürün için detaylı log, sonra sadece özet
        detailed_log = (idx <= 5)
        
        if detailed_log:
            logger.info(f"\n[{idx}/{total_products}] Ürün: {product.name} (slug: {product.slug})")
            logger.info(f"  Metadata image_paths: {len(image_paths)} adet")
            for i, path in enumerate(image_paths[:5], 1):  # İlk 5'ini göster
                logger.info(f"    [{i}] {path}")
        
        # Mevcut ProductImage kayıtlarını kontrol et (URL'den dosya adına göre)
        existing_images = product.images.filter(is_deleted=False)
        existing_filenames = set()
        existing_urls = []
        for img in existing_images:
            filename = os.path.basename(img.image_url)
            existing_filenames.add(filename.lower())  # Case-insensitive
            existing_urls.append(img.image_url)
        
        if detailed_log:
            logger.info(f"  Mevcut ProductImage kayıtları: {existing_images.count()} adet")
            for i, url in enumerate(existing_urls[:3], 1):  # İlk 3'ünü göster
                logger.info(f"    [{i}] {url}")
        
        # Her image_path için ProductImage oluştur
        for img_idx, image_path in enumerate(image_paths):
            # Dosya adını çıkar
            filename = os.path.basename(image_path)
            
            # Bu resim zaten ProductImage'da var mı?
            if filename.lower() in existing_filenames:
                if detailed_log:
                    logger.info(f"    [{img_idx+1}/{len(image_paths)}] ✓ Zaten var: {filename}")
                stats['images_already_exist'] += 1
                continue
            
            # R2 URL'i oluştur
            r2_url = build_r2_url(tenant.slug, image_path)
            
            if detailed_log:
                logger.info(f"    [{img_idx+1}/{len(image_paths)}] {filename}")
                logger.info(f"      Metadata path: {image_path}")
                logger.info(f"      R2 URL: {r2_url}")
            
            if dry_run:
                if detailed_log:
                    logger.info(f"      [DRY RUN] ProductImage oluşturulacak")
                stats['images_created'] += 1
                continue
            
            # ProductImage oluştur
            try:
                # Position: ilk resim 0, sonraki resimler sırayla
                position = existing_images.count() + img_idx
                
                # İlk resim primary olsun (eğer hiç primary yoksa)
                is_primary = (img_idx == 0 and not existing_images.filter(is_primary=True).exists())
                
                product_image = ProductImage.objects.create(
                    product=product,
                    image_url=r2_url,
                    alt_text=product.name,
                    position=position,
                    is_primary=is_primary
                )
                
                if detailed_log:
                    logger.info(f"      ✓ ProductImage oluşturuldu (ID: {product_image.id}, position: {position}, primary: {is_primary})")
                stats['images_created'] += 1
                
                # existing_filenames'e ekle (aynı ürün içinde tekrar kontrol etmemek için)
                existing_filenames.add(filename.lower())
                
            except Exception as e:
                logger.error(f"      ✗ Hata: {str(e)}")
                if detailed_log:
                    import traceback
                    logger.error(traceback.format_exc())
                stats['errors'] += 1
        
        # Her 100 üründe bir özet göster
        if idx % 100 == 0:
            logger.info(f"\n[İlerleme] {idx}/{total_products} ürün işlendi | Oluşturulan: {stats['images_created']} | Zaten var: {stats['images_already_exist']}")
    
    logger.info("\n" + "="*60)
    logger.info("ÖZET:")
    logger.info(f"  Toplam ürün: {stats['total_products']}")
    logger.info(f"  Metadata'da image_paths olan ürünler: {stats['products_with_metadata_images']}")
    logger.info(f"  Metadata'da image_paths olmayan ürünler: {stats['products_without_metadata_images']}")
    logger.info(f"  Oluşturulan ProductImage kayıtları: {stats['images_created']}")
    logger.info(f"  Zaten var olan ProductImage kayıtları: {stats['images_already_exist']}")
    logger.info(f"  Hatalar: {stats['errors']}")
    logger.info("="*60)
    
    return stats


def create_images_for_all_tenants(dry_run=False):
    """
    Tüm tenant'lar için metadata'daki image_paths'leri ProductImage tablosuna aktar.
    """
    tenants = Tenant.objects.filter(is_deleted=False)
    total_tenants = tenants.count()
    
    logger.info(f"Toplam {total_tenants} tenant bulundu.")
    logger.info("="*60)
    
    all_stats = {
        'total_tenants': total_tenants,
        'tenants_processed': 0,
        'total_images_created': 0,
        'total_errors': 0,
    }
    
    for idx, tenant in enumerate(tenants, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"[{idx}/{total_tenants}] Tenant: {tenant.name} (slug: {tenant.slug})")
        logger.info(f"{'='*60}")
        
        stats = create_images_from_metadata_for_tenant(
            tenant_slug=tenant.slug,
            dry_run=dry_run
        )
        
        if stats:
            all_stats['tenants_processed'] += 1
            all_stats['total_images_created'] += stats['images_created']
            all_stats['total_errors'] += stats['errors']
    
    logger.info("\n" + "="*60)
    logger.info("GENEL ÖZET:")
    logger.info(f"  İşlenen tenant sayısı: {all_stats['tenants_processed']}/{all_stats['total_tenants']}")
    logger.info(f"  Toplam oluşturulan ProductImage: {all_stats['total_images_created']}")
    logger.info(f"  Toplam hata: {all_stats['total_errors']}")
    logger.info("="*60)
    
    return all_stats


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Metadata\'daki image_paths\'leri ProductImage tablosuna aktar')
    parser.add_argument('--tenant-slug', type=str, help='Belirli bir tenant için çalıştır (örn: avrupamutfak)')
    parser.add_argument('--tenant-id', type=str, help='Belirli bir tenant ID için çalıştır')
    parser.add_argument('--all-tenants', action='store_true', help='Tüm tenant\'lar için çalıştır')
    parser.add_argument('--dry-run', action='store_true', help='Sadece rapor ver, kayıt oluşturma')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("="*60)
        logger.info("DRY RUN MODE - Kayıt oluşturulmayacak!")
        logger.info("="*60)
    
    if args.all_tenants:
        create_images_for_all_tenants(dry_run=args.dry_run)
    elif args.tenant_slug:
        create_images_from_metadata_for_tenant(tenant_slug=args.tenant_slug, dry_run=args.dry_run)
    elif args.tenant_id:
        create_images_from_metadata_for_tenant(tenant_id=args.tenant_id, dry_run=args.dry_run)
    else:
        # Default: avrupamutfak için çalıştır
        logger.info("Tenant belirtilmedi, default olarak 'avrupamutfak' için çalıştırılıyor...")
        create_images_from_metadata_for_tenant(tenant_slug='avrupamutfak', dry_run=args.dry_run)

