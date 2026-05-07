"""
Karatekin Rotbalans için "GÜNCEL STOK 2026" Excel'ini import eder.

Bu komut TEK BİR TENANT için yazılmıştır (karatekin-rotbalans). Başka bir
tenant slug verirseniz çalışmaz. Canlıda yanlış tenant'a yazma riskini
ortadan kaldırmak için sabittir.

Excel kolonları:
    ADET           -> inventory_quantity
    EBAT+DESEN     -> name (zorunlu, boşsa satır atlanır)
    ÜRETİM TARİHİ  -> metadata.production_year
    ÜRÜN KODU      -> sku (boşsa "")
    MEVSİM         -> tags + metadata.season
    LASTİK MARKASI -> brand (CharField) + brand_item (Brand FK, get_or_create)

Sabit defaultlar:
    price            = 1.00 TL  (kullanıcı isteği — sonradan düzenlenecek)
    currency         = TRY
    status           = 'active'
    is_visible       = True
    track_inventory  = True

Kullanım:
    docker exec -it tinisoft-backend python manage.py import_karatekin_stock \\
        /app/GÜNCEL_STOK_2026.xlsx --confirm-tenant=karatekin-rotbalans --dry-run

    --dry-run kaldırınca gerçek import yapar.
"""
from decimal import Decimal

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.models import Brand, Product, Tenant

EXPECTED_TENANT_SLUG = "karatekin-rotbalans"

EXCEL_COLUMNS = {
    "ADET": "qty",
    "EBAT+DESEN": "name",
    "ÜRETİM TARİHİ": "year",
    "ÜRÜN KODU": "sku",
    "MEVSİM": "season",
    "LASTİK MARKASI": "brand",
}


class Command(BaseCommand):
    help = "Karatekin Rotbalans için stok Excel import (tek tenant'a kilitli)"

    def add_arguments(self, parser):
        parser.add_argument("excel_file", type=str, help="Excel dosya yolu")
        parser.add_argument(
            "--confirm-tenant",
            type=str,
            required=True,
            help=f"Güvenlik için açıkça '{EXPECTED_TENANT_SLUG}' yazılmalı",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Hiçbir şey yazma, sadece neyin oluşacağını göster",
        )

    def handle(self, *args, **options):
        confirm = options["confirm_tenant"]
        if confirm != EXPECTED_TENANT_SLUG:
            raise CommandError(
                f"--confirm-tenant '{EXPECTED_TENANT_SLUG}' olmalı, '{confirm}' verildi. İptal edildi."
            )

        excel_file = options["excel_file"]
        dry_run = options["dry_run"]

        try:
            tenant = Tenant.objects.get(slug=EXPECTED_TENANT_SLUG, is_deleted=False)
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant '{EXPECTED_TENANT_SLUG}' bulunamadı")

        self.stdout.write(self.style.NOTICE(
            f"Tenant: {tenant.name} (slug={tenant.slug}, id={tenant.id})"
        ))

        df = pd.read_excel(excel_file, engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]

        missing = [c for c in EXCEL_COLUMNS if c not in df.columns]
        if missing:
            raise CommandError(
                f"Excel'de eksik kolonlar: {missing}. Bulunan kolonlar: {list(df.columns)}"
            )

        rows = df.to_dict(orient="records")
        self.stdout.write(f"Toplam satır: {len(rows)}")

        used_slugs_in_db = set(
            Product.objects.filter(tenant=tenant, is_deleted=False).values_list("slug", flat=True)
        )
        used_slugs_in_batch = set()
        brand_cache = {}

        created = 0
        skipped = 0
        errors = []
        preview = []

        try:
            with transaction.atomic():
                for idx, row in enumerate(rows, start=2):
                    name = self._clean_str(row.get("EBAT+DESEN"))
                    if not name:
                        skipped += 1
                        continue

                    qty = self._to_int(row.get("ADET"), default=0)
                    sku = self._clean_str(row.get("ÜRÜN KODU"))[:200]
                    season = self._clean_str(row.get("MEVSİM")).upper()
                    brand_name = self._clean_str(row.get("LASTİK MARKASI")).upper()
                    year = self._to_int(row.get("ÜRETİM TARİHİ"), default=None)

                    slug = self._unique_slug(name, used_slugs_in_db, used_slugs_in_batch)
                    used_slugs_in_batch.add(slug)

                    brand_item = None
                    if brand_name:
                        brand_item = self._get_or_create_brand(tenant, brand_name, brand_cache, dry_run)

                    tags = []
                    if season:
                        tags.append(season)
                    if year:
                        tags.append(str(year))

                    metadata = {"imported_from": "GÜNCEL STOK 2026.xlsx"}
                    if season:
                        metadata["season"] = season
                    if year:
                        metadata["production_year"] = year

                    product_kwargs = dict(
                        tenant=tenant,
                        name=name,
                        slug=slug,
                        price=Decimal("1.00"),
                        currency="TRY",
                        sku=sku,
                        inventory_quantity=qty,
                        track_inventory=True,
                        status="active",
                        is_visible=True,
                        brand=brand_name,
                        brand_item=brand_item,
                        tags=tags,
                        collections=[],
                        metadata=metadata,
                        specifications={},
                    )

                    if len(preview) < 5:
                        preview.append({
                            "row": idx,
                            "name": name,
                            "slug": slug,
                            "qty": qty,
                            "sku": sku,
                            "brand": brand_name,
                            "season": season,
                            "year": year,
                        })

                    try:
                        Product.objects.create(**product_kwargs)
                        created += 1
                    except Exception as exc:
                        errors.append(f"Satır {idx} ({name}): {exc}")

                if dry_run:
                    self.stdout.write(self.style.WARNING("--dry-run: değişiklikler geri alınıyor"))
                    transaction.set_rollback(True)
        except Exception as exc:
            raise CommandError(f"Import sırasında hata: {exc}")

        self.stdout.write("\n=== ÖRNEK SATIRLAR (ilk 5) ===")
        for p in preview:
            self.stdout.write(f"  {p}")

        self.stdout.write("\n=== SONUÇ ===")
        self.stdout.write(f"  Oluşturulan : {created}")
        self.stdout.write(f"  Atlanan     : {skipped} (boş EBAT+DESEN)")
        self.stdout.write(f"  Hata        : {len(errors)}")
        for e in errors[:20]:
            self.stdout.write(f"    - {e}")
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY-RUN — DB değişmedi"))
        else:
            self.stdout.write(self.style.SUCCESS("\nGerçek import tamamlandı"))

    @staticmethod
    def _clean_str(value):
        if value is None:
            return ""
        if isinstance(value, float) and pd.isna(value):
            return ""
        return str(value).strip()

    @staticmethod
    def _to_int(value, default=0):
        if value is None:
            return default
        if isinstance(value, float) and pd.isna(value):
            return default
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _unique_slug(name, used_in_db, used_in_batch):
        base = slugify(name) or "urun"
        base = base[:240]
        candidate = base
        i = 1
        while candidate in used_in_db or candidate in used_in_batch:
            i += 1
            suffix = f"-{i}"
            candidate = base[: 245 - len(suffix)] + suffix
        return candidate

    @staticmethod
    def _get_or_create_brand(tenant, brand_name, cache, dry_run):
        key = brand_name.upper()
        if key in cache:
            return cache[key]
        brand = Brand.objects.filter(tenant=tenant, name__iexact=brand_name).first()
        if brand is None:
            brand = Brand.objects.create(
                tenant=tenant,
                name=brand_name,
                slug=slugify(brand_name) or "marka",
                is_active=True,
            )
        cache[key] = brand
        return brand
