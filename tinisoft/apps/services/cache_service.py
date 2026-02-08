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
    CACHE_PREFIX_TENANT = 'tenant'
    CACHE_PREFIX_USER_PERMS = 'user_perms'
    
    # Cache timeout'ları (saniye)
    TIMEOUT_PRODUCT = 3600  # 1 saat
    TIMEOUT_CATEGORY = 7200  # 2 saat
    TIMEOUT_CART = 1800  # 30 dakika
    TIMEOUT_ORDER = 3600  # 1 saat
    TIMEOUT_CUSTOMER = 1800  # 30 dakika
    TIMEOUT_ANALYTICS = 300  # 5 dakika
    TIMEOUT_TENANT = 86400  # 24 saat (Tenant bilgileri nadir değişir)
    TIMEOUT_USER_PERMS = 3600  # 1 saat
    
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
    def get_tenant_by_host(host):
        """Host (domain/subdomain) bilgisine göre tenant'ı cache'den al."""
        cache_key = f"{CacheService.CACHE_PREFIX_TENANT}:host:{host}"
        return cache.get(cache_key)

    @staticmethod
    def set_tenant_by_host(host, tenant_data, timeout=None):
        """Host bilgisine göre tenant'ı cache'e kaydet."""
        cache_key = f"{CacheService.CACHE_PREFIX_TENANT}:host:{host}"
        cache.set(cache_key, tenant_data, timeout or CacheService.TIMEOUT_TENANT)

    @staticmethod
    def get_user_permissions(user_id):
        """Kullanıcı yetkilerini cache'den al."""
        cache_key = f"{CacheService.CACHE_PREFIX_USER_PERMS}:{user_id}"
        return cache.get(cache_key)

    @staticmethod
    def set_user_permissions(user_id, perms_data, timeout=None):
        """Kullanıcı yetkilerini cache'e kaydet."""
        cache_key = f"{CacheService.CACHE_PREFIX_USER_PERMS}:{user_id}"
        cache.set(cache_key, perms_data, timeout or CacheService.TIMEOUT_USER_PERMS)

    @staticmethod
    def delete_user_permissions(user_id):
        """Kullanıcı yetkilerini cache'den sil."""
        cache_key = f"{CacheService.CACHE_PREFIX_USER_PERMS}:{user_id}"
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

