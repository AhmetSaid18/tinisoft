"""
Product Excel Import views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.conf import settings
from apps.services.excel_import_service import ExcelImportService
from apps.serializers.product import ProductListSerializer
from apps.tasks.excel_import_task import import_products_from_excel_task, import_products_from_excel_async
from core.middleware import get_tenant_from_request
from celery.result import AsyncResult
import logging
import os
import tempfile

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def import_products_from_excel(request):
    """
    Excel dosyasından ürünleri import et.
    Büyük dosyalar için async (Celery) kullanır, küçük dosyalar için sync.
    
    POST: /api/products/import/
    Content-Type: multipart/form-data
    Body: {
        "file": <excel_file>,
        "async": true  // Opsiyonel, async işlem için (default: false, 1000+ satır için otomatik async)
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
    
    # Dosya kontrolü
    if 'file' not in request.FILES:
        return Response({
            'success': False,
            'message': 'Excel dosyası yüklenmedi.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    excel_file = request.FILES['file']
    
    # Dosya uzantısı kontrolü
    if not excel_file.name.endswith(('.xlsx', '.xls')):
        return Response({
            'success': False,
            'message': 'Sadece Excel dosyaları (.xlsx, .xls) kabul edilir.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Dosya boyutu kontrolü (100 MB limit)
    max_file_size = 100 * 1024 * 1024  # 100 MB
    if excel_file.size > max_file_size:
        return Response({
            'success': False,
            'message': f'Dosya boyutu çok büyük. Maksimum {max_file_size / (1024*1024):.0f} MB kabul edilir. Mevcut dosya: {excel_file.size / (1024*1024):.2f} MB',
            'file_size': excel_file.size,
            'max_size': max_file_size,
        }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    
    # Async işlem kontrolü
    use_async = request.data.get('async', False)
    
    # Dosya boyutuna göre otomatik async (1000+ satır için)
    try:
        import pandas as pd
        import io
        excel_file.seek(0)
        df = pd.read_excel(excel_file, engine='openpyxl', nrows=0)  # Sadece header oku
        total_rows = len(pd.read_excel(excel_file, engine='openpyxl'))  # Toplam satır sayısı
        excel_file.seek(0)
        
        # 1000+ satır varsa otomatik async
        if total_rows >= 1000:
            use_async = True
    except:
        total_rows = 0
    
    # Geçici dosya olarak kaydet (LOCAL FILESYSTEM - R2'ye gitmez, sadece fotoğraflar R2'ye gider)
    temp_file_path = None
    try:
        # Excel dosyasını local filesystem'e kaydet (Docker volume paylaşıldığı için Celery worker erişebilir)
        import uuid
        from django.utils import timezone
        
        # Local temp dizini oluştur
        temp_dir = os.path.join(settings.BASE_DIR, 'temp_imports', str(tenant.id))
        os.makedirs(temp_dir, exist_ok=True)
        
        # Dosya adı: {timestamp}_{uuid}.xlsx
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        file_uuid = str(uuid.uuid4())[:8]
        filename = f'{timestamp}_{file_uuid}.xlsx'
        temp_file_path = os.path.join(temp_dir, filename)
        
        # Dosyayı local filesystem'e kaydet
        excel_file.seek(0)
        with open(temp_file_path, 'wb') as f:
            for chunk in excel_file.chunks():
                f.write(chunk)
        
        logger.info(f"Excel file saved to local temp storage: {temp_file_path} (NOT to R2 - only product images go to R2) for tenant {tenant.name}")
        
        # Async işlem
        if use_async:
            # Celery task başlat
            task = import_products_from_excel_task.delay(
                file_path=temp_file_path,  # Storage path
                tenant_id=str(tenant.id),
                user_id=str(request.user.id) if request.user else None,
                batch_size=100  # Her batch'te 100 ürün
            )
            
            return Response({
                'success': True,
                'message': f'Excel import başlatıldı ({total_rows} satır). Task ID ile durumu takip edebilirsiniz.',
                'task_id': task.id,
                'status': 'PENDING',
                'total_rows': total_rows,
                'async': True,
                'check_status_url': f'/api/products/import/status/{task.id}/'
            }, status=status.HTTP_202_ACCEPTED)
        
        # Sync işlem (küçük dosyalar için)
        else:
            result = ExcelImportService.import_products_from_excel(
                file_path=temp_file_path,  # Storage path
                tenant=tenant,
                user=request.user
            )
            
            if result['success']:
                # Başarılı ürünleri serialize et
                products_data = []
                if result['products']:
                    serializer = ProductListSerializer(result['products'], many=True)
                    products_data = serializer.data
                
                response_data = {
                    'success': True,
                    'message': f"{result['imported_count']} ürün başarıyla import edildi.",
                    'imported_count': result['imported_count'],
                    'failed_count': result['failed_count'],
                    'errors': result['errors'][:10],  # İlk 10 hatayı göster
                    'products': products_data[:20],  # İlk 20 ürünü göster
                }
                
                if result['failed_count'] > 0:
                    response_data['message'] += f" {result['failed_count']} ürün import edilemedi."
                
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Import işlemi başarısız.',
                    'errors': result['errors'],
                }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Excel import error: {str(e)}")
        return Response({
            'success': False,
            'message': f'Import hatası: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    finally:
        # Sync işlemde geçici dosyayı sil (async'te task siler)
        if not use_async and temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"Temporary Excel file deleted: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Could not delete temporary file {temp_file_path}: {str(e)}")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def import_status(request, task_id):
    """
    Excel import task durumunu kontrol et.
    
    GET: /api/products/import/status/{task_id}/
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
    
    try:
        # Task durumunu al
        task_result = AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = {
                'success': True,
                'status': 'PENDING',
                'message': 'Import işlemi bekleniyor...',
            }
        elif task_result.state == 'PROGRESS':
            response = {
                'success': True,
                'status': 'PROGRESS',
                'message': 'Import işlemi devam ediyor...',
                'progress': task_result.info.get('progress', 0),
                'current': task_result.info.get('current', 0),
                'total': task_result.info.get('total', 0),
                'imported': task_result.info.get('imported', 0),
                'failed': task_result.info.get('failed', 0),
            }
        elif task_result.state == 'SUCCESS':
            result = task_result.result
            response = {
                'success': True,
                'status': 'SUCCESS',
                'message': f"Import tamamlandı! {result.get('imported_count', 0)} ürün başarıyla import edildi.",
                'imported_count': result.get('imported_count', 0),
                'failed_count': result.get('failed_count', 0),
                'total_rows': result.get('total_rows', 0),
                'errors': result.get('errors', [])[:20],  # İlk 20 hatayı göster
            }
        elif task_result.state == 'FAILURE':
            error_info = task_result.info
            if isinstance(error_info, Exception):
                error_message = str(error_info)
                error_traceback = getattr(error_info, '__traceback__', None)
            else:
                error_message = str(error_info)
                error_traceback = None
            
            response = {
                'success': False,
                'status': 'FAILURE',
                'message': 'Import işlemi başarısız oldu.',
                'error': error_message,
                'traceback': str(error_traceback) if error_traceback else None,
            }
        elif task_result.state in ['RETRY', 'REVOKED']:
            error_info = task_result.info
            if isinstance(error_info, Exception):
                error_message = str(error_info)
            else:
                error_message = str(error_info) if error_info else 'Bilinmeyen hata'
            
            response = {
                'success': False,
                'status': task_result.state,
                'message': f'Import işlemi {task_result.state} durumunda. Hata nedeniyle yeniden deneniyor veya iptal edildi.',
                'error': error_message,
                'retry_count': getattr(task_result, 'retries', 0),
                'max_retries': getattr(task_result, 'max_retries', 3),
            }
        else:
            response = {
                'success': True,
                'status': task_result.state,
                'message': f'Task durumu: {task_result.state}',
                'info': str(task_result.info) if task_result.info else None,
            }
        
        return Response(response, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Import status check error: {str(e)}")
        return Response({
            'success': False,
            'message': f'Durum kontrolü hatası: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def excel_template_download(request):
    """
    Excel import template dosyasını indir.
    
    GET: /api/products/import/template/
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
    
    try:
        import openpyxl
        from django.http import HttpResponse
        
        # Yeni workbook oluştur
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Ürünler"
        
        # Header satırı
        headers = [
            'Ürün Adı',
            'Açıklama',
            'Fiyat',
            'Karşılaştırma Fiyatı',
            'SKU',
            'Barkod',
            'Stok',
            'Stok Takibi (Evet/Hayır)',
            'Kategori',
            'Durum (active/draft/archived)',
            'Görünür (Evet/Hayır)',
            'Öne Çıkan (Evet/Hayır)',
            'Yeni (Evet/Hayır)',
            'Çok Satan (Evet/Hayır)',
            'Meta Başlık',
            'Meta Açıklama',
            'Meta Anahtar Kelimeler',
            'Ağırlık (kg)',
            'Uzunluk (cm)',
            'Genişlik (cm)',
            'Yükseklik (cm)',
            'Görsel URL',
            'Görseller (virgülle ayrılmış)',
            'Etiketler (virgülle ayrılmış)',
            'Sıra',
        ]
        
        ws.append(headers)
        
        # Örnek satır
        example_row = [
            'Örnek Ürün',
            'Bu bir örnek ürün açıklamasıdır',
            '100.00',
            '120.00',
            'SKU-001',
            '1234567890123',
            '50',
            'Evet',
            'Elektronik',
            'active',
            'Evet',
            'Hayır',
            'Evet',
            'Hayır',
            'Örnek Ürün - SEO Başlık',
            'SEO açıklama',
            'ürün, elektronik, örnek',
            '1.5',
            '30',
            '20',
            '10',
            'https://example.com/image.jpg',
            'https://example.com/img1.jpg,https://example.com/img2.jpg',
            'yeni,popüler,indirim',
            '0',
        ]
        ws.append(example_row)
        
        # Kolon genişliklerini ayarla
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Response oluştur
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="urun_import_template.xlsx"'
        
        wb.save(response)
        return response
    
    except Exception as e:
        logger.error(f"Template download error: {str(e)}")
        return Response({
            'success': False,
            'message': f'Template oluşturma hatası: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

