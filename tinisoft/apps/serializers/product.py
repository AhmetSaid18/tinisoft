"""
Product serializers.
"""
from rest_framework import serializers
from decimal import Decimal
from apps.models import (
    Product, Category, Brand, ProductImage, ProductOption,
    ProductOptionValue, ProductVariant
)
from apps.services.currency_service import CurrencyService
from django.utils.html import strip_tags
import base64
import uuid
import logging
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


def upload_base64_image(product, image_url):
    """
    Base64 formatındaki görseli storage'a yükler ve URL döndürür.
    """
    if not image_url or not image_url.startswith('data:image'):
        return image_url
        
    try:
        # Base64 format: data:image/[format];base64,[data]
        if ';base64,' in image_url:
            format_part, imgstr = image_url.split(';base64,')
            ext = format_part.split('/')[-1]
        else:
            return image_url
            
        if ext == 'svg+xml':
            ext = 'svg'
        
        # uzantı temizliği
        if ext == 'jpeg':
            ext = 'jpg'
            
        data = base64.b64decode(imgstr)
        
        # Benzersiz dosya adı oluştur
        filename = f"{uuid.uuid4()}.{ext}"
        
        # Tenant bazlı klasör yapısı: {tenant_id}/products/{product_id}/{filename}
        # product.tenant might be a lazy relation, ensures ID is accesssed safely
        if hasattr(product, 'tenant_id'):
            tenant_id = str(product.tenant_id)
        else:
            tenant_id = str(product.tenant.id)
            
        file_path = f'{tenant_id}/products/{product.id}/{filename}'
        
        # Storage'a kaydet
        saved_path = default_storage.save(file_path, ContentFile(data))
        file_url = default_storage.url(saved_path)
        
        return file_url
    except Exception as e:
        logger.error(f"Base64 upload error: {e}")
        return image_url


class BrandSerializer(serializers.ModelSerializer):
    """Brand serializer."""
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'slug', 'logo_url', 'description',
            'is_active', 'product_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_product_count(self, obj):
        """Markadaki ürün sayısı."""
        return obj.products.filter(is_deleted=False).count()

class CategorySerializer(serializers.ModelSerializer):
    """Category serializer."""
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent',
            'is_active', 'children', 'product_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_children(self, obj):
        """Alt kategorileri döndür."""
        children = obj.children.filter(is_deleted=False, is_active=True)
        return CategorySerializer(children, many=True).data
    
    def get_product_count(self, obj):
        """Kategorideki ürün sayısı."""
        return obj.products.filter(is_deleted=False, status='active').count()

    def validate(self, attrs):
        """Döngüsel kategori kontrolü."""
        parent = attrs.get('parent')
        instance = self.instance

        # Eğer yeni oluşturuluyorsa instance None'dır, o yüzden döngü olamaz (henüz çocukları yok)
        # Sadece güncelleme yaparken kontrol etmemiz lazım
        if instance and parent:
            # 1. Kendisini parent olarak seçemez
            if parent.id == instance.id:
                raise serializers.ValidationError({"parent": "Kategori kendisinin üst kategorisi olamaz."})

            # 2. Döngü kontrolü (Seçilen parent'ın ataları arasında kendisi var mı?)
            # Parent yolunda yukarı çık, eğer instance'a rastlarsak döngü var demektir.
            current = parent
            # Sonsuz döngüden kaçınmak için visited seti (zaten veride hata varsa diye)
            visited = set()
            
            while current:
                if current.id == instance.id:
                    raise serializers.ValidationError({"parent": "Döngüsel kategori ilişkisi algılandı. Bir kategoriyi kendi alt kategorisinin altına taşıyamazsınız."})
                
                if current.id in visited:
                    # Veritabanında zaten döngü varmış, burada keselim
                    break
                visited.add(current.id)
                
                current = current.parent
        
        return attrs


