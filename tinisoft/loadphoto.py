"""
Ürün görsellerini indirip Cloudflare R2'ye yükleyen script.
Tek seferlik kullanım için.
"""
import os
import sys
import django
import requests
from io import BytesIO
from django.conf import settings

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tinisoft.settings')
django.setup()

from apps.models import Product, ProductImage
from django.conf import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upload_to_r2(image_url, filename=None):
    """
    URL'den resim indirip Cloudflare R2'ye yükle.
    """
    import boto3
    from botocore.config import Config
    
    # R2 credentials
    access_key_id = os.environ.get('R2_ACCESS_KEY_ID', '')
    secret_access_key = os.environ.get('R2_SECRET_ACCESS_KEY', '')
    bucket_name = os.environ.get('R2_BUCKET_NAME', '')
    endpoint_url = os.environ.get('R2_ENDPOINT_URL', '')
    
    if not all([access_key_id, secret_access_key, bucket_name, endpoint_url]):
        logger.error("R2 credentials not configured!")
        logger.error("Set R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_ENDPOINT_URL in .env")
        return None
    
    try:
        # 1. Resmi indir
        logger.info(f"Downloading: {image_url}")
        response = requests.get(image_url, timeout=30, stream=True)
        response.raise_for_status()
        
        # 2. Dosya adını belirle
        if not filename:
            filename = os.path.basename(image_url.split('?')[0])
            if not filename or '.' not in filename:
                filename = 'image.jpg'
        
        # 3. R2'ye yükle (products/ klasörüne)
        r2_path = f"products/{filename}"
        
        # S3-compatible client oluştur
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(signature_version='s3v4')
        )
        
        logger.info(f"Uploading to R2: {r2_path}")
        
        # Resmi direkt stream olarak yükle
        s3_client.upload_fileobj(
            response.raw,
            bucket_name,
            r2_path,
            ExtraArgs={
                'ContentType': response.headers.get('Content-Type', 'image/jpeg'),
                'CacheControl': 'max-age=31536000'  # 1 yıl cache
            }
        )
        
        # Public URL oluştur
        # Custom domain varsa onu kullan, yoksa endpoint URL'i kullan
        custom_domain = os.environ.get('R2_CUSTOM_DOMAIN', '')
        if custom_domain:
            cloudflare_url = f"https://{custom_domain}/{r2_path}"
        else:
            # Endpoint URL'den custom domain çıkar (eğer varsa)
            # Yoksa direkt endpoint kullan
            cloudflare_url = f"{endpoint_url}/{bucket_name}/{r2_path}"
        
        logger.info(f"✓ Uploaded: {cloudflare_url}")
        return cloudflare_url
    
    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")
        return None


def migrate_product_images(product_id=None, product_slug=None):
    """
    Belirli bir ürünün görsellerini Cloudflare'e yükle.
    
    Args:
        product_id: Ürün UUID (opsiyonel)
        product_slug: Ürün slug (opsiyonel)
    """
    # Ürünü bul
    if product_id:
        try:
            product = Product.objects.get(id=product_id, is_deleted=False)
        except Product.DoesNotExist:
            logger.error(f"Ürün bulunamadı: ID={product_id}")
            return
    elif product_slug:
        try:
            product = Product.objects.get(slug=product_slug, is_deleted=False)
        except Product.DoesNotExist:
            logger.error(f"Ürün bulunamadı: slug={product_slug}")
            return
    else:
        logger.error("product_id veya product_slug belirtilmeli!")
        return
    
    logger.info(f"Ürün: {product.name} (ID: {product.id}, Slug: {product.slug})")
    logger.info(f"Tenant: {product.tenant.name}")
    
    # Ürünün görsellerini al
    images = product.images.filter(is_deleted=False)
    
    if not images.exists():
        logger.info("  → Görsel yok!")
        return
    
    logger.info(f"  → {images.count()} görsel bulundu")
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    for idx, image in enumerate(images, 1):
        logger.info(f"\n  [{idx}/{images.count()}] Görsel: {image.image_url}")
        
        # Eğer zaten Cloudflare URL'i ise atla
        if 'cloudflare' in image.image_url.lower() or 'imagedelivery.net' in image.image_url:
            logger.info(f"    → Zaten Cloudflare'de, atlanıyor")
            skip_count += 1
            continue
        
        # WooCommerce URL'i ise yükle
        logger.info(f"    → İndiriliyor ve yükleniyor...")
        cloudflare_url = upload_to_cloudflare_images(image.image_url)
        
        if cloudflare_url:
            # URL'i güncelle
            old_url = image.image_url
            image.image_url = cloudflare_url
            image.save()
            logger.info(f"    ✓ Güncellendi!")
            logger.info(f"       Eski: {old_url}")
            logger.info(f"       Yeni: {cloudflare_url}")
            success_count += 1
        else:
            logger.error(f"    ✗ Yüklenemedi!")
            fail_count += 1
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Özet:")
    logger.info(f"  ✓ Başarılı: {success_count}")
    logger.info(f"  ✗ Başarısız: {fail_count}")
    logger.info(f"  ⊘ Atlanan: {skip_count}")
    logger.info(f"{'='*50}")


