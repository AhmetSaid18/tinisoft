"""
10 fotoğraflı bir ürün bul ve API response'unu test et.
"""
import os
import sys
import django
import requests
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tinisoft.settings')
django.setup()

from apps.models import Product, ProductImage, Tenant
from core.db_router import set_tenant_schema
from django.db import connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_product_with_10_images(tenant_slug='avrupamutfak'):
    """
    10 fotoğraflı bir ürün bul.
    """
    # Tenant'ı bul
    tenant = Tenant.objects.filter(slug=tenant_slug, is_deleted=False).first()
    if not tenant:
        tenant = Tenant.objects.filter(subdomain=tenant_slug, is_deleted=False).first()
    
    if not tenant:
        logger.error(f"Tenant bulunamadı: {tenant_slug}")
        return None
    
    # Schema'yı set et
    schema = f"tenant_{tenant.subdomain}"
    set_tenant_schema(schema)
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{schema}", public;')
    
    # Metadata'da 10 image_path olan bir ürün bul
    products = Product.objects.filter(tenant=tenant, is_deleted=False)
    
    for product in products:
        image_paths = product.metadata.get('image_paths', [])
        if len(image_paths) >= 10:
            logger.info("="*60)
            logger.info(f"ÜRÜN BULUNDU: {product.name}")
            logger.info(f"Slug: {product.slug}")
            logger.info(f"ID: {product.id}")
            logger.info(f"Metadata'da {len(image_paths)} image_path var")
            
            # ProductImage kayıtları
            existing_images = product.images.filter(is_deleted=False).order_by('position', 'created_at')
            logger.info(f"ProductImage'da {existing_images.count()} kayıt var")
            logger.info("="*60)
            
            return product
    
    logger.warning("10 fotoğraflı ürün bulunamadı!")
    return None


def test_api_response(product_slug, tenant_slug='avrupamutfak', api_base_url='https://api.tinisoft.com.tr'):
    """
    API'den ürün detayını çek ve görselleri kontrol et.
    """
    # API endpoint'leri dene
    endpoints = [
        f"{api_base_url}/api/public/products/urun/{product_slug}/?tenant_slug={tenant_slug}",
        f"{api_base_url}/api/public/{tenant_slug}/products/urun/{product_slug}/",
        f"{api_base_url}/api/public/products/{product_slug}/?tenant_slug={tenant_slug}",
        f"{api_base_url}/api/public/{tenant_slug}/products/{product_slug}/",
    ]
    
    for endpoint in endpoints:
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST: {endpoint}")
        logger.info("="*60)
        
        try:
            response = requests.get(endpoint, timeout=10)
            logger.info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Response yapısını kontrol et
                if 'product' in data:
                    product_data = data['product']
                elif 'success' in data and data.get('success'):
                    product_data = data.get('product', data)
                else:
                    product_data = data
                
                # Görselleri kontrol et
                images = product_data.get('images', [])
                logger.info(f"\nAPI Response'da {len(images)} görsel var:")
                
                for idx, img in enumerate(images, 1):
                    if isinstance(img, dict):
                        logger.info(f"  [{idx}] {img.get('image_url', img.get('url', 'N/A'))}")
                        logger.info(f"      Position: {img.get('position', 'N/A')}")
                        logger.info(f"      Primary: {img.get('is_primary', 'N/A')}")
                    else:
                        logger.info(f"  [{idx}] {img}")
                
                # Response'un tamamını göster (ilk 2000 karakter)
                logger.info(f"\n{'='*60}")
                logger.info("API RESPONSE (ilk 2000 karakter):")
                logger.info("="*60)
                response_str = json.dumps(product_data, indent=2, ensure_ascii=False)
                logger.info(response_str[:2000])
                if len(response_str) > 2000:
                    logger.info(f"\n... ({len(response_str) - 2000} karakter daha)")
                
                return product_data
            
            else:
                logger.error(f"API Error: {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
        
        except Exception as e:
            logger.error(f"Request Error: {str(e)}")
            continue
    
    return None


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='10 fotoğraflı ürün bul ve API test et')
    parser.add_argument('--tenant-slug', type=str, default='avrupamutfak', help='Tenant slug')
    parser.add_argument('--api-url', type=str, default='https://api.tinisoft.com.tr', help='API base URL')
    parser.add_argument('--product-slug', type=str, help='Belirli bir ürün slug\'ı test et')
    
    args = parser.parse_args()
    
    if args.product_slug:
        # Belirli bir ürünü test et
        logger.info(f"Belirtilen ürün test ediliyor: {args.product_slug}")
        test_api_response(args.product_slug, args.tenant_slug, args.api_url)
    else:
        # 10 fotoğraflı ürün bul ve test et
        product = find_product_with_10_images(args.tenant_slug)
        if product:
            test_api_response(product.slug, args.tenant_slug, args.api_url)
        else:
            logger.error("10 fotoğraflı ürün bulunamadı, test edilemedi!")

