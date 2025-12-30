"""
Aras Kargo API dokümantasyonunu PDF'den extract et ve analiz et.
SOAP metodları, parametreler ve response formatlarını çıkarır.
"""
import pdfplumber
import re
import json
import sys

# Windows terminal encoding sorununu çöz
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def extract_aras_api_docs():
    """PDF'den Aras Kargo API dokümantasyonunu extract et."""
    
    import os
    # Root dizindeki PDF'i bul - önce takip web sayfası PDF'ini dene
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)  # tinisoft klasörünün üstü
    pdf_path = os.path.join(root_dir, 'kargotakipwebsayfasıuyeligihakkinda.pdf')
    
    if not os.path.exists(pdf_path):
        # Root dizinde de dene
        pdf_path = os.path.join(script_dir, '..', 'kargotakipwebsayfasıuyeligihakkinda.pdf')
        pdf_path = os.path.abspath(pdf_path)
    
    if not os.path.exists(pdf_path):
        # Eski PDF'i dene
        pdf_path = os.path.join(root_dir, 'Aras Kargo-Müşteri Bilgi Sorgulama Servisleri.pdf')
    
    try:
        pdf = pdfplumber.open(pdf_path)
        print(f'[INFO] Toplam sayfa: {len(pdf.pages)}\n')
    except Exception as e:
        print(f'[ERROR] PDF acilamadi: {e}')
        return
    
    # İlgili bölümleri bulmak için anahtar kelimeler
    api_keywords = [
        'GetQueryDS', 'CreateShipment', 'CancelShipment', 'PrintLabel',
        'SOAP', 'XML', 'Request', 'Response', 'Parameter', 'Parametre',
        'username', 'password', 'customerCode', 'QueryType',
        'KargoTakipNo', 'MusteriKodu', 'MüşteriKodu', 'ReferansNo',
        'AliciAdi', 'AliciSoyadi', 'AliciAdres', 'AliciIl', 'AliciIlce',
        'AliciTelefon', 'Icerik', 'Desi', 'Kg', 'OdemeSekli',
        'ServisTipi', 'TeslimatSekli', 'AlisverisKod', 'Tutar',
        'kargotakip', 'takip', 'tracking', 'accountid', 'alici_kod',
        'mainpage', 'iframe', 'link', 'url', 'entegrasyon'
    ]
    
    all_text = ""
    api_sections = []
    method_sections = {}
    
    print("[INFO] PDF icerigi extract ediliyor...\n")
    
    # Tüm sayfaları oku
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            all_text += f"\n=== PAGE {i+1} ===\n{text}\n"
            
            # API ile ilgili bölümleri bul
            for keyword in api_keywords:
                if keyword.lower() in text.lower():
                    # Bu sayfayı kaydet
                    if i+1 not in api_sections:
                        api_sections.append(i+1)
    
    print(f"[INFO] API ile ilgili {len(api_sections)} sayfa bulundu\n")
    
    # Metod isimlerini bul
    methods = ['GetQueryDS', 'CreateShipment', 'CancelShipment', 'PrintLabel', 
               'GetQuery', 'Query', 'Create', 'Cancel', 'Print']
    
    print("[INFO] SOAP metodlari araniyor...\n")
    
    for method in methods:
        pattern = re.compile(rf'{method}[\s\S]{{0,500}}', re.IGNORECASE)
        matches = pattern.findall(all_text)
        if matches:
            method_sections[method] = matches
            print(f"[OK] {method}: {len(matches)} bolum bulundu")
    
    # GetQueryDS detaylarını bul
    print("\n" + "="*80)
    print("[INFO] GetQueryDS Metodu Detaylari")
    print("="*80 + "\n")
    
    queryds_pattern = re.compile(
        r'GetQueryDS[\s\S]{0,2000}(?:username|password|customerCode|QueryType)[\s\S]{0,2000}',
        re.IGNORECASE
    )
    queryds_matches = queryds_pattern.findall(all_text)
    
    for i, match in enumerate(queryds_matches[:3]):  # İlk 3'ü göster
        print(f"\n--- GetQueryDS Örnek {i+1} ---\n")
        # Önemli kısımları vurgula
        match_clean = re.sub(r'\s+', ' ', match)
        print(match_clean[:800])
        print("...")
    
    # CreateShipment detaylarını bul
    print("\n" + "="*80)
    print("[INFO] CreateShipment Metodu Detaylari")
    print("="*80 + "\n")
    
    create_pattern = re.compile(
        r'CreateShipment[\s\S]{0,3000}(?:Alici|Gonderici|Icerik|Desi|Kg|Odeme)[\s\S]{0,2000}',
        re.IGNORECASE
    )
    create_matches = create_pattern.findall(all_text)
    
    for i, match in enumerate(create_matches[:3]):  # İlk 3'ü göster
        print(f"\n--- CreateShipment Örnek {i+1} ---\n")
        match_clean = re.sub(r'\s+', ' ', match)
        print(match_clean[:1000])
        print("...")
    
    # QueryType değerlerini bul
    print("\n" + "="*80)
    print("[INFO] QueryType Degerleri")
    print("="*80 + "\n")
    
    querytype_pattern = re.compile(
        r'QueryType\s*[=:]\s*(\d+)[\s\S]{0,200}(?:nedir|ne|anlam|meaning|açıklama|description|what)',
        re.IGNORECASE
    )
    querytype_matches = querytype_pattern.findall(all_text)
    
    querytype_descriptions = {}
    for qtype in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']:
        pattern = re.compile(
            rf'QueryType\s*[=:]\s*{qtype}[\s\S]{{0,300}}',
            re.IGNORECASE
        )
        matches = pattern.findall(all_text)
        if matches:
            querytype_descriptions[qtype] = matches[0][:500]
            print(f"QueryType {qtype}: {matches[0][:300]}...")
    
    # Parametre listelerini bul
    print("\n" + "="*80)
    print("[INFO] Parametre Listeleri")
    print("="*80 + "\n")
    
    # CreateShipment parametreleri
    params_pattern = re.compile(
        r'(?:parametre|parameter|alan|field)[\s\S]{0,1000}(?:AliciAdi|AliciSoyadi|AliciAdres|Icerik|Desi|Kg)[\s\S]{0,500}',
        re.IGNORECASE
    )
    params_matches = params_pattern.findall(all_text)
    
    print(f"{len(params_matches)} parametre bölümü bulundu\n")
    
    # XML/SOAP örneklerini bul
    print("\n" + "="*80)
    print("[INFO] XML/SOAP Ornekleri")
    print("="*80 + "\n")
    
    xml_pattern = re.compile(r'<[?]?xml[\s\S]{0,2000}</\w+>', re.IGNORECASE)
    xml_matches = xml_pattern.findall(all_text)
    
    print(f"{len(xml_matches)} XML örneği bulundu\n")
    for i, xml in enumerate(xml_matches[:2]):  # İlk 2 XML'i göster
        print(f"--- XML Örnek {i+1} ---\n")
        print(xml[:500])
        print("...\n")
    
    # Endpoint bilgilerini bul
    print("\n" + "="*80)
    print("[INFO] Endpoint Bilgileri")
    print("="*80 + "\n")
    
    endpoint_pattern = re.compile(
        r'(?:endpoint|url|adres|address)[\s\S]{0,100}(?:http|https|\.svc|\.asmx)[\s\S]{0,200}',
        re.IGNORECASE
    )
    endpoint_matches = endpoint_pattern.findall(all_text)
    
    for match in endpoint_matches[:5]:
        print(match[:200])
        print()
    
    # Özet bilgileri JSON'a kaydet
    summary = {
        'total_pages': len(pdf.pages),
        'api_related_pages': api_sections,
        'methods_found': list(method_sections.keys()),
        'querytypes': list(querytype_descriptions.keys()),
        'xml_examples_count': len(xml_matches),
        'parameters_sections_count': len(params_matches),
    }
    
    # Sonuçları dosyaya kaydet
    print("\n" + "="*80)
    print("[INFO] Sonuclar kaydediliyor...")
    print("="*80 + "\n")
    
    with open('aras_kargo_extracted_text.txt', 'w', encoding='utf-8') as f:
        f.write(all_text)
    
    with open('aras_kargo_api_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Önemli bölümleri ayrı dosyaya kaydet
    with open('aras_kargo_api_details.txt', 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("ARAS KARGO API DOKÜMANTASYONU\n")
        f.write("="*80 + "\n\n")
        
        f.write("\n--- GetQueryDS Metodları ---\n\n")
        for match in queryds_matches[:5]:
            f.write(match[:1000])
            f.write("\n\n" + "-"*80 + "\n\n")
        
        f.write("\n--- CreateShipment Metodları ---\n\n")
        for match in create_matches[:5]:
            f.write(match[:1500])
            f.write("\n\n" + "-"*80 + "\n\n")
        
        f.write("\n--- QueryType Değerleri ---\n\n")
        for qtype, desc in querytype_descriptions.items():
            f.write(f"QueryType {qtype}:\n{desc}\n\n")
    
    print("[OK] Tamamlandi!")
    print("\nOluşturulan dosyalar:")
    print("  - aras_kargo_extracted_text.txt (Tüm metin)")
    print("  - aras_kargo_api_summary.json (Özet JSON)")
    print("  - aras_kargo_api_details.txt (Detaylı API bilgileri)")
    
    pdf.close()

if __name__ == '__main__':
    extract_aras_api_docs()

