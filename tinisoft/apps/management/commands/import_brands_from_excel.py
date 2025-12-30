"""
Django management command: Excel'den marka bilgilerini ürünlere aktar.

Kullanım:
    python manage.py import_brands_from_excel <tenant_slug> <excel_file_path>

Örnek:
    python manage.py import_brands_from_excel avrupamutfak ../test23.xlsx
"""
import os
import sys
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.models import Tenant, Product
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Excel'den marka bilgilerini ürünlere aktarır"

    def add_arguments(self, parser):
        parser.add_argument(
            'tenant_slug',
            type=str,
            help='Tenant slug (örn: avrupamutfak)'
        )
        parser.add_argument(
            'excel_file',
            type=str,
            help='Excel dosyası yolu (örn: ../test23.xlsx)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece test et, veritabanına yazma'
        )
        parser.add_argument(
            '--match-by',
            type=str,
            default='sku',
            choices=['sku', 'barcode'],
            help='Ürün eşleştirme yöntemi: sku (Urun-Kodu) veya barcode (Barcode)'
        )

    def handle(self, *args, **options):
        tenant_slug = options['tenant_slug']
        excel_file = options['excel_file']
        dry_run = options['dry_run']
        match_by = options['match_by']

        # Tenant kontrolü
        try:
            tenant = Tenant.objects.get(slug=tenant_slug)
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant bulunamadı: {tenant_slug}")

        # Excel dosyası kontrolü
        if not os.path.exists(excel_file):
            raise CommandError(f"Excel dosyası bulunamadı: {excel_file}")

        self.stdout.write(f"Tenant: {tenant.name} ({tenant.slug})")
        self.stdout.write(f"Excel dosyası: {excel_file}")
        self.stdout.write(f"Eşleştirme: {match_by}")
        self.stdout.write(f"Dry run: {dry_run}")
        self.stdout.write("-" * 80)

        # Excel'i oku
        try:
            df = pd.read_excel(excel_file)
            self.stdout.write(f"Excel'den {len(df)} satır okundu.")
        except Exception as e:
            raise CommandError(f"Excel okuma hatası: {str(e)}")

        # Kolon isimlerini kontrol et
        excel_columns = [col.strip() for col in df.columns.tolist()]
        
        # Marka kolonunu bul (farklı yazımlar için)
        brand_column = None
        for col in excel_columns:
            col_lower = col.lower()
            if 'marka' in col_lower or 'brand' in col_lower:
                brand_column = col
                break
        
        if not brand_column:
            self.stdout.write(self.style.WARNING("⚠ Marka kolonu bulunamadı!"))
            self.stdout.write(f"Mevcut kolonlar: {', '.join(excel_columns[:10])}...")
            return

        self.stdout.write(f"Marka kolonu bulundu: '{brand_column}'")

        # Eşleştirme kolonunu bul
        if match_by == 'sku':
            match_column = None
            for col in excel_columns:
                col_lower = col.lower()
                if 'urun-kodu' in col_lower or 'urun_kodu' in col_lower or 'sku' in col_lower or 'ana ürün kodu' in col_lower:
                    match_column = col
                    break
            
            if not match_column:
                self.stdout.write(self.style.WARNING("⚠ Ürün kodu kolonu bulunamadı!"))
                return
            
            self.stdout.write(f"Eşleştirme kolonu: '{match_column}' (SKU)")
        else:  # barcode
            match_column = None
            for col in excel_columns:
                col_lower = col.lower()
                if 'barcode' in col_lower or 'barkod' in col_lower:
                    match_column = col
                    break
            
            if not match_column:
                self.stdout.write(self.style.WARNING("⚠ Barcode kolonu bulunamadı!"))
                return
            
            self.stdout.write(f"Eşleştirme kolonu: '{match_column}' (Barcode)")

        self.stdout.write("-" * 80)

        # Excel'den marka bilgilerini al
        brand_data = {}
        updated_count = 0
        not_found_count = 0
        no_brand_count = 0

        for index, row in df.iterrows():
            # Eşleştirme değeri
            match_value = str(row.get(match_column, '')).strip() if pd.notna(row.get(match_column)) else None
            if not match_value or match_value == 'nan' or match_value == '':
                continue

            # Marka değeri
            brand_value = str(row.get(brand_column, '')).strip() if pd.notna(row.get(brand_column)) else None
            if not brand_value or brand_value == 'nan' or brand_value == '':
                no_brand_count += 1
                continue

            brand_data[match_value] = brand_value

        self.stdout.write(f"Excel'den {len(brand_data)} ürün için marka bilgisi bulundu.")
        self.stdout.write(f"Marka bilgisi olmayan satır sayısı: {no_brand_count}")
        self.stdout.write("-" * 80)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - Veritabanına yazılmayacak"))
            self.stdout.write(f"\nVeritabanında eşleşen ürünler kontrol ediliyor...")
            
            # Toplu sorgu ile performansı artır
            match_values_list = list(brand_data.keys())
            
            if match_by == 'sku':
                # Tüm SKU'ları bir kerede çek
                products_qs = Product.objects.filter(
                    tenant=tenant,
                    sku__in=match_values_list,
                    is_deleted=False
                ).values('id', 'sku', 'name')
            else:  # barcode
                # Tüm barcode'ları bir kerede çek
                products_qs = Product.objects.filter(
                    tenant=tenant,
                    barcode__in=match_values_list,
                    is_deleted=False
                ).values('id', 'barcode', 'name')
            
            # Eşleşen ürünleri dict'e çevir
            products_dict = {}
            for product in products_qs:
                key = product['sku'] if match_by == 'sku' else product['barcode']
                products_dict[key] = product
            
            # Eşleştirmeleri kontrol et
            matched_products = []
            matched_count = 0
            unmatched_count = 0
            
            for match_value, brand_value in brand_data.items():
                product = products_dict.get(match_value)
                if product:
                    matched_count += 1
                    if len(matched_products) < 10:
                        matched_products.append((match_value, brand_value, product['name']))
                else:
                    unmatched_count += 1
                    if unmatched_count <= 5:  # İlk 5 bulunamayanı göster
                        self.stdout.write(
                            self.style.WARNING(f"  ⚠ Bulunamadı: {match_by}={match_value}, marka={brand_value}")
                        )
            
            self.stdout.write(f"\n✓ Eşleşen ürün sayısı: {matched_count}")
            if unmatched_count > 0:
                self.stdout.write(self.style.WARNING(f"⚠ Bulunamayan ürün sayısı: {unmatched_count}"))
            
            if matched_products:
                self.stdout.write(f"\nÖrnek eşleştirmeler (ilk {len(matched_products)}):")
                for match_val, brand_val, product_name in matched_products:
                    self.stdout.write(f"  {match_val} → {brand_val} (Ürün: {product_name})")
        else:
            # Veritabanına yaz - Toplu sorgu ile optimize edildi
            self.stdout.write(f"\nÜrünler güncelleniyor...")
            
            match_values_list = list(brand_data.keys())
            
            # Toplu sorgu ile tüm ürünleri al
            if match_by == 'sku':
                products = Product.objects.filter(
                    tenant=tenant,
                    sku__in=match_values_list,
                    is_deleted=False
                )
            else:  # barcode
                products = Product.objects.filter(
                    tenant=tenant,
                    barcode__in=match_values_list,
                    is_deleted=False
                )
            
            # Ürünleri dict'e çevir (key: sku/barcode, value: product)
            products_dict = {}
            for product in products:
                key = product.sku if match_by == 'sku' else product.barcode
                products_dict[key] = product
            
            # Güncellemeleri yap
            with transaction.atomic():
                for match_value, brand_value in brand_data.items():
                    try:
                        product = products_dict.get(match_value)
                        
                        if product:
                            # Metadata'ya marka ekle/güncelle
                            if not product.metadata:
                                product.metadata = {}
                            
                            product.metadata['brand'] = brand_value
                            product.save(update_fields=['metadata'])
                            
                            updated_count += 1
                            
                            if updated_count % 100 == 0:
                                self.stdout.write(f"  {updated_count} ürün güncellendi...")
                        else:
                            not_found_count += 1
                            if not_found_count <= 10:  # İlk 10 tanesini göster
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"  Ürün bulunamadı: {match_by}={match_value}, marka={brand_value}"
                                    )
                                )

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"  Hata ({match_value}): {str(e)}"
                            )
                        )
                        logger.error(f"Error updating product {match_value}: {str(e)}", exc_info=True)

        # Özet
        self.stdout.write("-" * 80)
        self.stdout.write(self.style.SUCCESS(f"✓ Güncellenen ürün sayısı: {updated_count}"))
        if not_found_count > 0:
            self.stdout.write(self.style.WARNING(f"⚠ Bulunamayan ürün sayısı: {not_found_count}"))
        if no_brand_count > 0:
            self.stdout.write(self.style.WARNING(f"⚠ Marka bilgisi olmayan satır: {no_brand_count}"))

