"""
WooCommerce'den ürün görsellerini indirip Cloudflare Images'e yükleyen script.
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


def upload_to_cloudflare_images(image_url, filename=None):
    """
    URL'den resim indirip Cloudflare Images'e yükle.
    """
    account_id = getattr(settings, 'CLOUDFLARE_ACCOUNT_ID', '')
    api_token = getattr(settings, 'CLOUDFLARE_IMAGES_API_TOKEN', '')
    
    if not account_id or not api_token:
        logger.error("Cloudflare Images API credentials not configured!")
        logger.error("Set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_IMAGES_API_TOKEN in .env")
        return None
    
    base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v1"
    
    try:
        # 1. Resmi indir
        logger.info(f"Downloading: {image_url}")
        response = requests.get(image_url, timeout=30, stream=True)
        response.raise_for_status()
        
        # 2. Resmi BytesIO'ya yükle
        image_data = BytesIO()
        for chunk in response.iter_content(chunk_size=8192):
            image_data.write(chunk)
        image_data.seek(0)
        
        # 3. Dosya adını belirle
        if not filename:
            filename = os.path.basename(image_url.split('?')[0])
            if not filename or '.' not in filename:
                filename = 'image.jpg'
        
        # 4. Cloudflare Images API'ye yükle
        files = {
            'file': (filename, image_data, response.headers.get('Content-Type', 'image/jpeg'))
        }
        
        headers = {
            'Authorization': f'Bearer {api_token}'
        }
        
        logger.info(f"Uploading to Cloudflare: {filename}")
        upload_response = requests.post(
            base_url,
            files=files,
            headers=headers,
            timeout=60
        )
        
        if upload_response.status_code == 200:
            data = upload_response.json()
            if data.get('success'):
                result = data.get('result', {})
                variants = result.get('variants', [])
                cloudflare_url = variants[0] if variants else result.get('filename', '')
                logger.info(f"✓ Uploaded: {cloudflare_url}")
                return cloudflare_url
            else:
                error_msg = data.get('errors', [{}])[0].get('message', 'Upload failed')
                logger.error(f"✗ Upload failed: {error_msg}")
                return None
        else:
            logger.error(f"✗ HTTP {upload_response.status_code}: {upload_response.text}")
            return None
    
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
            
            # WooCommerce URL'i ise yükle
            logger.info(f"  → Eski URL: {image.image_url}")
            cloudflare_url = upload_to_cloudflare_images(image.image_url)
            
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
        
        cloudflare_url = upload_to_cloudflare_images(image.image_url)
        
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
    
    # Cloudflare credentials kontrolü
    account_id = getattr(settings, 'CLOUDFLARE_ACCOUNT_ID', '')
    api_token = getattr(settings, 'CLOUDFLARE_IMAGES_API_TOKEN', '')
    
    if not account_id or not api_token:
        print("HATA: Cloudflare Images API credentials bulunamadı!")
        print()
        print(".env dosyasına şunları ekle:")
        print("CLOUDFLARE_ACCOUNT_ID=your-account-id")
        print("CLOUDFLARE_IMAGES_API_TOKEN=your-api-token")
        print()
        print("Cloudflare Dashboard → Images → API Token oluştur")
        sys.exit(1)
    
    print("✓ Cloudflare credentials bulundu.")
    print()
    
    # Random ürün test
    print("Random bir ürün seçilip test edilecek...")
    print()
    test_random_product()
    print()
    print("Tamamlandı!")

