"""
Product Image Upload from Excel - Excel'den import edilen ürünlerin resimlerini yükle.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.services.image_path_service import ImagePathService
from apps.tasks.excel_import_task import upload_images_from_excel_task
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_images_from_excel_paths(request):
    """
    Excel'den import edilen ürünlerin ImageName kolonlarından resimleri yükle.
    
    NASIL ÇALIŞIR:
    1. Excel import edildiğinde ImageName1-10 kolonları metadata'da saklanır
       Örnek: "resimler/remta-st23-elegance-dijital-serbet-ve-ayran-sogutucu-20-l-gold-6112.jpg"
    
    2. Bu endpoint çağrıldığında:
       - Her ürünün metadata'sındaki ImageName path'lerini alır
       - Local PC'de bu dosyaları arar (base_directories'de)
       - Bulunan dosyaları R2'ye yükler
       - ProductImage oluşturur ve ürüne bağlar
    
    3. Eşleştirme:
       - Excel ImageName: "resimler/remta-st23-elegance...jpg"
       - Local'de arar: "resimler/remta-st23-elegance...jpg" veya sadece dosya adı
       - Bulursa R2'ye yükler: "{tenant_id}/products/{product_id}/remta-st23-elegance...jpg"
    
    POST: /api/products/images/upload-from-excel/
    Body: {
        "base_directories": ["C:/resimler", "D:/fotograflar", "images", "resimler"]  
        // Opsiyonel, local resim dizinleri (absolute path veya relative path)
        // Eğer verilmezse varsayılan dizinlerde arar: images, resimler, photos, pictures, .
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece tenant owner veya admin
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    base_directories = request.data.get('base_directories', None)
    async_mode = request.data.get('async', True)  # Default: async (büyük miktarlar için)
    
    # 4000-5000 fotoğraf için async mode önerilir
    if async_mode:
        try:
            # Celery task olarak başlat (async)
            task = upload_images_from_excel_task.delay(
                tenant_id=str(tenant.id),
                base_directories=base_directories,
                batch_size=50  # Her batch'te 50 ürün işle
            )
            
            return Response({
                'success': True,
                'message': 'Görsel yükleme başlatıldı. Task ID ile durumu takip edebilirsiniz.',
                'task_id': task.id,
                'status': 'PENDING',
                'async': True,
                'endpoint': f'/api/tasks/{task.id}/status/'  # Task durumu için endpoint
            }, status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            logger.error(f"Async image upload task error: {str(e)}")
            return Response({
                'success': False,
                'message': f'Görsel yükleme task hatası: {str(e)}',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        # Senkron mode (küçük miktarlar için)
        try:
            results = ImagePathService.upload_images_from_excel_paths(
                tenant=tenant,
                base_directories=base_directories
            )
            
            return Response({
                'success': True,
                'message': f'{results["success_count"]} resim başarıyla yüklendi, {results["failed_count"]} resim yüklenemedi.',
                'results': results,
                'async': False,
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Upload images from excel error: {str(e)}")
            return Response({
                'success': False,
                'message': f'Resim yükleme hatası: {str(e)}',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

