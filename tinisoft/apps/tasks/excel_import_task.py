"""
Excel import Celery task - Paralel ve hızlı ürün yükleme.
"""
from celery import shared_task
from django.conf import settings
from apps.services.excel_import_service import ExcelImportService
from apps.models import Product, Tenant
from core.middleware import get_tenant_from_request
from core.db_router import set_tenant_schema
import logging
import pandas as pd
import os
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def import_products_from_excel_task(self, file_path, tenant_id, user_id=None, batch_size=100):
    """
    Excel'den ürünleri paralel olarak import et (Celery task).
    
    Args:
        file_path: Excel dosya yolu
        tenant_id: Tenant ID
        user_id: User ID (opsiyonel)
        batch_size: Her batch'te kaç ürün işlenecek (default: 100)
    
    Returns:
        dict: Import sonuçları
    """
    from apps.models import User
    
    try:
        # Tenant ve user'ı al
        tenant = Tenant.objects.get(id=tenant_id, is_deleted=False)
        user = User.objects.get(id=user_id) if user_id else None
        
        # Tenant schema'sını ayarla
        tenant_schema = f'tenant_{tenant.id}'
        set_tenant_schema(tenant_schema)
        
        # Excel dosyasını local filesystem'den oku (R2'ye gitmez, sadece fotoğraflar R2'ye gider)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found in local filesystem: {file_path}")
        
        logger.info(f"Reading Excel file from local filesystem: {file_path} (NOT from R2 - only product images go to R2)")
        
        # Local filesystem'den dosyayı oku
        df = pd.read_excel(file_path, engine='openpyxl')
        df.columns = df.columns.str.lower().str.strip()
        
        total_rows = len(df)
        logger.info(f"Starting Excel import: {total_rows} rows for tenant {tenant.name}")
        
        # Batch'ler halinde işle
        imported_count = 0
        failed_count = 0
        errors = []
        products_created = []
        
        # Batch'lere böl
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            batch_df = df.iloc[batch_start:batch_end]
            
            logger.info(f"Processing batch {batch_start // batch_size + 1}: rows {batch_start + 1}-{batch_end}")
            
            # Batch'i işle
            batch_results = _process_batch(batch_df, tenant, user, batch_start)
            
            imported_count += batch_results['imported_count']
            failed_count += batch_results['failed_count']
            errors.extend(batch_results['errors'])
            products_created.extend(batch_results['products'])
            
            # Progress update (Celery task için)
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': batch_end,
                    'total': total_rows,
                    'imported': imported_count,
                    'failed': failed_count,
                    'progress': int((batch_end / total_rows) * 100)
                }
            )
        
        # Geçici dosyayı local filesystem'den sil
        if os.path.exists(file_path):
            try:
                os.unlink(file_path)
                logger.info(f"Temporary Excel file deleted from local filesystem: {file_path}")
            except Exception as e:
                logger.warning(f"Could not delete temporary file {file_path}: {str(e)}")
        
        result = {
            'success': True,
            'imported_count': imported_count,
            'failed_count': failed_count,
            'total_rows': total_rows,
            'errors': errors[:50],  # İlk 50 hatayı göster
            'products_count': len(products_created)
        }
        
        logger.info(f"Excel import completed: {imported_count} imported, {failed_count} failed")
        return result
    
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Excel import task error for tenant {tenant_id}: {str(e)}")
        logger.error(f"Traceback: {error_traceback}")
        
        # Retry count'u kontrol et
        retry_count = self.request.retries
        max_retries = self.max_retries
        
        if retry_count < max_retries:
            logger.warning(f"Retrying import task (attempt {retry_count + 1}/{max_retries})")
            raise self.retry(exc=e, countdown=60)
        else:
            logger.error(f"Max retries reached for import task. Failing permanently.")
            raise


def _process_batch(batch_df, tenant, user, row_offset):
    """
    Bir batch'i işle (transaction içinde).
    
    Args:
        batch_df: DataFrame (batch)
        tenant: Tenant instance
        user: User instance
        row_offset: Satır offset (hata mesajları için)
    
    Returns:
        dict: Batch sonuçları
    """
    imported_count = 0
    failed_count = 0
    errors = []
    products = []
    
    try:
        with transaction.atomic():
            # Her satırı işle
            for idx, row in batch_df.iterrows():
                try:
                    # Excel satırını product data'ya çevir
                    product_data = ExcelImportService._map_row_to_product_data(row, tenant)
                    
                    # Product oluştur
                    product = ExcelImportService._create_product(product_data, tenant, user)
                    products.append(product)
                    imported_count += 1
                
                except Exception as e:
                    failed_count += 1
                    row_num = row_offset + idx + 2  # +2 çünkü Excel'de header var ve 0-based index
                    error_msg = f"Satır {row_num}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"Product import error at row {row_num}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Batch processing error: {str(e)}")
        failed_count += len(batch_df)
        errors.append(f"Batch hatası: {str(e)}")
    
    return {
        'imported_count': imported_count,
        'failed_count': failed_count,
        'errors': errors,
        'products': products
    }


