import os
import django
import sys
from django.utils.text import slugify

# Django ortamını ayarla
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tinisoft.settings')
django.setup()

from apps.models import Product, Brand, Tenant

def migrate_brands():
    """
    Ürünlerdeki string 'brand' alanlarını yeni 'Brand' modeline taşır.
    """
    print("Marka taşıma işlemi başlatılıyor...")
    
    products_with_brand = Product.objects.filter(is_deleted=False).exclude(brand='')
    total_count = products_with_brand.count()
    print(f"Taşınacak markası olan toplam ürün sayısı: {total_count}")
    
    migrated_count = 0
    brands_created = 0
    
    for product in products_with_brand:
        brand_name = product.brand.strip()
        if not brand_name:
            continue
            
        # Bu tenant için bu isimde marka var mı bak, yoksa oluştur
        brand_obj, created = Brand.objects.get_or_create(
            tenant=product.tenant,
            name=brand_name,
            defaults={
                'slug': slugify(brand_name)
            }
        )
        
        if created:
            brands_created += 1
            print(f"Yeni marka oluşturuldu: {brand_name} (Tenant: {product.tenant.name})")
            
        # Ürünü yeni markaya bağla
        product.brand_item = brand_obj
        product.save(update_fields=['brand_item'])
        migrated_count += 1
        
        if migrated_count % 10 == 0:
            print(f"İlerleme: {migrated_count}/{total_count} ürün işlendi.")

    print("\nİşlem Tamamlandı!")
    print(f"Toplam oluşturulan marka sayısı: {brands_created}")
    print(f"Toplam güncellenen ürün sayısı: {migrated_count}")

if __name__ == "__main__":
    migrate_brands()
