"""
Search service - Ürün arama ve filtreleme optimizasyonu.
İkas benzeri arama sistemi.
"""
from django.db.models import Q, Count, Avg, Max, Min
from django.db.models.functions import Coalesce
from apps.models import Product, Category, ProductAttribute, ProductAttributeValue, ProductAttributeMapping
import logging

logger = logging.getLogger(__name__)


class SearchService:
    """Search business logic."""
    
    @staticmethod
    def search_products(tenant, query, filters=None, ordering=None, limit=None):
        """
        Ürün arama ve filtreleme.
        
        Args:
            tenant: Tenant instance
            query: Arama sorgusu
            filters: Filtreler dict (category, price_range, attributes, vb.)
            ordering: Sıralama (price_asc, price_desc, newest, popularity)
            limit: Sonuç limiti
        
        Returns:
            QuerySet: Filtrelenmiş ürünler
        """
        queryset = Product.objects.filter(
            tenant=tenant,
            is_deleted=False,
            status='active',
            is_visible=True,
        )
        
        # Metin araması
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(sku__icontains=query) |
                Q(tags__icontains=query) |
                Q(meta_keywords__icontains=query)
            ).distinct()
        
        # Filtreler
        if filters:
            # Kategori filtresi
            if 'category_id' in filters:
                queryset = queryset.filter(categories__id=filters['category_id'])
            
            if 'category_slug' in filters:
                queryset = queryset.filter(categories__slug=filters['category_slug'])
            
            # Fiyat aralığı
            if 'min_price' in filters:
                queryset = queryset.filter(price__gte=filters['min_price'])
            
            if 'max_price' in filters:
                queryset = queryset.filter(price__lte=filters['max_price'])
            
            # Stok durumu
            if 'in_stock' in filters and filters['in_stock']:
                queryset = queryset.filter(
                    Q(inventory_quantity__gt=0) |
                    Q(is_variant_product=True, variants__inventory_quantity__gt=0)
                ).distinct()
            
            # Özellikler (attributes)
            if 'attributes' in filters:
                for attr_slug, value_slugs in filters['attributes'].items():
                    if isinstance(value_slugs, str):
                        value_slugs = [value_slugs]
                    
                    # Attribute ve value'ları bul
                    try:
                        attribute = ProductAttribute.objects.get(
                            tenant=tenant,
                            slug=attr_slug,
                            is_filterable=True
                        )
                        values = ProductAttributeValue.objects.filter(
                            attribute=attribute,
                            slug__in=value_slugs
                        )
                        
                        # Bu attribute-value'lara sahip ürünleri filtrele
                        product_ids = ProductAttributeMapping.objects.filter(
                            attribute=attribute,
                            value__in=values
                        ).values_list('product_id', flat=True)
                        
                        queryset = queryset.filter(id__in=product_ids)
                    except ProductAttribute.DoesNotExist:
                        pass
            
            # Etiketler
            if 'tags' in filters:
                tags = filters['tags']
                if isinstance(tags, str):
                    tags = [tags]
                for tag in tags:
                    queryset = queryset.filter(tags__contains=[tag])
            
            # Koleksiyonlar
            if 'collections' in filters:
                collections = filters['collections']
                if isinstance(collections, str):
                    collections = [collections]
                for collection in collections:
                    queryset = queryset.filter(collections__contains=[collection])
            
            # Özellikler (featured, new, bestseller)
            if 'is_featured' in filters:
                queryset = queryset.filter(is_featured=filters['is_featured'])
            
            if 'is_new' in filters:
                queryset = queryset.filter(is_new=filters['is_new'])
            
            if 'is_bestseller' in filters:
                queryset = queryset.filter(is_bestseller=filters['is_bestseller'])
            
            # Marka filtresi
            if 'brand' in filters:
                brand = filters['brand']
                # Eğer liste ise birden fazla marka, string ise tek marka
                if isinstance(brand, list):
                    queryset = queryset.filter(metadata__brand__in=brand)
                elif isinstance(brand, str):
                    # Virgülle ayrılmış birden fazla marka destekle
                    brands = [b.strip() for b in brand.split(',') if b.strip()]
                    if brands:
                        if len(brands) == 1:
                            queryset = queryset.filter(metadata__brand=brands[0])
                        else:
                            queryset = queryset.filter(metadata__brand__in=brands)
        
        # Sıralama
        if ordering:
            if ordering == 'price_asc':
                queryset = queryset.order_by('price')
            elif ordering == 'price_desc':
                queryset = queryset.order_by('-price')
            elif ordering == 'newest':
                queryset = queryset.order_by('-created_at')
            elif ordering == 'popularity':
                queryset = queryset.order_by('-view_count', '-sale_count')
            elif ordering == 'name_asc':
                queryset = queryset.order_by('name')
            elif ordering == 'name_desc':
                queryset = queryset.order_by('-name')
        else:
            queryset = queryset.order_by('-created_at')
        
        # Limit
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    @staticmethod
    def get_search_suggestions(tenant, query, limit=5):
        """
        Arama önerileri.
        
        Args:
            tenant: Tenant instance
            query: Arama sorgusu
            limit: Öneri limiti
        
        Returns:
            list: Öneri listesi
        """
        suggestions = []
        
        # Ürün önerileri
        products = Product.objects.filter(
            tenant=tenant,
            is_deleted=False,
            status='active',
            is_visible=True,
            name__icontains=query
        )[:limit]
        
        for product in products:
            suggestions.append({
                'type': 'product',
                'text': product.name,
                'url': f'/products/{product.slug}',
            })
        
        # Kategori önerileri
        categories = Category.objects.filter(
            tenant=tenant,
            is_deleted=False,
            is_active=True,
            name__icontains=query
        )[:limit]
        
        for category in categories:
            suggestions.append({
                'type': 'category',
                'text': category.name,
                'url': f'/categories/{category.slug}',
            })
        
        return suggestions[:limit]
    
    @staticmethod
    def get_filter_options(tenant, category_id=None):
        """
        Filtreleme seçeneklerini getir.
        
        Args:
            tenant: Tenant instance
            category_id: Kategori ID (opsiyonel)
        
        Returns:
            dict: Filtre seçenekleri
        """
        # Ürünleri al
        products = Product.objects.filter(
            tenant=tenant,
            is_deleted=False,
            status='active',
            is_visible=True,
        )
        
        if category_id:
            products = products.filter(categories__id=category_id)
        
        # Fiyat aralığı
        price_stats = products.aggregate(
            min_price=Min('price'),
            max_price=Max('price'),
        )
        
        # Filtrelenebilir özellikler
        filterable_attributes = ProductAttribute.objects.filter(
            tenant=tenant,
            is_filterable=True,
            is_deleted=False,
        )
        
        attribute_options = {}
        for attr in filterable_attributes:
            # Bu attribute'a sahip ürünlerin value'larını al
            mappings = ProductAttributeMapping.objects.filter(
                product__in=products,
                attribute=attr,
            ).values_list('value_id', flat=True).distinct()
            
            values = ProductAttributeValue.objects.filter(
                id__in=mappings,
                attribute=attr,
            ).order_by('position', 'value')
            
            if values.exists():
                attribute_options[attr.slug] = {
                    'name': attr.name,
                    'values': [
                        {
                            'slug': v.slug,
                            'value': v.value,
                            'color_code': v.color_code,
                            'image_url': v.image_url,
                        }
                        for v in values
                    ],
                }
        
        return {
            'price_range': {
                'min': float(price_stats['min_price'] or 0),
                'max': float(price_stats['max_price'] or 0),
            },
            'attributes': attribute_options,
        }

