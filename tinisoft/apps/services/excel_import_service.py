"""
Excel Import Service - Ürün Excel'den import etme.
"""
import openpyxl
import pandas as pd
from django.utils.text import slugify
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from apps.models import Product, Category, ProductImage
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ExcelImportService:
    """Excel'den ürün import servisi."""
    
    # Excel kolon isimleri -> Product model alanları mapping
    FIELD_MAPPING = {
        # Temel bilgiler
        'urunadi': 'name',
        'urun_adi': 'name',
        'urun_adı': 'name',
        'name': 'name',
        'isim': 'name',
        'urun_ismi': 'name',
        
        'urunaciklamasi': 'description',
        'urun_aciklamasi': 'description',
        'urun_acıklaması': 'description',
        'aciklama': 'description',
        'açıklama': 'description',
        'description': 'description',
        'urun_aciklamasi1': 'description',
        'urun_aciklamasi2': 'description_2',
        'urun_aciklamasi3': 'description_3',
        'urun_aciklamasi4': 'description_4',
        'urun_aciklamasi5': 'description_5',
        
        'fiyat': 'price',
        'price': 'price',
        'satis_fiyati': 'price',
        'satış_fiyatı': 'price',
        
        'karsilastirma_fiyati': 'compare_at_price',
        'karşılaştırma_fiyatı': 'compare_at_price',
        'compare_at_price': 'compare_at_price',
        'eski_fiyat': 'compare_at_price',
        
        'urun-kodu': 'sku',
        'urun_kodu': 'sku',
        'ana ürün kodu': 'sku',
        'ana_urun_kodu': 'sku',
        'sku': 'sku',
        'stok_kodu': 'sku',
        'barcode': 'barcode',
        'barkod': 'barcode',
        
        # Stok
        'ürün adedi': 'inventory_quantity',
        'ürün adedı': 'inventory_quantity',  # Encoding hatası için
        'urun_adedi': 'inventory_quantity',
        'urun_adedi2': 'inventory_quantity_2',
        'stok': 'inventory_quantity',
        'stok_adedi': 'inventory_quantity',
        'inventory_quantity': 'inventory_quantity',
        'miktar': 'inventory_quantity',
        'adet': 'inventory_quantity',
        
        'stok_takibi': 'track_inventory',
        'track_inventory': 'track_inventory',
        
        # Kategori
        'ürün kategori adı': 'category',
        'ürün kategorı adı': 'category',  # Encoding hatası için
        'urun_kategori_adi': 'category',
        'urun_kategori_adı': 'category',
        'kategori': 'category',
        'category': 'category',
        'kategori_adi': 'category',
        'kategori_adı': 'category',
        'eticaretkategori': 'ecommerce_category',
        'eticaret_kategori': 'ecommerce_category',
        
        # Durum
        'ürün durumu': 'status',
        'ürün durumı': 'status',  # Encoding hatası için
        'urun_durumu': 'status',
        'urun_durum': 'status',
        'durum': 'status',
        'status': 'status',
        'statu': 'status',
        
        'gorunur': 'is_visible',
        'görünür': 'is_visible',
        'is_visible': 'is_visible',
        'aktif': 'is_visible',
        
        # Özellikler
        'one_cikan': 'is_featured',
        'öne_çıkan': 'is_featured',
        'is_featured': 'is_featured',
        'featured': 'is_featured',
        
        'yeni': 'is_new',
        'is_new': 'is_new',
        'new': 'is_new',
        
        'cok_satan': 'is_bestseller',
        'çok_satan': 'is_bestseller',
        'is_bestseller': 'is_bestseller',
        'bestseller': 'is_bestseller',
        
        # SEO
        'meta_baslik': 'meta_title',
        'meta_başlık': 'meta_title',
        'meta_title': 'meta_title',
        'seo_baslik': 'meta_title',
        
        'meta_aciklama': 'meta_description',
        'meta_açıklama': 'meta_description',
        'meta_description': 'meta_description',
        'seo_aciklama': 'meta_description',
        
        'meta_anahtar_kelimeler': 'meta_keywords',
        'meta_keywords': 'meta_keywords',
        'seo_keywords': 'meta_keywords',
        
        # Kargo bilgileri
        'ürün ağırlık': 'weight',
        'ürün ağırlık': 'weight',  # Encoding hatası için
        'urun_agirlik': 'weight',
        'urun_ağırlık': 'weight',
        'agirlik': 'weight',
        'ağırlık': 'weight',
        'weight': 'weight',
        'kg': 'weight',
        'secenek_agirlik': 'weight',
        'secenek_ağırlık': 'weight',
        'secenek_agirlik': 'weight',
        
        'ürün boy': 'length',
        'ürün boy': 'length',  # Encoding hatası için
        'urun_boy': 'length',
        'uzunluk': 'length',
        'length': 'length',
        'boy': 'length',
        
        'ürün en': 'width',
        'ürün en': 'width',  # Encoding hatası için
        'urun_en': 'width',
        'genislik': 'width',
        'genişlik': 'width',
        'width': 'width',
        'en': 'width',
        'secenek_genislik': 'width',
        'secenek_genişlik': 'width',
        'secenek_genislik': 'width',
        
        'ürün derinlik': 'depth',
        'ürün derinlik': 'depth',  # Encoding hatası için
        'urun_derinlik': 'depth',
        'derinlik': 'depth',
        'depth': 'depth',
        'secenek_derinlik': 'depth',
        
        'ürün desi': 'desi',
        'ürün desı': 'desi',  # Encoding hatası için
        'urun_desi': 'desi',
        'desi': 'desi',
        'secenek_desi': 'desi',
        
        'yukseklik': 'height',
        'yükseklik': 'height',
        'height': 'height',
        
        # Görseller
        'imageurl1': 'image_url_1',
        'imageurl2': 'image_url_2',
        'imageurl3': 'image_url_3',
        'imageurl4': 'image_url_4',
        'imageurl5': 'image_url_5',
        'imageurl6': 'image_url_6',
        'imageurl7': 'image_url_7',
        'imageurl8': 'image_url_8',
        'imageurl9': 'image_url_9',
        'imageurl10': 'image_url_10',
        
        # ImageName kolonları (local path)
        'imagename1': 'image_name_1',
        'imagename2': 'image_name_2',
        'imagename3': 'image_name_3',
        'imagename4': 'image_name_4',
        'imagename5': 'image_name_5',
        'imagename6': 'image_name_6',
        'imagename7': 'image_name_7',
        'imagename8': 'image_name_8',
        'imagename9': 'image_name_9',
        'imagename10': 'image_name_10',
        'gorsel': 'image_url',
        'görsel': 'image_url',
        'image_url': 'image_url',
        'resim': 'image_url',
        'resim_url': 'image_url',
        'gorsel_url': 'image_url',
        
        'gorseller': 'images',
        'görseller': 'images',
        'images': 'images',
        'resimler': 'images',
        
        # Etiketler
        'etiketler': 'tags',
        'tags': 'tags',
        'tag': 'tags',
        
        # Sıralama
        'sira': 'sort_order',
        'sıra': 'sort_order',
        'sort_order': 'sort_order',
        'siralama': 'sort_order',
        
        # Yeni alanlar
        'marka': 'brand',
        'brand': 'brand',
        
        'menşei': 'origin',
        'menşe-i': 'origin',
        'menşeı': 'origin',  # Encoding hatası için
        'mensei': 'origin',
        'mense-i': 'origin',
        'origin': 'origin',
        
        'ürün tipi': 'product_type',
        'urun_tipi': 'product_type',
        'product_type': 'product_type',
        
        'ürün gtin': 'gtin',
        'urun_gtin': 'gtin',
        'gtin': 'gtin',
        'secenek-gtin': 'gtin',
        'secenek_gtin': 'gtin',
        
        'ürün mpn': 'mpn',
        'urun_mpn': 'mpn',
        'mpn': 'mpn',
        'secenek-mpn': 'mpn',
        'secenek_mpn': 'mpn',
        
        'ürün gtip': 'gtip',
        'urun_gtip': 'gtip',
        'gtip': 'gtip',
        
        'buying_price': 'buying_price',
        'alış_fiyatı': 'buying_price',
        'alis_fiyati': 'buying_price',
        
        'eticaret_site_fiyati': 'ecommerce_price',
        'ecommerce_price': 'ecommerce_price',
        'e-ticaret_fiyatı': 'ecommerce_price',
        
        '2-ürün kargo fiyatı': 'shipping_price',
        'urun_kargo_fiyati': 'shipping_price',
        'kargo_fiyatı': 'shipping_price',
        'shipping_price': 'shipping_price',
        
        'kritik stok': 'critical_stock',
        'kritik_stok': 'critical_stock',
        'critical_stock': 'critical_stock',
        
        'fatura adı': 'invoice_name',
        'fatura_adi': 'invoice_name',
        'invoice_name': 'invoice_name',
        
        'raf numarası': 'shelf_number',
        'raf_numarasi': 'shelf_number',
        'shelf_number': 'shelf_number',
        
        'fulfillmentid': 'fulfillment_id',
        'fulfillment_id': 'fulfillment_id',
        'secenekfulfillmentid': 'fulfillment_id',
        
        'xml fiyatı': 'xml_price',
        'xml_fiyati': 'xml_price',
        'xml_price': 'xml_price',
        'secenek_xml_fiyat': 'xml_price',
        
        'parabirimi': 'currency',
        'para_birimi': 'currency',
        'currency': 'currency',
        
        'kdv': 'tax_rate',
        'tax_rate': 'tax_rate',
        'vergi_orani': 'tax_rate',
        
        'ürün güncellenme tarihi': 'updated_date',
        'ürün güncellenme tarıhı': 'updated_date',  # Encoding hatası için
        'urun_guncellenme_tarihi': 'updated_date',
        
        'ürün miad': 'expiry_date',
        'ürün mıad': 'expiry_date',  # Encoding hatası için
        'urun_miad': 'expiry_date',
        'expiry_date': 'expiry_date',
        'son_kullanma_tarihi': 'expiry_date',
        
        # Varyant bilgileri (metadata'da saklanır)
        'varyantid': 'variant_id',
        'varyant_id': 'variant_id',
        'secenek-ürün-kodu': 'variant_sku',
        'secenek_urun_kodu': 'variant_sku',
        'secenek-barcode': 'variant_barcode',
        'secenek_barcode': 'variant_barcode',
        'varyantfiyatfark': 'variant_price_diff',
        'varyant_fiyat_fark': 'variant_price_diff',
        
        # Uyumluluk alanları (metadata'da saklanır)
        'uyumluluk model': 'compatibility_model',
        'uyumluluk seri': 'compatibility_serial',
        'uyumluluk hacim': 'compatibility_volume',
        'uyumluluk yıl': 'compatibility_year',
        'uyumluluk numara': 'compatibility_number',
        'uyumluluk beden': 'compatibility_size',
        'uyumluluk renk': 'compatibility_color',
        'uyumluluk desen': 'compatibility_pattern',
        'uyumluluk cinsiyet': 'compatibility_gender',
    }
    
    @staticmethod
    def import_products_from_excel(file_path, tenant, user=None):
        """
        Excel dosyasından ürünleri import et.
        
        Args:
            file_path: Excel dosya yolu
            tenant: Tenant instance
            user: User instance (opsiyonel)
        
        Returns:
            dict: {
                'success': bool,
                'imported_count': int,
                'failed_count': int,
                'errors': list,
                'products': list
            }
        """
        imported_count = 0
        failed_count = 0
        errors = []
        products = []
        
        try:
            # Excel dosyasını oku
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Kolon isimlerini normalize et (küçük harf, boşlukları temizle)
            df.columns = df.columns.str.lower().str.strip()
            
            # Her satırı işle
            for index, row in df.iterrows():
                try:
                    product_data = ExcelImportService._map_row_to_product_data(row, tenant)
                    product = ExcelImportService._create_product(product_data, tenant, user)
                    products.append(product)
                    imported_count += 1
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Satır {index + 2}: {str(e)}"  # +2 çünkü Excel'de header var ve 0-based index
                    errors.append(error_msg)
                    logger.error(f"Product import error at row {index + 2}: {str(e)}")
            
            return {
                'success': True,
                'imported_count': imported_count,
                'failed_count': failed_count,
                'errors': errors,
                'products': products
            }
        
        except Exception as e:
            logger.error(f"Excel import error: {str(e)}")
            return {
                'success': False,
                'imported_count': imported_count,
                'failed_count': failed_count,
                'errors': [f"Excel okuma hatası: {str(e)}"],
                'products': []
            }
    
    @staticmethod
    def _map_row_to_product_data(row, tenant):
        """Excel satırını Product data dict'ine çevir."""
        product_data = {
            'tenant': tenant,
        }
        
        # Mapping yap
        for excel_col, model_field in ExcelImportService.FIELD_MAPPING.items():
            if excel_col in row.index and pd.notna(row[excel_col]):
                value = row[excel_col]
                
                # Değer tipine göre işle
                if model_field == 'name':
                    product_data['name'] = str(value).strip()
                    # Slug otomatik oluştur
                    product_data['slug'] = slugify(product_data['name'])
                
                elif model_field == 'description':
                    product_data['description'] = str(value).strip()
                
                elif model_field in ['price', 'compare_at_price', 'weight', 'length', 'width', 'height']:
                    try:
                        # Decimal'e çevir
                        if isinstance(value, (int, float)):
                            product_data[model_field] = Decimal(str(value))
                        else:
                            # String'den temizle ve çevir
                            clean_value = str(value).replace(',', '.').replace(' ', '').replace('₺', '').replace('TL', '')
                            product_data[model_field] = Decimal(clean_value)
                    except (InvalidOperation, ValueError):
                        pass  # Geçersiz değer, atla
                
                elif model_field == 'inventory_quantity':
                    try:
                        product_data['inventory_quantity'] = int(float(value))
                    except (ValueError, TypeError):
                        product_data['inventory_quantity'] = 0
                
                elif model_field == 'track_inventory':
                    # Boolean değerlere çevir
                    if isinstance(value, bool):
                        product_data['track_inventory'] = value
                    elif isinstance(value, str):
                        product_data['track_inventory'] = value.lower() in ['true', 'evet', 'yes', '1', 'var']
                    else:
                        product_data['track_inventory'] = bool(value)
                
                elif model_field == 'category':
                    # Hiyerarşik kategori işleme (örn: "İçecek Ekipmanları>Soğuk İçecek Makineleri")
                    if value:
                        category_path = str(value).strip()
                        if category_path:
                            # Hiyerarşik kategori oluştur
                            category = ExcelImportService._get_or_create_category_tree(
                                tenant=tenant,
                                category_path=category_path
                            )
                            product_data['category'] = category
                
                elif model_field == 'status':
                    status_value = str(value).strip().lower()
                    if status_value in ['active', 'aktif', 'aktif', '1']:
                        product_data['status'] = 'active'
                    elif status_value in ['draft', 'taslak', '0']:
                        product_data['status'] = 'draft'
                    elif status_value in ['archived', 'arsiv', 'arşiv']:
                        product_data['status'] = 'archived'
                    else:
                        product_data['status'] = 'draft'
                
                elif model_field in ['is_visible', 'is_featured', 'is_new', 'is_bestseller']:
                    # Boolean değerlere çevir
                    if isinstance(value, bool):
                        product_data[model_field] = value
                    elif isinstance(value, str):
                        product_data[model_field] = value.lower() in ['true', 'evet', 'yes', '1', 'var']
                    else:
                        product_data[model_field] = bool(value)
                
                elif model_field in ['meta_title', 'meta_description', 'meta_keywords', 'sku', 'barcode']:
                    product_data[model_field] = str(value).strip() if value else ''
                
                elif model_field == 'tags':
                    # Virgülle ayrılmış etiketler
                    if isinstance(value, str):
                        tags = [tag.strip() for tag in value.split(',') if tag.strip()]
                        product_data['tags'] = tags
                    elif isinstance(value, list):
                        product_data['tags'] = value
                
                elif model_field.startswith('image_url_'):
                    # ImageURL1, ImageURL2, vb.
                    if 'image_urls' not in product_data:
                        product_data['image_urls'] = []
                    image_url = str(value).strip()
                    if image_url:
                        product_data['image_urls'].append(image_url)
                
                elif model_field.startswith('image_name_'):
                    # ImageName1, ImageName2, vb. (local path)
                    if 'image_paths' not in product_data:
                        product_data['image_paths'] = []
                    image_path = str(value).strip()
                    if image_path:
                        product_data['image_paths'].append(image_path)
                
                elif model_field == 'images':
                    # Virgülle ayrılmış görsel URL'leri
                    if isinstance(value, str):
                        image_urls = [url.strip() for url in value.split(',') if url.strip()]
                        if 'image_urls' not in product_data:
                            product_data['image_urls'] = []
                        product_data['image_urls'].extend(image_urls)
                    elif isinstance(value, list):
                        if 'image_urls' not in product_data:
                            product_data['image_urls'] = []
                        product_data['image_urls'].extend(value)
                
                elif model_field == 'image_url':
                    # Tek görsel URL
                    if 'image_urls' not in product_data:
                        product_data['image_urls'] = []
                    product_data['image_urls'].append(str(value).strip())
                
                elif model_field in ['brand', 'origin', 'product_type', 'gtin', 'mpn', 'gtip', 
                                     'invoice_name', 'shelf_number', 'fulfillment_id', 
                                     'ecommerce_category', 'ecommerce_integration_code']:
                    product_data[model_field] = str(value).strip() if value else ''
                
                elif model_field in ['buying_price', 'ecommerce_price', 'shipping_price', 'desi']:
                    try:
                        if isinstance(value, (int, float)):
                            product_data[model_field] = Decimal(str(value))
                        else:
                            clean_value = str(value).replace(',', '.').replace(' ', '').replace('₺', '').replace('TL', '')
                            product_data[model_field] = Decimal(clean_value)
                    except (InvalidOperation, ValueError):
                        pass
                
                elif model_field == 'critical_stock':
                    try:
                        product_data['critical_stock'] = int(float(value))
                    except (ValueError, TypeError):
                        product_data['critical_stock'] = 0
                
                elif model_field == 'expiry_date':
                    # Tarih parse et
                    try:
                        if isinstance(value, datetime):
                            product_data['expiry_date'] = value.date()
                        elif isinstance(value, str):
                            # Farklı tarih formatlarını dene
                            for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%Y.%m.%d']:
                                try:
                                    product_data['expiry_date'] = datetime.strptime(value.strip(), fmt).date()
                                    break
                                except:
                                    continue
                    except:
                        pass
                
                elif model_field == 'currency':
                    product_data['currency'] = str(value).strip().upper()[:3] if value else 'TRY'
                
                elif model_field == 'tax_rate':
                    try:
                        product_data['tax_rate'] = Decimal(str(value))
                    except:
                        pass
                
                elif model_field.startswith('compatibility_'):
                    # Uyumluluk bilgileri metadata'da saklanır
                    if 'compatibility' not in product_data:
                        product_data['compatibility'] = {}
                    field_name = model_field.replace('compatibility_', '')
                    product_data['compatibility'][field_name] = str(value).strip() if value else ''
                
                elif model_field in ['variant_id', 'variant_sku', 'variant_barcode', 'variant_price_diff']:
                    # Varyant bilgileri metadata'da saklanır
                    if 'variant_info' not in product_data:
                        product_data['variant_info'] = {}
                    field_name = model_field.replace('variant_', '')
                    if model_field == 'variant_price_diff':
                        try:
                            product_data['variant_info'][field_name] = Decimal(str(value))
                        except:
                            pass
                    else:
                        product_data['variant_info'][field_name] = str(value).strip() if value else ''
                
                elif model_field.startswith('description_'):
                    # Birden fazla açıklama metadata'da saklanır
                    if 'descriptions' not in product_data:
                        product_data['descriptions'] = {}
                    field_name = model_field.replace('description_', '')
                    product_data['descriptions'][field_name] = str(value).strip() if value else ''
                
                elif model_field == 'sort_order':
                    try:
                        product_data['sort_order'] = int(float(value))
                    except (ValueError, TypeError):
                        product_data['sort_order'] = 0
        
        # Zorunlu alanlar kontrolü
        if 'name' not in product_data or not product_data['name']:
            raise ValueError("Ürün adı zorunludur.")
        
        if 'price' not in product_data:
            product_data['price'] = Decimal('0.00')
        
        if 'slug' not in product_data:
            product_data['slug'] = slugify(product_data['name'])
        
        # Varsayılan değerler
        product_data.setdefault('status', 'draft')
        product_data.setdefault('is_visible', True)
        product_data.setdefault('track_inventory', True)
        product_data.setdefault('inventory_quantity', 0)
        product_data.setdefault('sort_order', 0)
        product_data.setdefault('currency', 'TRY')
        
        # Uyumluluk bilgilerini metadata'ya ekle
        if 'compatibility' in product_data:
            if 'metadata' not in product_data:
                product_data['metadata'] = {}
            product_data['metadata']['compatibility'] = product_data.pop('compatibility')
        
        # Ek açıklamaları metadata'ya ekle
        if 'descriptions' in product_data:
            if 'metadata' not in product_data:
                product_data['metadata'] = {}
            product_data['metadata']['additional_descriptions'] = product_data.pop('descriptions')
        
        # XML fiyatı metadata'ya ekle (Decimal -> string)
        if 'xml_price' in product_data:
            if 'metadata' not in product_data:
                product_data['metadata'] = {}
            xml_price = product_data.pop('xml_price')
            # Decimal'i string'e çevir (JSON serializable)
            product_data['metadata']['xml_price'] = str(xml_price) if isinstance(xml_price, Decimal) else xml_price
        
        # Tax rate metadata'ya ekle (Decimal -> string)
        if 'tax_rate' in product_data:
            if 'metadata' not in product_data:
                product_data['metadata'] = {}
            tax_rate = product_data.pop('tax_rate')
            # Decimal'i string'e çevir (JSON serializable)
            product_data['metadata']['tax_rate'] = str(tax_rate) if isinstance(tax_rate, Decimal) else tax_rate
        
        # Varyant bilgilerini metadata'ya ekle (Decimal -> string)
        if 'variant_info' in product_data:
            if 'metadata' not in product_data:
                product_data['metadata'] = {}
            variant_info = product_data.pop('variant_info')
            # Decimal değerleri string'e çevir
            if isinstance(variant_info, dict):
                for key, value in variant_info.items():
                    if isinstance(value, Decimal):
                        variant_info[key] = str(value)
            product_data['metadata']['variant_info'] = variant_info
        
        # Inventory quantity 2 metadata'ya ekle
        if 'inventory_quantity_2' in product_data:
            if 'metadata' not in product_data:
                product_data['metadata'] = {}
            product_data['metadata']['inventory_quantity_2'] = product_data.pop('inventory_quantity_2')
        
        # Image paths metadata'ya ekle (local resim yolları)
        if 'image_paths' in product_data:
            if 'metadata' not in product_data:
                product_data['metadata'] = {}
            product_data['metadata']['image_paths'] = product_data.pop('image_paths')
        
        # Metadata'daki tüm Decimal değerleri string'e çevir (JSON serializable)
        if 'metadata' in product_data:
            ExcelImportService._convert_decimals_to_string(product_data['metadata'])
        
        return product_data
    
    @staticmethod
    def _convert_decimals_to_string(obj):
        """Recursively convert Decimal values to string in dict/list."""
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = ExcelImportService._convert_decimals_to_string(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                obj[i] = ExcelImportService._convert_decimals_to_string(item)
        return obj
    
    @staticmethod
    def _create_product(product_data, tenant, user=None):
        """Product oluştur."""
        from django.db import transaction
        
        with transaction.atomic():
            # Kategoriyi ayır
            category = product_data.pop('category', None)
            image_urls = product_data.pop('image_urls', [])
            primary_image_url = product_data.pop('primary_image_url', None)
            
            # Slug unique kontrolü
            base_slug = product_data['slug']
            slug = base_slug
            counter = 1
            while Product.objects.filter(tenant=tenant, slug=slug, is_deleted=False).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            product_data['slug'] = slug
            
            # Product oluştur
            product = Product.objects.create(**product_data)
            
            # Kategori ekle
            if category:
                product.categories.add(category)
            
            # Görseller ekle
            if primary_image_url:
                ProductImage.objects.create(
                    product=product,
                    image_url=primary_image_url,
                    is_primary=True,
                    position=0
                )
            
            if image_urls:
                for idx, image_url in enumerate(image_urls):
                    if image_url:  # Boş URL'leri atla
                        ProductImage.objects.create(
                            product=product,
                            image_url=image_url,
                            is_primary=(idx == 0 and not primary_image_url),
                            position=idx
                        )
            
            return product
    
    @staticmethod
    def _get_or_create_category_tree(tenant, category_path):
        """
        Hiyerarşik kategori ağacı oluştur.
        
        Args:
            tenant: Tenant instance
            category_path: Kategori yolu (örn: "İçecek Ekipmanları>Soğuk İçecek Makineleri")
        
        Returns:
            Category: En alt seviye kategori
        """
        if not category_path or not category_path.strip():
            return None
        
        # Kategori yolu ">" ile ayrılmış
        category_names = [name.strip() for name in str(category_path).split('>') if name.strip()]
        
        if not category_names:
            return None
        
        parent = None
        current_category = None
        
        # Her seviyeyi oluştur
        for category_name in category_names:
            # Slug oluştur
            category_slug = slugify(category_name)
            
            # Kategoriyi bul veya oluştur
            if parent:
                # Alt kategori - parent'a göre ara
                current_category, created = Category.objects.get_or_create(
                    tenant=tenant,
                    name=category_name,
                    parent=parent,
                    defaults={'slug': category_slug}
                )
            else:
                # Root kategori - parent yok
                current_category, created = Category.objects.get_or_create(
                    tenant=tenant,
                    name=category_name,
                    parent=None,
                    defaults={'slug': category_slug}
                )
            
            # Parent'ı güncelle (bir sonraki seviye için)
            parent = current_category
        
        return current_category

