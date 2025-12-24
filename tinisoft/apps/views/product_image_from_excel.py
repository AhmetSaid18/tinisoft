"""
Product Image Upload from Excel - Excel'den import edilen ürünlerin resimlerini yükle.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.services.image_path_service import ImagePathService
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_images_from_excel_paths(request):
    """
    Excel'den import edilen ürünlerin ImageName kolonlarından resimleri yükle.
    Local'deki resimleri bulup R2'ye yükler.
    
    POST: /api/products/images/upload-from-excel/
    Body: {
        "base_directories": ["images", "resimler", "photos"]  // Opsiyonel, local resim dizinleri
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
    
    try:
        # Excel'den import edilen ürünlerin resimlerini yükle
        results = ImagePathService.upload_images_from_excel_paths(
            tenant=tenant,
            base_directories=base_directories
        )
        
        return Response({
            'success': True,
            'message': f'{results["success_count"]} resim başarıyla yüklendi, {results["failed_count"]} resim yüklenemedi.',
            'results': results,
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Upload images from excel error: {str(e)}")
        return Response({
            'success': False,
            'message': f'Resim yükleme hatası: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

