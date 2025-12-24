"""
Product Excel Import views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from apps.services.excel_import_service import ExcelImportService
from apps.serializers.product import ProductListSerializer
from core.middleware import get_tenant_from_request
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
    
    POST: /api/products/import/
    Content-Type: multipart/form-data
    Body: {
        "file": <excel_file>
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
    
    # Geçici dosya olarak kaydet
    temp_file = None
    try:
        # Geçici dosya oluştur
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            for chunk in excel_file.chunks():
                tmp.write(chunk)
            temp_file = tmp.name
        
        # Import işlemi
        result = ExcelImportService.import_products_from_excel(
            file_path=temp_file,
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
        # Geçici dosyayı sil
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass


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