def migrate_all_images():
    """
    Tüm ürün görsellerini Cloudflare'e yükle.
    """
    # Tüm ürünleri al
    products = Product.objects.filter(is_deleted=False)
    total_products = products.count()
    
    logger.info(f"Toplam {total_products} ürün bulundu.")
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    for idx, product in enumerate(products, 1):
        logger.info(f"\n[{idx}/{total_products}] Ürün: {product.name} (ID: {product.id})")
        
        # Ürünün görsellerini al
        images = product.images.filter(is_deleted=False)
        
        if not images.exists():
            logger.info("  → Görsel yok, atlanıyor")
            skip_count += 1
            continue
        
        for image in images:
            # Eğer zaten Cloudflare URL'i ise atla
            if 'cloudflare' in image.image_url.lower() or 'imagedelivery.net' in image.image_url:
                logger.info(f"  → Zaten Cloudflare'de: {image.image_url}")
                continue
            
            # URL'i R2'ye yükle
            logger.info(f"  → Eski URL: {image.image_url}")
            cloudflare_url = upload_to_r2(image.image_url)
            
            if cloudflare_url:
                # URL'i güncelle
                image.image_url = cloudflare_url
                image.save()
                logger.info(f"  ✓ Güncellendi: {cloudflare_url}")
                success_count += 1
            else:
                logger.error(f"  ✗ Yüklenemedi: {image.image_url}")
                fail_count += 1
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Özet:")
    logger.info(f"  ✓ Başarılı: {success_count}")
    logger.info(f"  ✗ Başarısız: {fail_count}")
    logger.info(f"  ⊘ Atlanan: {skip_count}")
    logger.info(f"{'='*50}")


def test_random_product():
    """
    Random bir ürün seç, görsellerini Cloudflare'e yükle ve güncelle.
    """
    import random
    
    # Cloudflare içermeyen görseli olan ürünleri bul
    products_with_images = Product.objects.filter(
        is_deleted=False,
        images__is_deleted=False
    ).exclude(
        images__image_url__icontains='cloudflare'
    ).exclude(
        images__image_url__icontains='imagedelivery.net'
    ).distinct()
    
    if not products_with_images.exists():
        logger.error("Cloudflare dışı görseli olan ürün bulunamadı!")
        logger.info("Tüm görseller zaten Cloudflare'de olabilir.")
        return
    
    # Random bir ürün seç
    product = random.choice(products_with_images)
    
    logger.info("="*50)
    logger.info("RANDOM ÜRÜN TEST")
    logger.info("="*50)
    logger.info(f"Seçilen ürün: {product.name}")
    logger.info(f"ID: {product.id}")
    logger.info(f"Slug: {product.slug}")
    logger.info(f"Tenant: {product.tenant.name}")
    logger.info("="*50)
    logger.info("")
    
    # Ürünün Cloudflare dışı görsellerini bul
    images_to_migrate = product.images.filter(
        is_deleted=False
    ).exclude(
        image_url__icontains='cloudflare'
    ).exclude(
        image_url__icontains='imagedelivery.net'
    )
    
    if not images_to_migrate.exists():
        logger.error("Bu ürünün Cloudflare dışı görseli yok!")
        return
    
    logger.info(f"{images_to_migrate.count()} görsel bulundu.")
    logger.info("")
    
    success_count = 0
    fail_count = 0
    
    for idx, image in enumerate(images_to_migrate, 1):
        logger.info(f"[{idx}/{images_to_migrate.count()}] Görsel işleniyor...")
        logger.info(f"  URL: {image.image_url}")
        
        cloudflare_url = upload_to_r2(image.image_url)
        
        if cloudflare_url:
            old_url = image.image_url
            image.image_url = cloudflare_url
            image.save()
            logger.info(f"  ✓ Başarılı!")
            logger.info(f"    Eski: {old_url[:80]}...")
            logger.info(f"    Yeni: {cloudflare_url}")
            success_count += 1
        else:
            logger.error(f"  ✗ Başarısız!")
            fail_count += 1
        logger.info("")
    
    logger.info("="*50)
    logger.info(f"Özet: ✓ {success_count} | ✗ {fail_count}")
    logger.info("="*50)


if __name__ == '__main__':
    print("="*50)
    print("WooCommerce → Cloudflare Images Migration")
    print("="*50)
    print()
    
    # DB bağlantısını test et
    try:
        from apps.models import Product
        product_count = Product.objects.count()
        print(f"✓ DB bağlantısı başarılı! ({product_count} ürün bulundu)")
    except Exception as e:
        print(f"✗ DB bağlantı hatası: {str(e)}")
        print()
        print(".env dosyasında DB ayarlarını kontrol et:")
        print("DB_HOST=your-remote-db-host")
        print("DB_NAME=your-db-name")
        print("DB_USER=your-db-user")
        print("DB_PASSWORD=your-db-password")
        sys.exit(1)
    
    print()
    
    # R2 credentials kontrolü
    access_key_id = os.environ.get('R2_ACCESS_KEY_ID', '')
    secret_access_key = os.environ.get('R2_SECRET_ACCESS_KEY', '')
    bucket_name = os.environ.get('R2_BUCKET_NAME', '')
    endpoint_url = os.environ.get('R2_ENDPOINT_URL', '')
    
    if not all([access_key_id, secret_access_key, bucket_name, endpoint_url]):
        print("HATA: R2 credentials bulunamadı!")
        print()
        print(".env dosyasında şunlar olmalı:")
        print("R2_ACCESS_KEY_ID=...")
        print("R2_SECRET_ACCESS_KEY=...")
        print("R2_BUCKET_NAME=...")
        print("R2_ENDPOINT_URL=...")
        sys.exit(1)
    
    print("✓ R2 credentials bulundu.")
    print()
    
    # Random ürün test
    print("Random bir ürün seçilip test edilecek...")
    print()
    test_random_product()
    print()
    print("Tamamlandı!")

