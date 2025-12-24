"""
Image path service - Local'deki resimleri bulup yükleme.
Excel'deki ImageName kolonlarından resim yollarını çıkarıp local'den bulur.
"""
import os
from pathlib import Path
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from apps.models import Product, ProductImage
import logging

logger = logging.getLogger(__name__)

MAX_IMAGES_PER_PRODUCT = 10


class ImagePathService:
    """Local resim yolu servisi."""
    
    @staticmethod
    def find_local_image(image_path, base_directories=None):
        """
        Local'deki resmi bul.
        
        Excel'deki ImageName kolonundan gelen path'i kullanarak local'deki dosyayı bulur.
        Örnek: Excel'de "resimler/remta-st23-elegance...jpg" varsa,
        local'de "resimler/remta-st23-elegance...jpg" veya sadece dosya adını arar.
        
        Args:
            image_path: Resim yolu (örn: resimler/remta-st23-elegance-dijital-serbet-ve-ayran-sogutucu-20-l-gold-6112.jpg)
            base_directories: Arama yapılacak dizinler (liste). None ise varsayılan dizinler kullanılır.
        
        Returns:
            str: Bulunan dosya yolu (absolute path) veya None
        """
        if base_directories is None:
            # Varsayılan dizinler - local PC'deki resim klasörleri
            base_directories = [
                'images',
                'resimler',
                'photos',
                'pictures',
                'fotograflar',
                'fotoğraflar',
                '.',  # Mevcut dizin
            ]
        
        # Path'i normalize et (Windows \ -> /)
        image_path = str(image_path).replace('\\', '/').strip()
        
        # Dosya adını çıkar (örn: remta-st23-elegance...jpg)
        filename = os.path.basename(image_path)
        
        # Her dizinde ara
        for base_dir in base_directories:
            # 1. Tam path ile dene (örn: resimler/remta-st23-elegance...jpg)
            full_path = os.path.join(base_dir, image_path)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                return os.path.abspath(full_path)
            
            # 2. Base dir + filename ile dene (örn: resimler/remta-st23-elegance...jpg)
            filename_path = os.path.join(base_dir, filename)
            if os.path.exists(filename_path) and os.path.isfile(filename_path):
                return os.path.abspath(filename_path)
            
            # 3. Recursive arama - Alt dizinlerde dosya adını ara
            if os.path.isdir(base_dir):
                for root, dirs, files in os.walk(base_dir):
                    if filename in files:
                        found_path = os.path.join(root, filename)
                        return os.path.abspath(found_path)
        
        return None
    
    @staticmethod
    def upload_image_from_local(product, local_image_path, position=None, is_primary=None):
        """
        Local'deki resmi yükle ve ProductImage oluştur.
        
        Args:
            product: Product instance
            local_image_path: Local dosya yolu
            position: Görsel pozisyonu (opsiyonel)
            is_primary: Primary görsel mi? (opsiyonel)
        
        Returns:
            ProductImage instance veya None
        """
        if not os.path.exists(local_image_path):
            logger.warning(f"Image not found: {local_image_path}")
            return None
        
        # Maksimum görsel sayısı kontrolü
        existing_images_count = product.images.filter(is_deleted=False).count()
        if existing_images_count >= MAX_IMAGES_PER_PRODUCT:
            logger.warning(f"Product {product.slug} has reached max images limit ({MAX_IMAGES_PER_PRODUCT})")
            return None
        
        try:
            # Dosyayı oku
            with open(local_image_path, 'rb') as f:
                file_content = f.read()
            
            # Dosya adı
            filename = os.path.basename(local_image_path)
            
            # Storage'a kaydet - Tenant bazlı klasör yapısı: {tenant_id}/products/{product_id}/{filename}
            tenant_id = str(product.tenant.id)
            file_path = f'{tenant_id}/products/{product.id}/{filename}'
            saved_path = default_storage.save(file_path, ContentFile(file_content))
            file_url = default_storage.url(saved_path)
            
            # Position belirle
            if position is None:
                position = existing_images_count
            
            # Primary belirle
            if is_primary is None:
                is_primary = (position == 0)
            
            # ProductImage oluştur
            product_image = ProductImage.objects.create(
                product=product,
                image_url=file_url,
                alt_text=product.name,
                position=position,
                is_primary=is_primary
            )
            
            return product_image
        
        except Exception as e:
            logger.error(f"Image upload error for {local_image_path}: {str(e)}")
            return None
    
    @staticmethod
    def upload_images_from_excel_paths(tenant, base_directories=None):
        """
        Excel'den import edilen ürünlerin ImageName'lerinden resimleri yükle.
        
        Args:
            tenant: Tenant instance
            base_directories: Local resim dizinleri
        
        Returns:
            dict: {
                'success_count': int,
                'failed_count': int,
                'results': list
            }
        """
        results = {
            'success_count': 0,
            'failed_count': 0,
            'results': [],
        }
        
        # Tüm ürünleri al (metadata'da image_paths olanlar)
        products = Product.objects.filter(
            tenant=tenant,
            is_deleted=False
        )
        
        for product in products:
            # Metadata'dan image path'leri al
            image_paths = product.metadata.get('image_paths', [])
            
            if not image_paths:
                continue
            
            # Her resim yolunu işle
            for idx, image_path in enumerate(image_paths[:MAX_IMAGES_PER_PRODUCT]):
                # Local'de bul
                local_path = ImagePathService.find_local_image(image_path, base_directories)
                
                if not local_path:
                    results['failed_count'] += 1
                    results['results'].append({
                        'product_slug': product.slug,
                        'image_path': image_path,
                        'status': 'not_found',
                        'error': 'Local resim bulunamadı'
                    })
                    continue
                
                # Yükle
                product_image = ImagePathService.upload_image_from_local(
                    product=product,
                    local_image_path=local_path,
                    position=idx,
                    is_primary=(idx == 0)
                )
                
                if product_image:
                    results['success_count'] += 1
                    results['results'].append({
                        'product_slug': product.slug,
                        'image_path': image_path,
                        'local_path': local_path,
                        'image_url': product_image.image_url,
                        'status': 'success'
                    })
                else:
                    results['failed_count'] += 1
                    results['results'].append({
                        'product_slug': product.slug,
                        'image_path': image_path,
                        'status': 'upload_failed',
                        'error': 'Yükleme başarısız'
                    })
        
        return results

