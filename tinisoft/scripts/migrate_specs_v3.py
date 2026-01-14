import re
import html
import os
import django

# Django ortamını hazırla
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tinisoft.settings')
django.setup()

from apps.models import Product

def migrate_v3():
    print("\n--- TEKNİK ÖZELLİKLER KURTARMA OPERASYONU (V3) ---")
    
    products = Product.objects.all()
    total = products.count()
    print(f"Toplam {total} ürün kontrol ediliyor...\n")
    
    count = 0
    for p in products:
        # Önce description_html'e bak (Tablo genelde burada), yoksa düz description'a bak
        source_text = p.description_html if p.description_html else p.description
        
        if not source_text:
            continue
            
        # HTML karmaşasını (&nbsp; vs) ve meşhur \xa0 karakterini temizle
        clean_text = html.unescape(source_text).replace('\xa0', ' ')
        new_specs = []
        
        # 1. YÖNTEM: Tablo Yapısını Yakala (Gelişmiş regex)
        table_rows = re.findall(r'<tr.*?>(.*?)</tr>', clean_text, re.DOTALL | re.IGNORECASE)
        for row in table_rows:
            cols = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
            if len(cols) == 2:
                # Key ve Value'yu sök, HTML taglerini temizle
                key = re.sub('<[^<]+?>', '', cols[0]).strip().replace(':', '')
                value = re.sub('<[^<]+?>', '', cols[1]).strip()
                
                # Başlıkları ve boşları atla
                if key.lower() not in ['özellik', '', 'değer', 'ozellik', 'deger']:
                    new_specs.append({"key": key, "value": value})
        
        # 2. YÖNTEM: FALLBACK - Eğer tablo yoksa ama metin içinde anahtar kelimeler varsa
        if not new_specs:
            keys = ['Model', 'Kapasite', 'Malzeme', 'Güç', 'Boyutlar', 'Ağırlık', 'Enerji']
            for k in keys:
                m = re.search(f"{k}[:\s]+(.*?)(?=<br|/p|/td|\n|$)", clean_text, re.IGNORECASE)
                if m:
                    val = re.sub('<[^<]+?>', '', m.group(1)).strip()
                    if val and len(val) < 100:
                        new_specs.append({"key": k, "value": val})

        if new_specs:
            # Mevcut specifications ile aynı mı kontrol et, boşsa veya farklıysa güncelle
            p.specifications = new_specs
            p.save(update_fields=['specifications'])
            count += 1
            if count % 100 == 0:
                print(f"✓ {count} ürün başarıyla mühürlendi...")

    print(f"\n--- İŞLEM TAMAMLANDI ---")
    print(f"✓ Toplam {count} ürünün teknik özellikleri 'specifications' alanına taşındı.")

if __name__ == "__main__":
    migrate_v3()
