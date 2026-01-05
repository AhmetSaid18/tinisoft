import os
import sys
import django
import base64
import uuid
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tinisoft.settings')
django.setup()

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from apps.models import ProductImage

logger = logging.getLogger(__name__)

def fix_base64_images():
    """
    Veritabanında base64 olarak saklanan görselleri bulur,
    R2/Storage'a yükler ve URL ile günceller.
    """
    print("Base64 formatındaki görseller taranıyor...")
    
    # data:image ile başlayan URL'leri bul
    images = ProductImage.objects.filter(image_url__startswith='data:image')
    count = images.count()
    
    print(f"Toplam {count} adet base64 görsel bulundu.")
    
    if count == 0:
        return

    fixed_count = 0
    error_count = 0
    
    for img in images:
        try:
            image_url = img.image_url
            product = img.product
            
            print(f"İşleniyor: Image ID {img.id} (Ürün: {product.slug})")
            
            # Base64 parse
            if ';base64,' in image_url:
                format_part, imgstr = image_url.split(';base64,')
                ext = format_part.split('/')[-1]
            else:
                print(f"  ATLANDI: Format anlaşılamadı (ID: {img.id})")
                error_count += 1
                continue
                
            if ext == 'svg+xml':
                ext = 'svg'
            
            # uzantı temizliği
            if ext == 'jpeg':
                ext = 'jpg'
            
            # Decode
            try:
                data = base64.b64decode(imgstr)
            except Exception as e:
                print(f"  HATA: Base64 decode edilemedi: {e}")
                error_count += 1
                continue
            
            # Benzersiz dosya adı oluştur
            filename = f"{uuid.uuid4()}.{ext}"
            
            # Tenant bazlı klasör yapısı: {tenant_id}/products/{product_id}/{filename}
            tenant_id = str(product.tenant.id)
            file_path = f'{tenant_id}/products/{product.id}/{filename}'
            
            # Storage'a kaydet
            print(f"  Storage'a yükleniyor: {file_path}")
            saved_path = default_storage.save(file_path, ContentFile(data))
            file_url = default_storage.url(saved_path)
            
            # Update DB
            img.image_url = file_url
            img.save()
            
            print(f"  TAMAMLANDI: Yeni URL -> {file_url}")
            fixed_count += 1
            
        except Exception as e:
            print(f"  GENEL HATA (ID: {img.id}): {e}")
            error_count += 1
            
    print("-" * 50)
    print(f"İşlem bitti.")
    print(f"Başarılı: {fixed_count}")
    print(f"Hatalı: {error_count}")

if __name__ == '__main__':
    fix_base64_images()
