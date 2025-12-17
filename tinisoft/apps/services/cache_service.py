"""
Cache service - Redis cache yönetimi.
İkas benzeri cache sistemi.
"""
import json
import logging
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Cache business logic."""
    
    # Cache key prefix'leri
    CACHE_PREFIX_PRODUCT = 'product'
    CACHE_PREFIX_CATEGORY = 'category'
    CACHE_PREFIX_CART = 'cart'
    CACHE_PREFIX_ORDER = 'order'
    CACHE_PREFIX_CUSTOMER = 'customer'
    CACHE_PREFIX_ANALYTICS = 'analytics'
    
    # Cache timeout'ları (saniye)
    TIMEOUT_PRODUCT = 3600  # 1 saat
    TIMEOUT_CATEGORY = 7200  # 2 saat
    TIMEOUT_CART = 1800  # 30 dakika
    TIMEOUT_ORDER = 3600  # 1 saat
    TIMEOUT_CUSTOMER = 1800  # 30 dakika
    TIMEOUT_ANALYTICS = 300  # 5 dakika
    
    @staticmethod
    def get_cache_key(prefix, tenant_id, *args):
        """Cache key oluştur."""
        key_parts = [prefix, str(tenant_id)] + [str(arg) for arg in args]
        return ':'.join(key_parts)
    
    @staticmethod
    def get_product(tenant_id, product_id):
        """Ürün cache'den al."""
        cache_key = CacheService.get_cache_key(
            CacheService.CACHE_PREFIX_PRODUCT,
            tenant_id,
            product_id
        )
        return cache.get(cache_key)
    
    @staticmethod
    def set_product(tenant_id, product_id, product_data, timeout=None):
        """Ürün cache'e kaydet."""
        cache_key = CacheService.get_cache_key(
            CacheService.CACHE_PREFIX_PRODUCT,
            tenant_id,
            product_id
        )
        cache.set(
            cache_key,
            product_data,
            timeout or CacheService.TIMEOUT_PRODUCT
        )
    
    @staticmethod
    def delete_product(tenant_id, product_id):
        """Ürün cache'den sil."""
        cache_key = CacheService.get_cache_key(
            CacheService.CACHE_PREFIX_PRODUCT,
            tenant_id,
            product_id
        )
        cache.delete(cache_key)
    
    @staticmethod
    def get_category_tree(tenant_id):
        """Kategori ağacı cache'den al."""
        cache_key = CacheService.get_cache_key(
            CacheService.CACHE_PREFIX_CATEGORY,
            tenant_id,
            'tree'
        )
        return cache.get(cache_key)
    
    @staticmethod
    def set_category_tree(tenant_id, category_data, timeout=None):
        """Kategori ağacı cache'e kaydet."""
        cache_key = CacheService.get_cache_key(
            CacheService.CACHE_PREFIX_CATEGORY,
            tenant_id,
            'tree'
        )
        cache.set(
            cache_key,
            category_data,
            timeout or CacheService.TIMEOUT_CATEGORY
        )
    
    @staticmethod
    def delete_category_tree(tenant_id):
        """Kategori ağacı cache'den sil."""
        cache_key = CacheService.get_cache_key(
            CacheService.CACHE_PREFIX_CATEGORY,
            tenant_id,
            'tree'
        )
        cache.delete(cache_key)
    
    @staticmethod
    def get_cart(tenant_id, cart_id):
        """Sepet cache'den al."""
        cache_key = CacheService.get_cache_key(
            CacheService.CACHE_PREFIX_CART,
            tenant_id,
            cart_id
        )
        return cache.get(cache_key)
    
    @staticmethod
    def set_cart(tenant_id, cart_id, cart_data, timeout=None):
        """Sepet cache'e kaydet."""
        cache_key = CacheService.get_cache_key(
            CacheService.CACHE_PREFIX_CART,
            tenant_id,
            cart_id
        )
        cache.set(
            cache_key,
            cart_data,
            timeout or CacheService.TIMEOUT_CART
        )
    
    @staticmethod
    def delete_cart(tenant_id, cart_id):
        """Sepet cache'den sil."""
        cache_key = CacheService.get_cache_key(
            CacheService.CACHE_PREFIX_CART,
            tenant_id,
            cart_id
        )
        cache.delete(cache_key)
    
    @staticmethod
    def invalidate_tenant_cache(tenant_id, prefix=None):
        """Tenant'a ait tüm cache'i temizle."""
        if prefix:
            # Belirli prefix için pattern
            pattern = f"{prefix}:{tenant_id}:*"
        else:
            # Tüm prefix'ler için
            pattern = f"*:{tenant_id}:*"
        
        # Django cache backend'e göre farklı yöntemler gerekebilir
        # Redis için keys() kullanılabilir ama production'da SCAN kullanılmalı
        try:
            # Redis backend kullanılıyorsa
            if hasattr(cache, 'delete_pattern'):
                cache.delete_pattern(pattern)
            else:
                # Fallback: Manuel temizleme
                logger.warning(f"Cache pattern deletion not supported. Pattern: {pattern}")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")

