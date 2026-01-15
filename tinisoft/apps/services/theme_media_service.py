"""
Website Theme Media Upload Service
Cloudflare R2 (S3-compatible) için media yükleme
Klasör yapısı: themes/{domain}/images/, themes/{domain}/videos/
"""

import boto3
import os
from django.conf import settings
from uuid import uuid4
from datetime import datetime


class ThemeMediaService:
    """
    Tema için media (image, video) upload servisi
    Cloudflare R2'ye yükler: themes/{domain}/images/filename.jpg
    """
    
    def __init__(self):
        """S3 client oluştur (Cloudflare R2 S3-compatible)"""
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name='auto'  # Cloudflare R2 için
        )
        self.bucket_name = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL  # https://cdn.example.com
    
    def upload_image(self, file, tenant_domain, custom_filename=None):
        """
        Görsel yükle
        
        Args:
            file: UploadedFile instance
            tenant_domain: Tenant domain (örn: avrupamutfak.com)
            custom_filename: Özel dosya adı (opsiyonel)
        
        Returns:
            {
                'url': 'https://cdn.example.com/themes/avrupamutfak.com/images/hero-bg.jpg',
                'path': 'themes/avrupamutfak.com/images/hero-bg.jpg',
                'size': 1024000,
                'type': 'image/jpeg'
            }
        """
        # Dosya adı
        ext = os.path.splitext(file.name)[1].lower()
        filename = custom_filename if custom_filename else f"{uuid4()}{ext}"
        
        # S3 path
        s3_path = f"themes/{tenant_domain}/images/{filename}"
        
        # Content type
        content_type = file.content_type or 'image/jpeg'
        
        # Upload
        try:
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                s3_path,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'public-read',  # Public access
                    'CacheControl': 'max-age=31536000'  # 1 yıl cache
                }
            )
            
            # Public URL
            url = f"{self.public_url}/{s3_path}"
            
            return {
                'url': url,
                'path': s3_path,
                'size': file.size,
                'type': content_type,
                'filename': filename
            }
        
        except Exception as e:
            raise Exception(f"Upload failed: {str(e)}")
    
    def upload_video(self, file, tenant_domain, custom_filename=None):
        """
        Video yükle
        
        Args:
            file: UploadedFile instance
            tenant_domain: Tenant domain
            custom_filename: Özel dosya adı
        
        Returns:
            Upload bilgisi dict
        """
        # Dosya adı
        ext = os.path.splitext(file.name)[1].lower()
        filename = custom_filename if custom_filename else f"{uuid4()}{ext}"
        
        # S3 path
        s3_path = f"themes/{tenant_domain}/videos/{filename}"
        
        # Content type
        content_type = file.content_type or 'video/mp4'
        
        # Upload
        try:
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                s3_path,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'public-read',
                    'CacheControl': 'max-age=31536000'
                }
            )
            
            url = f"{self.public_url}/{s3_path}"
            
            return {
                'url': url,
                'path': s3_path,
                'size': file.size,
                'type': content_type,
                'filename': filename
            }
        
        except Exception as e:
            raise Exception(f"Upload failed: {str(e)}")
    
    def delete_media(self, s3_path):
        """
        Media dosyasını sil
        
        Args:
            s3_path: S3'teki path (örn: themes/avrupamutfak.com/images/hero.jpg)
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_path
            )
            return True
        except Exception as e:
            raise Exception(f"Delete failed: {str(e)}")
    
    def list_media(self, tenant_domain, media_type='images'):
        """
        Tenant'ın medyalarını listele
        
        Args:
            tenant_domain: Tenant domain
            media_type: 'images' veya 'videos'
        
        Returns:
            List of media URLs
        """
        prefix = f"themes/{tenant_domain}/{media_type}/"
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            media_list = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    media_list.append({
                        'url': f"{self.public_url}/{obj['Key']}",
                        'path': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat()
                    })
            
            return media_list
        
        except Exception as e:
            raise Exception(f"List failed: {str(e)}")


# Singleton instance
theme_media_service = ThemeMediaService()