@shared_task
def import_products_from_excel_async(file_path, tenant_id, user_id=None):
    """
    Excel import'u async olarak başlat (wrapper task).
    """
    task = import_products_from_excel_task.delay(file_path, tenant_id, user_id)
    return {
        'task_id': task.id,
        'status': 'PENDING',
        'message': 'Excel import başlatıldı. Task ID ile durumu takip edebilirsiniz.'
    }


@shared_task(bind=True, max_retries=3)
def upload_images_from_excel_task(self, tenant_id, base_directories=None, batch_size=50):
    """
    Excel'den import edilen ürünlerin görsellerini paralel olarak yükle (Celery task).
    
    4000-5000 fotoğrafı batch'ler halinde işler ve R2'ye yükler.
    
    Args:
        tenant_id: Tenant ID
        base_directories: Local resim dizinleri (liste)
        batch_size: Her batch'te kaç ürün işlenecek (default: 50)
    
    Returns:
        dict: Upload sonuçları
    """
    from apps.models import Tenant
    from apps.services.image_path_service import ImagePathService
    
    try:
        # Tenant'ı al
        tenant = Tenant.objects.get(id=tenant_id, is_deleted=False)
        
        # Tenant schema'sını ayarla
        tenant_schema = f'tenant_{tenant.id}'
        set_tenant_schema(tenant_schema)
        
        # Tüm ürünleri al (metadata'da image_paths olanlar)
        products = Product.objects.filter(
            tenant=tenant,
            is_deleted=False
        )
        
        total_products = products.count()
        logger.info(f"Starting image upload: {total_products} products for tenant {tenant.name}")
        
        success_count = 0
        failed_count = 0
        results = []
        
        # Batch'ler halinde işle
        products_list = list(products)
        for batch_start in range(0, len(products_list), batch_size):
            batch_end = min(batch_start + batch_size, len(products_list))
            batch_products = products_list[batch_start:batch_end]
            
            logger.info(f"Processing image batch {batch_start // batch_size + 1}: products {batch_start + 1}-{batch_end}")
            
            # Batch'i işle
            batch_results = _process_image_batch(batch_products, base_directories)
            
            success_count += batch_results['success_count']
            failed_count += batch_results['failed_count']
            results.extend(batch_results['results'])
            
            # Progress update
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': batch_end,
                    'total': total_products,
                    'success': success_count,
                    'failed': failed_count,
                    'progress': int((batch_end / total_products) * 100) if total_products > 0 else 0
                }
            )
        
        result = {
            'success': True,
            'success_count': success_count,
            'failed_count': failed_count,
            'total_products': total_products,
            'results': results[:100],  # İlk 100 sonucu göster
        }
        
        logger.info(f"Image upload completed: {success_count} uploaded, {failed_count} failed")
        return result
    
    except Exception as e:
        logger.error(f"Image upload task error: {str(e)}")
        raise self.retry(exc=e, countdown=60)


def _process_image_batch(batch_products, base_directories):
    """
    Bir batch ürünün görsellerini işle.
    
    Args:
        batch_products: Product listesi (batch)
        base_directories: Local resim dizinleri
    
    Returns:
        dict: Batch sonuçları
    """
    from apps.services.image_path_service import ImagePathService
    
    success_count = 0
    failed_count = 0
    results = []
    
    for product in batch_products:
        # Metadata'dan image path'leri al
        image_paths = product.metadata.get('image_paths', [])
        
        if not image_paths:
            continue
        
        # Her resim yolunu işle
        for idx, image_path in enumerate(image_paths[:10]):  # MAX_IMAGES_PER_PRODUCT = 10
            # Local'de bul
            local_path = ImagePathService.find_local_image(image_path, base_directories)
            
            if not local_path:
                failed_count += 1
                results.append({
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
                success_count += 1
                results.append({
                    'product_slug': product.slug,
                    'image_path': image_path,
                    'local_path': local_path,
                    'image_url': product_image.image_url,
                    'status': 'success'
                })
            else:
                failed_count += 1
                results.append({
                    'product_slug': product.slug,
                    'image_path': image_path,
                    'status': 'upload_failed',
                    'error': 'Yükleme başarısız'
                })
    
    return {
        'success_count': success_count,
        'failed_count': failed_count,
        'results': results
    }

