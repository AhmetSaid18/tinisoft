
import os
import sys
import django
from django.db.models import Count

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tinisoft.settings')

# Celery hatasını bypass etmek için
os.environ['DJANGO_SETTINGS_MODULE'] = 'tinisoft.settings'

try:
    django.setup()
except Exception as e:
    # Celery hatası olsa bile modelleri kullanabiliriz belki
    print(f"Setup hatası (önemsiz olabilir): {e}")

from apps.models import ProductImage

def find_duplicates():
    print("Duplicate görseller aranıyor...")
    
    # URL ve Product bazlı gruplama yapıp, sayısı 1'den fazla olanları bulalım
    duplicates = ProductImage.objects.filter(is_deleted=False).values(
        'product_id', 'image_url'
    ).annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    if not duplicates.exists():
        print("✓ HİÇ DUPLICATE GÖRSEL BULUNAMADI! Veritabanı temiz.")
        return

    print(f"⚠ TOPLAM {duplicates.count()} ADET DUPLICATE GRUBU BULUNDU!\n")
    
    for item in duplicates:
        product_id = item['product_id']
        image_url = item['image_url']
        count = item['count']
        
        print(f"Ürün ID: {product_id}")
        print(f"URL: {image_url}")
        print(f"Adet: {count}")
        print("-" * 50)
        
        # Detaylı ID'leri göster
        images = ProductImage.objects.filter(
            product_id=product_id, 
            image_url=image_url, 
            is_deleted=False
        ).order_by('created_at')
        
        for img in images:
            print(f"  - ID: {img.id} | Primary: {img.is_primary} | Pos: {img.position} | Oluşturulma: {img.created_at}")
        print("\n")

if __name__ == '__main__':
    find_duplicates()
