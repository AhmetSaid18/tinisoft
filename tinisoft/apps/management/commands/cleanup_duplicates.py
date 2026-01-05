from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.models import ProductImage
import logging

class Command(BaseCommand):
    help = 'Duplicate ürün görsellerini bulur ve temizler (aynı product_id ve image_url)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece duplicate olanları listele, silme.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("Duplicate görseller aranıyor...")
        
        # URL ve Product bazlı gruplama yapıp, sayısı 1'den fazla olanları bulalım
        duplicates = ProductImage.objects.filter(is_deleted=False).values(
            'product_id', 'image_url'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if not duplicates.exists():
            self.stdout.write(self.style.SUCCESS("✓ HİÇ DUPLICATE GÖRSEL BULUNAMADI! Veritabanı temiz."))
            return

        self.stdout.write(self.style.WARNING(f"\n⚠ TOPLAM {duplicates.count()} ADET DUPLICATE GRUBU BULUNDU!\n"))
        
        total_deleted = 0
        
        for item in duplicates:
            product_id = item['product_id']
            image_url = item['image_url']
            
            # Gruptaki tüm resimleri al (created_at'e göre eskiden yeniye)
            images = ProductImage.objects.filter(
                product_id=product_id, 
                image_url=image_url, 
                is_deleted=False
            ).order_by('created_at')
            
            # İlkini (en eskisini) veya is_primary olanı sakla, diğerlerini sil
            # Eğer primary olan varsa onu koru
            primary_images = images.filter(is_primary=True)
            
            if primary_images.exists():
                keep_image = primary_images.first()
            else:
                keep_image = images.first()
                
            self.stdout.write(f"Ürün: {product_id} | URL: {image_url}")
            self.stdout.write(f"  → Toplam {images.count()} kopya. KORUNACAK ID: {keep_image.id}")
            
            # Silinecekler (keep_image dışındakiler)
            images_to_delete = images.exclude(id=keep_image.id)
            
            for img in images_to_delete:
                if dry_run:
                    self.stdout.write(f"  [DRY-RUN] Silinecek ID: {img.id}")
                else:
                    # Hard delete yapıyoruz çünkü bunlar gereksiz kopya
                    img.delete()
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Silindi ID: {img.id}"))
                    total_deleted += 1
            
            print("-" * 30)

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"\n[DRY-RUN] Tamamlandı. Silme işlemi yapılmadı."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✓ TEMİZLİK TAMAMLANDI! Toplam silinen kayıt: {total_deleted}"))
