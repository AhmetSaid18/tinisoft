"""
Theme Media Upload Views
Görsel ve video yükleme endpoint'leri
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from apps.permissions import IsTenantUser
from apps.services.theme_media_service import theme_media_service


class ThemeMediaUploadView(APIView):
    """
    POST /api/v1/tenant/website/media/upload/
    
    Tema için görsel/video yükle
    Cloudflare R2'ye upload: themes/{domain}/images/ veya themes/{domain}/videos/
    
    Form Data:
        - file: File (image or video)
        - type: "image" veya "video"
        - custom_filename: Opsiyonel özel dosya adı
    
    Response:
        {
            "url": "https://cdn.example.com/themes/avrupamutfak.com/images/hero-bg.jpg",
            "path": "themes/avrupamutfak.com/images/hero-bg.jpg",
            "size": 1024000,
            "type": "image/jpeg",
            "filename": "hero-bg.jpg"
        }
    """
    
    permission_classes = [IsAuthenticated, IsTenantUser]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Upload media file"""
        file = request.FILES.get('file')
        media_type = request.data.get('type', 'image')  # 'image' veya 'video'
        custom_filename = request.data.get('custom_filename')
        
        if not file:
            return Response(
                {"error": "File gerekli."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Tenant domain
        tenant = request.user.tenant
        domain = tenant.domain if hasattr(tenant, 'domain') else f"{tenant.slug}.example.com"
        
        # File type validation
        if media_type == 'image':
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
            max_size = 10 * 1024 * 1024  # 10MB
        elif media_type == 'video':
            allowed_extensions = ['.mp4', '.webm', '.mov', '.avi']
            max_size = 100 * 1024 * 1024  # 100MB
        else:
            return Response(
                {"error": "type 'image' veya 'video' olmalı."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extension check
        import os
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in allowed_extensions:
            return Response(
                {"error": f"Desteklenmeyen dosya formatı. İzin verilenler: {', '.join(allowed_extensions)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Size check
        if file.size > max_size:
            return Response(
                {"error": f"Dosya boyutu çok büyük. Maksimum: {max_size // 1024 // 1024}MB"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Upload
        try:
            if media_type == 'image':
                result = theme_media_service.upload_image(file, domain, custom_filename)
            else:
                result = theme_media_service.upload_video(file, domain, custom_filename)
            
            return Response(result, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {"error": f"Upload başarısız: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ThemeMediaListView(APIView):
    """
    GET /api/v1/tenant/website/media/list/?type=images
    
    Tenant'ın yüklediği medyaları listele
    
    Query Parameters:
        - type: "images" veya "videos" (default: images)
    
    Response:
        {
            "media": [
                {
                    "url": "https://cdn.example.com/themes/avrupamutfak.com/images/logo.png",
                    "path": "themes/avrupamutfak.com/images/logo.png",
                    "size": 45000,
                    "last_modified": "2024-01-16T01:00:00Z"
                }
            ]
        }
    """
    
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def get(self, request):
        """List uploaded media"""
        media_type = request.query_params.get('type', 'images')
        
        if media_type not in ['images', 'videos']:
            return Response(
                {"error": "type 'images' veya 'videos' olmalı."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Tenant domain
        tenant = request.user.tenant
        domain = tenant.domain if hasattr(tenant, 'domain') else f"{tenant.slug}.example.com"
        
        try:
            media_list = theme_media_service.list_media(domain, media_type)
            
            return Response({
                'media': media_list,
                'count': len(media_list)
            })
        
        except Exception as e:
            return Response(
                {"error": f"Liste alınamadı: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ThemeMediaDeleteView(APIView):
    """
    DELETE /api/v1/tenant/website/media/delete/
    
    Yüklenen medyayı sil (Tekli veya Çoklu)
    
    Request Body:
        {
            "paths": [
                "themes/avrupamutfak.com/images/1.jpg",
                "themes/avrupamutfak.com/images/2.jpg"
            ]
        }
        OR (Legacy)
        {
            "path": "themes/avrupamutfak.com/images/1.jpg"
        }
    """
    
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def delete(self, request):
        """Delete media file(s)"""
        s3_path = request.data.get('path')
        s3_paths = request.data.get('paths')
        
        # Normalize input to list
        paths_to_delete = []
        if s3_paths and isinstance(s3_paths, list):
            paths_to_delete = s3_paths
        elif s3_path:
            paths_to_delete = [s3_path]
            
        if not paths_to_delete:
            return Response(
                {"error": "path veya paths gerekli."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Tenant domain validation setup
        tenant = request.user.tenant
        domain = tenant.domain if hasattr(tenant, 'domain') else f"{tenant.slug}"
        # Basit slug check yeterli mi? R2 path formatı: themes/{domain}/...
        # Eğer domain yoksa slug kullanılır dedik upload'da. 
        # Upload: domain = tenant.domain if hasattr(tenant, 'domain') else f"{tenant.slug}.example.com"
        # Biz burada prefix kontrolü yapıyoruz.
        
        # Domain tam olarak neyse prefix odur.
        # En güvenli yöntem: Path içinde "themes/" var ve sonra tenant slug veya domain geçiyor mu?
        # Şimdilik upload mantığıyla aynı domaini alalım
        upload_domain_ref = tenant.domain if hasattr(tenant, 'domain') else f"{tenant.slug}.example.com"
        expected_prefix = f"themes/{upload_domain_ref}/"

        deleted_count = 0
        errors = []
        
        for path in paths_to_delete:
            # Security check per file
            if not path.startswith(expected_prefix):
                errors.append(f"Yetkisiz erişim: {path}")
                continue
                
            try:
                theme_media_service.delete_media(path)
                deleted_count += 1
            except Exception as e:
                errors.append(f"Silinemedi {path}: {str(e)}")
        
        return Response({
            "message": f"{deleted_count} dosya başarıyla silindi.",
            "deleted_count": deleted_count,
            "errors": errors if errors else None
        })