class ProductImageSerializer(serializers.ModelSerializer):
    """Product image serializer."""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = [
            'id', 'image_url', 'alt_text', 'position', 'is_primary',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_image_url(self, obj):
        """
        Görsel URL'ini döndür. Eğer veritabanında base64 varsa,
        otomatik olarak storage'a yükle ve güncelle (Lazy Migration).
        """
        url = obj.image_url
        if url and url.startswith('data:image'):
            new_url = upload_base64_image(obj.product, url)
            if new_url != url:
                # DB'yi güncelle
                obj.image_url = new_url
                obj.save(update_fields=['image_url'])
                return new_url
        return url


class ProductOptionValueSerializer(serializers.ModelSerializer):
    """Product option value serializer."""
    
    class Meta:
        model = ProductOptionValue
        fields = ['id', 'value', 'position', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductOptionSerializer(serializers.ModelSerializer):
    """Product option serializer."""
    values = ProductOptionValueSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductOption
        fields = ['id', 'name', 'position', 'values', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductVariantSerializer(serializers.ModelSerializer):
    """Product variant serializer."""
    option_values = ProductOptionValueSerializer(many=True, read_only=True)
    display_price = serializers.SerializerMethodField()
    display_compare_at_price = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'price', 'compare_at_price',
            'display_price', 'display_compare_at_price',
            'track_inventory', 'inventory_quantity',
            'allow_backorder', 'virtual_stock_quantity',
            'sku', 'barcode', 'option_values', 'is_default',
            'image_url', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'display_price', 'display_compare_at_price']
    
    def get_display_price(self, obj):
        """Kullanıcının seçtiği para birimine göre fiyat göster."""
        request = self.context.get('request')
        if not request:
            return str(obj.price)
        
        # Request'ten para birimi al (header'dan veya query param'dan)
        target_currency = request.headers.get('X-Currency-Code') or request.query_params.get('currency', 'TRY')
        target_currency = target_currency.upper()
        
        # Ürünün para birimini al (parent product'tan)
        product = obj.product
        from_currency = product.currency or 'TRY'
        
        # Aynı para birimiyse direkt döndür
        if from_currency == target_currency:
            return str(obj.price)
        
        # Para birimi dönüşümü yap
        try:
            converted_price = CurrencyService.convert_amount(
                obj.price,
                from_currency,
                target_currency
            )
            return str(converted_price)
        except Exception as e:
            # Hata durumunda orijinal fiyatı döndür
            return str(obj.price)
    
    def get_display_compare_at_price(self, obj):
        """Kullanıcının seçtiği para birimine göre karşılaştırma fiyatı göster."""
        if not obj.compare_at_price:
            return None
        
        request = self.context.get('request')
        if not request:
            return str(obj.compare_at_price)
        
        target_currency = request.headers.get('X-Currency-Code') or request.query_params.get('currency', 'TRY')
        target_currency = target_currency.upper()
        
        product = obj.product
        from_currency = product.currency or 'TRY'
        
        if from_currency == target_currency:
            return str(obj.compare_at_price)
        
        try:
            converted_price = CurrencyService.convert_amount(
                obj.compare_at_price,
                from_currency,
                target_currency
            )
            return str(converted_price)
        except Exception:
            return str(obj.compare_at_price)


class ProductListSerializer(serializers.ModelSerializer):
    """Product list serializer (lightweight)."""
    primary_image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    category_names = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    max_price = serializers.SerializerMethodField()
    display_price = serializers.SerializerMethodField()
    display_compare_at_price = serializers.SerializerMethodField()
    display_min_price = serializers.SerializerMethodField()
    display_max_price = serializers.SerializerMethodField()
    brand_name = serializers.SerializerMethodField()
    has_variants = serializers.BooleanField(source='is_variant_product', read_only=True)
    # Frontend uyumluluğu için camelCase field'lar
    inventoryQuantity = serializers.IntegerField(source='inventory_quantity', read_only=True)
    compareAtPrice = serializers.DecimalField(source='compare_at_price', max_digits=10, decimal_places=2, read_only=True, allow_null=True)
    isActive = serializers.BooleanField(source='is_visible', read_only=True)
    # Stok durumu (frontend için)
    available_quantity = serializers.SerializerMethodField()
    is_in_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'compare_at_price', 'compareAtPrice',
            'currency', 'price_with_vat',
            'display_price', 'display_compare_at_price',
            'display_min_price', 'display_max_price',
            'sku', 'inventory_quantity', 'inventoryQuantity', 'track_inventory',
            'allow_backorder', 'virtual_stock_quantity',
            'primary_image', 'images', 'category_names', 'min_price', 'max_price',
            'has_variants', 'is_featured', 'is_new', 'is_bestseller',
            'status', 'is_visible', 'isActive', 'view_count', 'sale_count',
            'brand', 'brand_name', 'brand_item', 'available_quantity', 'is_in_stock', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'price_with_vat', 'display_price', 'display_compare_at_price', 'display_min_price', 'display_max_price']
    
    def get_primary_image(self, obj):
        """Ana görseli döndür."""
        image = obj.images.filter(is_primary=True, is_deleted=False).first()
        if not image:
            image = obj.images.filter(is_deleted=False).first()
        
        if image:
            # Lazy migration check
            if image.image_url and image.image_url.startswith('data:image'):
                new_url = upload_base64_image(obj, image.image_url)
                if new_url != image.image_url:
                    image.image_url = new_url
                    image.save(update_fields=['image_url'])
                return new_url
            return image.image_url
            
        return None
    
    def get_images(self, obj):
        """Tüm görselleri döndür (sıralı)."""
        images = obj.images.filter(is_deleted=False).order_by('position', 'created_at')
        return ProductImageSerializer(images, many=True).data
    
    def get_category_names(self, obj):
        """Kategori isimlerini döndür."""
        return [cat.name for cat in obj.categories.filter(is_deleted=False, is_active=True)]
    
    def get_min_price(self, obj):
        """Minimum fiyat (varyant varsa varyantların min fiyatı)."""
        if obj.is_variant_product:
            variants = obj.variants.filter(is_deleted=False)
            if variants.exists():
                return min(v.price for v in variants)
        return obj.price
    
    def get_max_price(self, obj):
        """Maximum fiyat (varyant varsa varyantların max fiyatı)."""
        if obj.is_variant_product:
            variants = obj.variants.filter(is_deleted=False)
            if variants.exists():
                return max(v.price for v in variants)
        return obj.price
    
    def get_display_price(self, obj):
        """Kullanıcının seçtiği para birimine göre fiyat göster."""
        request = self.context.get('request')
        if not request:
            return str(obj.price)
        
        target_currency = request.headers.get('X-Currency-Code') or request.query_params.get('currency', 'TRY')
        target_currency = target_currency.upper()
        
        from_currency = obj.currency or 'TRY'
        
        if from_currency == target_currency:
            return str(obj.price)
        
        try:
            converted_price = CurrencyService.convert_amount(
                obj.price,
                from_currency,
                target_currency
            )
            return str(converted_price)
        except Exception:
            return str(obj.price)
    
    def get_display_compare_at_price(self, obj):
        """Kullanıcının seçtiği para birimine göre karşılaştırma fiyatı göster."""
        if not obj.compare_at_price:
            return None
        
        request = self.context.get('request')
        if not request:
            return str(obj.compare_at_price)
        
        target_currency = request.headers.get('X-Currency-Code') or request.query_params.get('currency', 'TRY')
        target_currency = target_currency.upper()
        
        from_currency = obj.currency or 'TRY'
        
        if from_currency == target_currency:
            return str(obj.compare_at_price)
        
        try:
            converted_price = CurrencyService.convert_amount(
                obj.compare_at_price,
                from_currency,
                target_currency
            )
            return str(converted_price)
        except Exception:
            return str(obj.compare_at_price)
    
    def get_display_min_price(self, obj):
        """Kullanıcının seçtiği para birimine göre minimum fiyat göster."""
        min_price = self.get_min_price(obj)
        if min_price is None:
            return None
        
        request = self.context.get('request')
        if not request:
            return str(min_price)
        
        target_currency = request.headers.get('X-Currency-Code') or request.query_params.get('currency', 'TRY')
        target_currency = target_currency.upper()
        
        from_currency = obj.currency or 'TRY'
        
        if from_currency == target_currency:
            return str(min_price)
        
        try:
            converted_price = CurrencyService.convert_amount(
                Decimal(str(min_price)),
                from_currency,
                target_currency
            )
            return str(converted_price)
        except Exception:
            return str(min_price)
    
    def get_display_max_price(self, obj):
        """Kullanıcının seçtiği para birimine göre maximum fiyat göster."""
        max_price = self.get_max_price(obj)
        if max_price is None:
            return None
        
        request = self.context.get('request')
        if not request:
            return str(max_price)
        
        target_currency = request.headers.get('X-Currency-Code') or request.query_params.get('currency', 'TRY')
        target_currency = target_currency.upper()
        
        from_currency = obj.currency or 'TRY'
        
        if from_currency == target_currency:
            return str(max_price)
        
        try:
            converted_price = CurrencyService.convert_amount(
                Decimal(str(max_price)),
                from_currency,
                target_currency
            )
            return str(converted_price)
        except Exception:
            return str(max_price)
        
    def get_brand_name(self, obj):
        """Marka bilgisini brand_item veya legacy brand alanından al."""
        if obj.brand_item:
            return obj.brand_item.name
        return obj.brand
        
    def get_available_quantity(self, obj):
        """Toplam mevcut stok miktarını döndür (gerçek + sanal)."""
        if not obj.track_inventory:
            return None  # Stok takibi yoksa None döndür (sınırsız)
        
        real_stock = obj.inventory_quantity
        
        # 1. Sanal stok var mı? (Açıkça girilmiş pozitif bir değer)
        # allow_backorder'a bakmaksızın, eğer sanal stok girildiyse ekle
        if obj.virtual_stock_quantity is not None and obj.virtual_stock_quantity > 0:
            return real_stock + obj.virtual_stock_quantity
            
        # 2. Allow backorder var mı? (Sanal stok girilmemiş veya 0 ama backorder açık -> Sınırsız)
        if obj.allow_backorder:
            return None  # None = sınırsız
            
        # 3. Sadece gerçek stok
        return real_stock
    
    def get_is_in_stock(self, obj):
        """Ürün stokta var mı? (frontend için boolean)."""
        if not obj.track_inventory:
            return True  # Stok takibi yoksa her zaman mevcut
        
        # Gerçek stok varsa True
        if obj.inventory_quantity > 0:
            return True
        
        # Sanal stok var mı? (>0)
        # allow_backorder'a bakmaksızın, eğer sanal stok varsa True
        if obj.virtual_stock_quantity is not None and obj.virtual_stock_quantity > 0:
            return True
        
        # Backorder açık mı? (Sınırsız satış izni)
        if obj.allow_backorder:
            return True
        
        # Hiç stok yok
        return False


class ProductDetailSerializer(serializers.ModelSerializer):
    """Product detail serializer (full)."""
    images = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_null=True,
        allow_empty=True,
        write_only=True,
        help_text="Ürün görselleri (array of objects: image_url, alt_text, position, is_primary)"
    )
    options = ProductOptionSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    display_price = serializers.SerializerMethodField()
    display_compare_at_price = serializers.SerializerMethodField()
    # Stok durumu (frontend için)
    available_quantity = serializers.SerializerMethodField()
    is_in_stock = serializers.SerializerMethodField()
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        write_only=True,
        required=False,
    )
    brand_name = serializers.SerializerMethodField() # Yeni marka alanı
    
    # Frontend uyumluluğu için: field mapping
    isActive = serializers.BooleanField(write_only=True, required=False)
    inventoryQuantity = serializers.IntegerField(source='inventory_quantity', write_only=True, required=False)
    compareAtPrice = serializers.DecimalField(source='compare_at_price', max_digits=10, decimal_places=2, write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'description_html',
            'price', 'compare_at_price', 'compareAtPrice',
            'currency', 'price_with_vat',
            'display_price', 'display_compare_at_price',
            'sku', 'barcode',
            'track_inventory', 'inventory_quantity', 'inventoryQuantity',
            'allow_backorder', 'virtual_stock_quantity',
            'is_variant_product',
            'status', 'is_visible', 'isActive',
            'meta_title', 'meta_description', 'meta_keywords',
            'tags', 'collections',
            'weight', 'length', 'width', 'height',
            'is_featured', 'is_new', 'is_bestseller',
            'sort_order',
            'available_from', 'available_until',
            'view_count', 'sale_count',
            'images', 'options', 'variants', 'categories',
            'category_ids',
            'brand', 'brand_name', 'brand_item', 'metadata',
            'available_quantity', 'is_in_stock',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'view_count', 'sale_count', 'price_with_vat', 'display_price', 'display_compare_at_price']
    
    def to_representation(self, instance):
        """Representation'ı override et - images'ı doğru sırala."""
        data = super().to_representation(instance)
        # Images'ı silinmemiş ve sıralı olarak göster
        images = instance.images.filter(is_deleted=False).order_by('position', 'created_at')
        data['images'] = ProductImageSerializer(images, many=True).data
        return data

    def _handle_image_url(self, product, image_url):
        """
        Görsel URL'ini işle.
        Eğer base64 ise storage'a yükle ve URL döndür.
        """
        return upload_base64_image(product, image_url)
    
    def validate(self, attrs):
        """Frontend'den gelen field'ları backend field'larına map et."""
        # isActive -> status mapping
        is_active = attrs.pop('isActive', None)
        if is_active is not None:
            # isActive=True ise status='active', False ise 'draft'
            if is_active:
                attrs['status'] = 'active'
                attrs['is_visible'] = True
            else:
                attrs['status'] = 'draft'
                attrs['is_visible'] = False
        
        # Eğer status gönderilmemişse ve isActive de yoksa, default 'active' yap
        if 'status' not in attrs:
            attrs['status'] = 'active'
            attrs['is_visible'] = True
        
        # inventoryQuantity -> inventory_quantity mapping (zaten source ile yapılıyor ama emin olalım)
        if 'inventory_quantity' not in attrs and 'inventoryQuantity' in attrs:
            attrs['inventory_quantity'] = attrs.pop('inventoryQuantity')
        
        # compareAtPrice -> compare_at_price mapping
        if 'compare_at_price' not in attrs and 'compareAtPrice' in attrs:
            attrs['compare_at_price'] = attrs.pop('compareAtPrice')

        # Brand senkronizasyonu
        if 'brand' in attrs:
            brand_name = attrs.get('brand')
            
            if brand_name and brand_name.strip():
                from django.utils.text import slugify
                # Request context'inden veya instance'tan tenant'ı al
                request = self.context.get('request')
                tenant = None
                
                if request and hasattr(request, 'tenant'):
                    tenant = request.tenant
                elif self.instance:
                    tenant = self.instance.tenant
                
                if tenant:
                    brand_obj, _ = Brand.objects.get_or_create(
                        tenant=tenant,
                        name=brand_name.strip(),
                        defaults={'slug': slugify(brand_name.strip())}
                    )
                    attrs['brand_item'] = brand_obj
                    attrs['brand'] = brand_name.strip()
            else:
                # Marka ismi silindiyse veya boşsa, bağı kopar
                attrs['brand_item'] = None
                attrs['brand'] = ''
        
        # Images validation - image_url eksik olanları filtrele
        if 'images' in attrs:
            images_data = attrs['images']
            if images_data:
                # image_url olmayan item'ları filtrele
                attrs['images'] = [img for img in images_data if img.get('image_url')]

        # Açıklama Senkronizasyonu (HTML -> Plain Text)
        # Eğer description_html geldi ama description gelmediyse (veya boşsa),
        # HTML'den tagleri temizleyip description oluştur.
        desc_html = attrs.get('description_html')
        desc_plain = attrs.get('description')
        
        if desc_html and not desc_plain:
            attrs['description'] = strip_tags(desc_html)
            
        return attrs
    
    def create(self, validated_data):
        """Ürün oluştur."""
        category_ids = validated_data.pop('category_ids', [])
        images_data = validated_data.pop('images', None)
        
        product = Product.objects.create(**validated_data)
        
        # Kategorileri ekle
        if category_ids:
            product.categories.set(category_ids)
        
        # Görselleri ekle (eğer gönderilmişse)
        if images_data:
            for image_data in images_data:
                # image_url zorunlu, yoksa atla
                if not image_data.get('image_url'):
                    continue
                
                # Base64 ise yükle
                image_data['image_url'] = self._handle_image_url(product, image_data['image_url'])
                
                # is_primary değişiyorsa, diğer görsellerin is_primary'ini False yap
                if image_data.get('is_primary', False):
                    ProductImage.objects.filter(product=product, is_deleted=False).update(is_primary=False)
                
                ProductImage.objects.create(
                    product=product,
                    **image_data
                )
        
        return product
    
    def update(self, instance, validated_data):
        """Ürün güncelle."""
        category_ids = validated_data.pop('category_ids', None)
        images_data = validated_data.pop('images', None)
        
        # Ürün field'larını güncelle
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Kategorileri güncelle
        if category_ids is not None:
            instance.categories.set(category_ids)
        
        # Görselleri güncelle (eğer gönderilmişse)
        if images_data is not None:
            # 1. Silinenleri işle: Gelen listede OLMAYAN mevcut görselleri sil
            incoming_ids = [item.get('id') for item in images_data if item.get('id')]
            instance.images.filter(is_deleted=False).exclude(id__in=incoming_ids).update(is_deleted=True)

            # 2. Mevcut görselleri güncelle veya yeni ekle
            for image_data in images_data:
                image_id = image_data.get('id')
                if image_id:
                    # Mevcut görseli güncelle
                    try:
                        product_image = instance.images.get(id=image_id, is_deleted=False)
                        # is_primary değişiyorsa, diğer görsellerin is_primary'ini False yap
                        if image_data.get('is_primary', False):
                            instance.images.filter(is_deleted=False).exclude(id=image_id).update(is_primary=False)
                        # Görseli güncelle
                        for key, value in image_data.items():
                            if key != 'id' and hasattr(product_image, key):
                                if key == 'image_url':
                                    value = self._handle_image_url(instance, value)
                                setattr(product_image, key, value)
                        product_image.save()
                    except ProductImage.DoesNotExist:
                        pass  # Görsel bulunamadı, atla
                else:
                    # Yeni görsel ekle
                    # image_url zorunlu, yoksa atla
                    if not image_data.get('image_url'):
                        continue
                    
                    # Base64 ise yükle
                    image_data['image_url'] = self._handle_image_url(instance, image_data['image_url'])
                    
                    # is_primary değişiyorsa, diğer görsellerin is_primary'ini False yap
                    if image_data.get('is_primary', False):
                        instance.images.filter(is_deleted=False).update(is_primary=False)
                    
                    ProductImage.objects.create(
                        product=instance,
                        **image_data
                    )
        
        return instance
    
    def get_display_price(self, obj):
        """Kullanıcının seçtiği para birimine göre fiyat göster."""
        request = self.context.get('request')
        if not request:
            return str(obj.price)
        
        target_currency = request.headers.get('X-Currency-Code') or request.query_params.get('currency', 'TRY')
        target_currency = target_currency.upper()
        
        from_currency = obj.currency or 'TRY'
        
        if from_currency == target_currency:
            return str(obj.price)
        
        try:
            converted_price = CurrencyService.convert_amount(
                obj.price,
                from_currency,
                target_currency
            )
            return str(converted_price)
        except Exception:
            return str(obj.price)
    
    def get_display_compare_at_price(self, obj):
        """Kullanıcının seçtiği para birimine göre karşılaştırma fiyatı göster."""
        if not obj.compare_at_price:
            return None
        
        request = self.context.get('request')
        if not request:
            return str(obj.compare_at_price)
        
        target_currency = request.headers.get('X-Currency-Code') or request.query_params.get('currency', 'TRY')
        target_currency = target_currency.upper()
        
        from_currency = obj.currency or 'TRY'
        
        if from_currency == target_currency:
            return str(obj.compare_at_price)
        
        try:
            converted_price = CurrencyService.convert_amount(
                obj.compare_at_price,
                from_currency,
                target_currency
            )
            return str(converted_price)
        except Exception:
            return str(obj.compare_at_price)
    def get_available_quantity(self, obj):
        """Toplam mevcut stok miktarını döndür (gerçek + sanal)."""
        if not obj.track_inventory:
            return None
        
        real_stock = obj.inventory_quantity
        
        if obj.virtual_stock_quantity is not None and obj.virtual_stock_quantity > 0:
            return real_stock + obj.virtual_stock_quantity
            
        if obj.allow_backorder:
            return None
            
        return real_stock
    
    def get_is_in_stock(self, obj):
        """Ürün stokta var mı? (frontend için boolean)."""
        if not obj.track_inventory:
            return True
        
        if obj.inventory_quantity > 0:
            return True
        
        if obj.virtual_stock_quantity is not None and obj.virtual_stock_quantity > 0:
            return True
        
        if obj.allow_backorder:
            return True
        
        return False

    def get_brand_name(self, obj):
        """Marka bilgisini brand_item veya legacy brand alanından al."""
        if obj.brand_item:
            return obj.brand_item.name
        return obj.brand or None

