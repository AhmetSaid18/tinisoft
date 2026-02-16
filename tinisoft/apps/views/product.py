"""
Product views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from apps.models import Product, Category
from apps.serializers.product import (
    ProductListSerializer, ProductDetailSerializer,
    CategorySerializer
)
from apps.permissions import IsTenantOwnerOfObject, HasStaffPermission
from django.core.exceptions import ValidationError
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """
    Kullanıcının IP adresini al.
    Öncelik: Cloudflare > X-Real-IP > X-Forwarded-For > Remote-Addr
    """
    # 1. Cloudflare
    cf_connecting_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_connecting_ip:
        return cf_connecting_ip.strip()
    
    # 2. X-Real-IP (Nginx/Traefik vs)
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip.strip()

    # 3. X-Forwarded-For
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # "client_ip, proxy_ip" formatında olabilir, ilkini al
        return x_forwarded_for.split(',')[0].strip()

    # 4. Fallback (Docker internal IP dönebilir: 172.18.x.x)
    return request.META.get('REMOTE_ADDR')


class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasStaffPermission])
def product_list_create(request):
    """
    Ürün listesi (GET) veya yeni ürün oluştur (POST).
    
    GET: /api/products/
    POST: /api/products/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        logger.warning(f"[PRODUCTS] {request.method} /api/products/ | 400 | Tenant not found")
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        # Filtreleme
        queryset = Product.objects.filter(tenant=tenant, is_deleted=False)
        
        # Status filtresi
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Görünürlük filtresi
        is_visible = request.query_params.get('is_visible')
        if is_visible is not None:
            queryset = queryset.filter(is_visible=is_visible.lower() == 'true')
        
        # Kategori filtresi
        category_id = request.query_params.get('category_id')
        if category_id:
            try:
                queryset = queryset.filter(categories__id=category_id)
            except (ValidationError, ValueError):
                queryset = queryset.filter(categories__slug=category_id)
        
        # Marka filtresi
        brand = request.query_params.get('brand')
        if brand:
            # Virgülle ayrılmış birden fazla marka destekle
            brands = [b.strip() for b in brand.split(',') if b.strip()]
            if brands:
                if len(brands) == 1:
                    queryset = queryset.filter(metadata__brand=brands[0])
                else:
                    queryset = queryset.filter(metadata__brand__in=brands)
        
        # Arama
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(sku__icontains=search)
            )
        
        # Sıralama
        ordering = request.query_params.get('ordering', '-created_at')
        
        # Geçerli ordering field'ları
        valid_orderings = [
            'created_at', '-created_at',
            'updated_at', '-updated_at',
            'name', '-name',
            'price', '-price',
            'sort_order', '-sort_order',
            'view_count', '-view_count',
            'sale_count', '-sale_count',
            'is_featured', '-is_featured',
        ]
        
        # Ordering parametresini kontrol et
        if ordering not in valid_orderings:
            # Geçersiz ordering ise default kullan
            logger.warning(f"Invalid ordering parameter: {ordering}, using default: -created_at")
            ordering = '-created_at'
        
        queryset = queryset.order_by(ordering)
        
        # Optimization
        queryset = queryset.prefetch_related('images', 'categories', 'variants')
        
        # Pagination
        paginator = ProductPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            response = paginator.get_paginated_response(serializer.data)
            logger.info(f"[PRODUCTS] GET /api/products/ | 200 | Count: {len(page)}/{paginator.page.paginator.count}")
            return response
        
        serializer = ProductListSerializer(queryset, many=True, context={'request': request})
        logger.info(f"[PRODUCTS] GET /api/products/ | 200 | Count: {queryset.count()}")
        return Response({
            'success': True,
            'products': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = ProductDetailSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save(tenant=tenant)
            
            # Activity Log
            from apps.services.activity_log_service import ActivityLogService
            ActivityLogService.log(
                tenant=tenant,
                user=request.user,
                action="product_create",
                description=f"Yeni ürün oluşturuldu: {product.name} (SKU: {product.sku})",
                content_type="Product",
                object_id=product.id,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            logger.info(f"[PRODUCTS] POST /api/products/ | 201 | Created | SKU: {product.sku}")
            return Response({
                'success': True,
                'message': 'Ürün oluşturuldu.',
                'product': ProductDetailSerializer(product, context={'request': request}).data,
            }, status=status.HTTP_201_CREATED)
        logger.error(f"[PRODUCTS] POST /api/products/ | 400 | Validation failed | Errors: {list(serializer.errors.keys())}")
        return Response({
            'success': False,
            'message': 'Ürün oluşturulamadı.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, HasStaffPermission])
def product_detail(request, product_id):
    """
    Ürün detayı (GET), güncelle (PUT/PATCH) veya sil (DELETE).
    
    GET: /api/products/{product_id}/
    PUT/PATCH: /api/products/{product_id}/
    DELETE: /api/products/{product_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        queryset = Product.objects.filter(id=product_id, tenant=tenant, is_deleted=False)
        if request.method == 'GET':
            queryset = queryset.prefetch_related('images', 'categories', 'options', 'options__values', 'variants', 'variants__option_values')
        product = queryset.get()
    except Product.DoesNotExist:
        logger.warning(f"[PRODUCTS] {request.method} /api/products/{product_id}/ | 404 | Product not found")
        return Response({
            'success': False,
            'message': 'Ürün bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ProductDetailSerializer(product, context={'request': request})
        logger.info(
            f"[PRODUCTS] GET /api/products/{product_id}/ - SUCCESS | "
            f"Tenant: {tenant.name} ({tenant.id}) | "
            f"User: {request.user.email} | "
            f"ProductID: {product.id} | "
            f"ProductName: {product.name} | "
            f"Status: {status.HTTP_200_OK}"
        )
        return Response({
            'success': True,
            'product': serializer.data,
        })
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = ProductDetailSerializer(
            product,
            data=request.data,
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            
            # Activity Log - Daha detaylı ve doğru açıklama
            action = "product_update"
            description = f"Ürün güncellendi: {product.name} (SKU: {product.sku})"
            
            # Eğer SADECE sanal stok güncellendiyse özel action/description kullan
            updated_fields = list(request.data.keys())
            if len(updated_fields) == 1 and updated_fields[0] == 'virtual_stock_quantity':
                action = "virtual_stock_update"
                new_qty = request.data.get('virtual_stock_quantity')
                description = f"Ürün sanal stok güncellendi: {product.name} (Yeni: {new_qty})"
            
            # Activity Log
            from apps.services.activity_log_service import ActivityLogService
            ActivityLogService.log(
                tenant=tenant,
                user=request.user,
                action=action,
                description=description,
                content_type="Product",
                object_id=product.id,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            logger.info(
                f"[PRODUCTS] {request.method} /api/products/{product_id}/ - SUCCESS | "
                f"Tenant: {tenant.name} ({tenant.id}) | "
                f"User: {request.user.email} | "
                f"ProductID: {product.id} | "
                f"ProductName: {product.name} | "
                f"Status: {status.HTTP_200_OK}"
            )
            return Response({
                'success': True,
                'message': 'Ürün güncellendi.',
                'product': serializer.data,
            })
        logger.warning(
            f"[PRODUCTS] {request.method} /api/products/{product_id}/ - VALIDATION ERROR | "
            f"Tenant: {tenant.name} ({tenant.id}) | "
            f"User: {request.user.email} | "
            f"ProductID: {product.id} | "
            f"Errors: {serializer.errors} | "
            f"Status: {status.HTTP_400_BAD_REQUEST}"
        )
        return Response({
            'success': False,
            'message': 'Ürün güncellenemedi.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        product.soft_delete()
        
        # Activity Log
        from apps.services.activity_log_service import ActivityLogService
        ActivityLogService.log(
            tenant=tenant,
            user=request.user,
            action="product_delete",
            description=f"Ürün silindi: {product.name}",
            content_type="Product",
            object_id=product.id,
            ip_address=get_client_ip(request)
        )
        
        logger.info(
            f"[PRODUCTS] DELETE /api/products/{product_id}/ - SUCCESS | "
            f"Tenant: {tenant.name} ({tenant.id}) | "
            f"User: {request.user.email} | "
            f"ProductID: {product.id} | "
            f"ProductName: {product.name} | "
            f"Status: {status.HTTP_200_OK}"
        )
        return Response({
            'success': True,
            'message': 'Ürün silindi.',
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def product_list_public(request, tenant_slug=None):
    """
    Public ürün listesi (frontend için).
    
    GET: /api/public/products/ (tenant_slug query parameter ile)
    GET: /api/public/{tenant_slug}/products/ (path parameter ile)
    
    Tenant belirleme önceliği:
    1. Path parameter: tenant_slug
    2. Query parameter: ?tenant_slug=xxx
    3. Query parameter: ?tenant_id=xxx
    4. Header: X-Tenant-Slug
    5. Header: X-Tenant-ID
    6. Subdomain/Custom domain (otomatik)
    """
    try:
        tenant = None
        tenant_slug_param = request.query_params.get('tenant_slug', 'Not provided')
        tenant_id_param = request.query_params.get('tenant_id', 'Not provided')
        tenant_slug_header = request.headers.get('X-Tenant-Slug', 'Not provided')
        tenant_id_header = request.headers.get('X-Tenant-ID', 'Not provided')
        
        client_ip = get_client_ip(request)
        logger.info(
            f"[PRODUCTS] GET /api/public/products/ | "
            f"IP: {client_ip} | "
            f"Path tenant_slug: {tenant_slug} | "
            f"Query tenant_slug: {tenant_slug_param} | "
            f"Query tenant_id: {tenant_id_param} | "
            f"Header X-Tenant-Slug: {tenant_slug_header} | "
            f"Header X-Tenant-ID: {tenant_id_header}"
        )
        
        # 1. Path parameter'dan tenant_slug
        if tenant_slug:
            try:
                from apps.models import Tenant
                tenant = Tenant.objects.get(slug=tenant_slug, is_deleted=False)
            except Tenant.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Mağaza bulunamadı: {tenant_slug}',
                }, status=status.HTTP_404_NOT_FOUND)
        
        # 2. Query parameter'dan tenant_slug
        if not tenant:
            tenant_slug_param = request.query_params.get('tenant_slug')
            if tenant_slug_param:
                try:
                    from apps.models import Tenant
                    tenant = Tenant.objects.get(slug=tenant_slug_param, is_deleted=False)
                except Tenant.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': f'Mağaza bulunamadı: {tenant_slug_param}',
                    }, status=status.HTTP_404_NOT_FOUND)
        
        # 3. Query parameter'dan tenant_id
        if not tenant:
            tenant_id_param = request.query_params.get('tenant_id')
            if tenant_id_param:
                try:
                    from apps.models import Tenant
                    tenant = Tenant.objects.get(id=tenant_id_param, is_deleted=False)
                except Tenant.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': f'Mağaza bulunamadı: {tenant_id_param}',
                    }, status=status.HTTP_404_NOT_FOUND)
        
        # 4. Header'dan tenant_slug
        if not tenant:
            tenant_slug_header = request.headers.get('X-Tenant-Slug')
            if tenant_slug_header:
                try:
                    from apps.models import Tenant
                    tenant = Tenant.objects.get(slug=tenant_slug_header, is_deleted=False)
                except Tenant.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': f'Mağaza bulunamadı: {tenant_slug_header}',
                    }, status=status.HTTP_404_NOT_FOUND)
        
        # 5. Header'dan tenant_id
        if not tenant:
            tenant_id_header = request.headers.get('X-Tenant-ID')
            if tenant_id_header:
                try:
                    from apps.models import Tenant
                    tenant = Tenant.objects.get(id=tenant_id_header, is_deleted=False)
                except Tenant.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': f'Mağaza bulunamadı: {tenant_id_header}',
                    }, status=status.HTTP_404_NOT_FOUND)
        
        if not tenant:
            logger.warning(
                f"[PRODUCTS] GET /api/public/products/ | 400 | "
                f"Tenant not found | "
                f"IP: {get_client_ip(request)} | "
                f"Path tenant_slug: {tenant_slug}, "
                f"Query tenant_slug: {tenant_slug_param}, "
                f"Query tenant_id: {tenant_id_param}, "
                f"Header X-Tenant-Slug: {tenant_slug_header}, "
                f"Header X-Tenant-ID: {tenant_id_header}"
            )
            return Response({
                'success': False,
                'message': 'Tenant bulunamadı. Lütfen tenant_slug veya tenant_id parametresi gönderin.',
                'hint': 'Örnek: /api/public/products/?tenant_slug=magaza-adi veya Header: X-Tenant-Slug: magaza-adi',
                'error': 'Tenant bilgisi eksik. Lütfen tenant_slug veya tenant_id parametresi gönderin.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"[PRODUCTS] Tenant found: {tenant.name} ({tenant.slug})")
        
        queryset = Product.objects.filter(
            tenant=tenant,
            is_deleted=False,
            status='active',
            is_visible=True,
        )
        
        # Kategori filtresi (category_id veya category_slug ile)
        category_id = request.query_params.get('category_id')
        category_slug = request.query_params.get('category_slug') or request.query_params.get('category')
        
        if category_id or category_slug:
            # Kategoriyi bul
            category = None
            
            # category_id bir UUID mi kontrol et? Değilse slug olarak değerlendir.
            if category_id:
                try:
                    category = Category.objects.get(
                        id=category_id,
                        tenant=tenant,
                        is_deleted=False,
                        is_active=True
                    )
                except (Category.DoesNotExist, ValidationError, ValueError):
                    # Eğer category_id geçerli bir UUID değilse veya bulunamadıysa, 
                    # slug olarak denemek için category_slug'a ata (eğer category_slug boşsa)
                    if not category_slug:
                        category_slug = category_id
            
            if not category and category_slug:
                try:
                    # .first() kullan - aynı slug'a sahip birden fazla kategori olabilir
                    category = Category.objects.filter(
                        slug=category_slug,
                        tenant=tenant,
                        is_deleted=False,
                        is_active=True
                    ).first()
                except Exception:
                    # Herhangi bir hata durumunda None olsun
                    category = None
            
            if category:
                # Alt kategorileri de dahil et (recursive)
                def get_all_category_ids(cat):
                    """Kategori ve tüm alt kategorilerinin ID'lerini döndür"""
                    category_ids = [cat.id]
                    children = Category.objects.filter(
                        parent=cat,
                        tenant=tenant,
                        is_deleted=False,
                        is_active=True
                    )
                    for child in children:
                        category_ids.extend(get_all_category_ids(child))
                    return category_ids
                
                # Kategori ve tüm alt kategorilerinin ID'lerini al
                all_category_ids = get_all_category_ids(category)
                
                # Bu kategorilerdeki ürünleri filtrele
                queryset = queryset.filter(
                    categories__id__in=all_category_ids,
                    categories__is_active=True
                ).distinct()
        
        # Marka filtresi
        brand = request.query_params.get('brand')
        if brand:
            # Virgülle ayrılmış birden fazla marka destekle
            brands = [b.strip() for b in brand.split(',') if b.strip()]
            if brands:
                if len(brands) == 1:
                    queryset = queryset.filter(metadata__brand=brands[0])
                else:
                    queryset = queryset.filter(metadata__brand__in=brands)
        
        # Arama
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Sıralama
        ordering = request.query_params.get('ordering', '-created_at')
        
        # Geçerli ordering field'ları
        valid_orderings = [
            'created_at', '-created_at',
            'updated_at', '-updated_at',
            'name', '-name',
            'price', '-price',
            'sort_order', '-sort_order',
            'view_count', '-view_count',
            'sale_count', '-sale_count',
            'is_featured', '-is_featured',
        ]
        
        # Ordering parametresini kontrol et
        if ordering not in valid_orderings:
            # Geçersiz ordering ise default kullan
            logger.warning(f"Invalid ordering parameter: {ordering}, using default: -created_at")
            ordering = '-created_at'
        
        queryset = queryset.order_by(ordering)
        
        # Optimization
        queryset = queryset.prefetch_related('images', 'categories', 'variants')
        
        # Pagination
        paginator = ProductPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            response = paginator.get_paginated_response(serializer.data)
            logger.info(f"[PRODUCTS] GET /api/public/products/ | 200 | IP: {get_client_ip(request)} | Count: {len(page)}/{paginator.page.paginator.count} | Tenant: {tenant.slug}")
            return response
        
        serializer = ProductListSerializer(queryset, many=True, context={'request': request})
        logger.info(f"[PRODUCTS] GET /api/public/products/ | 200 | IP: {get_client_ip(request)} | Count: {queryset.count()} | Tenant: {tenant.slug}")
        return Response({
            'success': True,
            'products': serializer.data,
        })
    
    except Exception as e:
        logger.error(
            f"[PRODUCTS] GET /api/public/products/ | 500 | "
            f"Error: {str(e)} | "
            f"Error type: {type(e).__name__} | "
            f"IP: {get_client_ip(request)} | "
            f"Path tenant_slug: {tenant_slug}",
            exc_info=True
        )
        return Response({
            'success': False,
            'message': 'Ürün listesi alınırken bir hata oluştu.',
            'error': str(e),
            'error_type': type(e).__name__,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, HasStaffPermission])
def product_activate(request, product_id):
    """
    Ürünü aktif yap (status='active', is_visible=True).
    """
    # Yetki adı
    product_activate.staff_permission = 'products'
    # POST: /api/products/{product_id}/activate/
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        product = Product.objects.get(id=product_id, tenant=tenant, is_deleted=False)
    except Product.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Ürün bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    product.status = 'active'
    product.is_visible = True
    product.save()
    
    # Activity Log
    from apps.services.activity_log_service import ActivityLogService
    ActivityLogService.log(
        tenant=tenant,
        user=request.user,
        action="product_activate",
        description=f"Ürün aktif edildi: {product.name}",
        content_type="Product",
        object_id=product.id,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    logger.info(f"[PRODUCTS] POST /api/products/{product_id}/activate/ | 200 | Activated | SKU: {product.sku}")
    
    return Response({
        'success': True,
        'message': 'Ürün aktif edildi.',
        'product': ProductDetailSerializer(product, context={'request': request}).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, HasStaffPermission])
def product_deactivate(request, product_id):
    """
    Ürünü pasif yap (status='archived', is_visible=False).
    """
    # Yetki adı
    product_deactivate.staff_permission = 'products'
    # POST: /api/products/{product_id}/deactivate/
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        product = Product.objects.get(id=product_id, tenant=tenant, is_deleted=False)
    except Product.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Ürün bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    product.status = 'archived'
    product.is_visible = False
    product.save()
    
    # Activity Log
    from apps.services.activity_log_service import ActivityLogService
    ActivityLogService.log(
        tenant=tenant,
        user=request.user,
        action="product_deactivate",
        description=f"Ürün pasif edildi: {product.name}",
        content_type="Product",
        object_id=product.id,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    logger.info(
        f"[PRODUCTS] POST /api/products/{product_id}/deactivate/ - SUCCESS | "
        f"Tenant: {tenant.name} ({tenant.id}) | "
        f"User: {request.user.email} | "
        f"ProductID: {product.id} | "
        f"ProductName: {product.name} | "
        f"Status: {status.HTTP_200_OK}"
    )
    
    return Response({
        'success': True,
        'message': 'Ürün pasif edildi.',
        'product': ProductDetailSerializer(product, context={'request': request}).data,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def product_detail_public(request, urun_slug=None, tenant_slug=None, product_slug=None):
    """
    Public ürün detayı (frontend için).
    
    GET: /api/public/products/urun/{urun_slug}/ (tenant_slug query parameter ile)
    GET: /api/public/{tenant_slug}/products/urun/{urun_slug}/ (path parameter ile)
    
    Not: product_slug parametresi geriye dönük uyumluluk için (eski URL'ler)
    
    Tenant belirleme önceliği:
    1. Path parameter: tenant_slug
    2. Query parameter: ?tenant_slug=xxx
    3. Query parameter: ?tenant_id=xxx
    4. Header: X-Tenant-Slug
    5. Header: X-Tenant-ID
    """
    # urun_slug veya product_slug (geriye dönük uyumluluk)
    product_slug = urun_slug or product_slug
    tenant = None
    
    # 1. Path parameter'dan tenant_slug
    if tenant_slug:
        try:
            from apps.models import Tenant
            tenant = Tenant.objects.get(slug=tenant_slug, is_deleted=False)
        except Tenant.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Mağaza bulunamadı: {tenant_slug}',
            }, status=status.HTTP_404_NOT_FOUND)
    
    # 2. Query parameter'dan tenant_slug
    if not tenant:
        tenant_slug_param = request.query_params.get('tenant_slug')
        if tenant_slug_param:
            try:
                from apps.models import Tenant
                tenant = Tenant.objects.get(slug=tenant_slug_param, is_deleted=False)
            except Tenant.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Mağaza bulunamadı: {tenant_slug_param}',
                }, status=status.HTTP_404_NOT_FOUND)
    
    # 3. Query parameter'dan tenant_id
    if not tenant:
        tenant_id_param = request.query_params.get('tenant_id')
        if tenant_id_param:
            try:
                from apps.models import Tenant
                tenant = Tenant.objects.get(id=tenant_id_param, is_deleted=False)
            except Tenant.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Mağaza bulunamadı: {tenant_id_param}',
                }, status=status.HTTP_404_NOT_FOUND)
    
    # 4. Header'dan tenant_slug
    if not tenant:
        tenant_slug_header = request.headers.get('X-Tenant-Slug')
        if tenant_slug_header:
            try:
                from apps.models import Tenant
                tenant = Tenant.objects.get(slug=tenant_slug_header, is_deleted=False)
            except Tenant.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Mağaza bulunamadı: {tenant_slug_header}',
                }, status=status.HTTP_404_NOT_FOUND)
    
    # 5. Header'dan tenant_id
    if not tenant:
        tenant_id_header = request.headers.get('X-Tenant-ID')
        if tenant_id_header:
            try:
                from apps.models import Tenant
                tenant = Tenant.objects.get(id=tenant_id_header, is_deleted=False)
            except Tenant.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Mağaza bulunamadı: {tenant_id_header}',
                }, status=status.HTTP_404_NOT_FOUND)
    
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı. Lütfen tenant_slug veya tenant_id parametresi gönderin.',
            'hint': 'Örnek: /api/public/products/urun-adi/?tenant_slug=magaza-adi veya Header: X-Tenant-Slug: magaza-adi',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # URL decode yap (boşluklar ve özel karakterler için)
    from urllib.parse import unquote
    decoded_slug = unquote(product_slug)
    
    try:
        product = Product.objects.prefetch_related(
            'images',
            'categories',
            'options',
            'options__values',
            'variants',
            'variants__option_values',
        ).get(
            slug=decoded_slug,
            tenant=tenant,
            is_deleted=False,
            status='active',
            is_visible=True,
        )
    except Product.DoesNotExist:
        # Slug bulunamazsa, name ile de dene (geriye dönük uyumluluk için)
        try:
            product = Product.objects.prefetch_related(
                'images',
                'categories',
                'options',
                'options__values',
                'variants',
                'variants__option_values',
            ).get(
                name=decoded_slug,
                tenant=tenant,
                is_deleted=False,
                status='active',
                is_visible=True,
            )
        except Product.DoesNotExist:
            client_ip = get_client_ip(request)
            logger.warning(
                f"[PRODUCTS] GET /api/public/products/{product_slug}/ - NOT FOUND | "
                f"IP: {client_ip} | "
                f"Tenant: {tenant.name} ({tenant.id}) | "
                f"Slug: {decoded_slug}"
            )
            return Response({
                'success': False,
                'message': 'Ürün bulunamadı.',
                'hint': f'Slug veya isim ile arandı: {decoded_slug}',
            }, status=status.HTTP_404_NOT_FOUND)
    
    # Görüntüleme sayısını artır
    product.view_count += 1
    product.save(update_fields=['view_count'])
    
    serializer = ProductDetailSerializer(product, context={'request': request})
    logger.info(
        f"[PRODUCTS] GET /api/public/products/{product_slug}/ - SUCCESS | "
        f"IP: {get_client_ip(request)} | "
        f"Tenant: {tenant.name} ({tenant.id}) | "
        f"ProductID: {product.id} | "
        f"ProductName: {product.name} | "
        f"ViewCount: {product.view_count} | "
        f"Status: {status.HTTP_200_OK}"
    )
    return Response({
        'success': True,
        'product': serializer.data,
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_all_products(request):
    """
    Tenant'a ait tüm ürünleri veritabanından fiziksel olarak sil.
    ⚠️ UYARI: Bu işlem geri alınamaz! Ürünler veritabanından tamamen silinir.
    
    DELETE: /api/products/delete-all/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        logger.warning(f"[PRODUCTS] DELETE /api/products/delete-all/ | {status.HTTP_400_BAD_REQUEST} | Tenant not found")
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece tenant owner veya admin
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        logger.warning(f"[PRODUCTS] DELETE /api/products/delete-all/ | {status.HTTP_403_FORBIDDEN} | Permission denied")
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Tüm ürünleri al (hem silinmiş hem silinmemiş - hepsini DB'den sileceğiz)
        products = Product.objects.filter(tenant=tenant)
        total_count = products.count()
        
        if total_count == 0:
            logger.info(f"[PRODUCTS] DELETE /api/products/delete-all/ | {status.HTTP_200_OK} | No products to delete | Tenant: {tenant.name}")
            return Response({
                'success': True,
                'message': 'Silinecek ürün bulunamadı.',
                'deleted_count': 0,
            })
        
        # Fiziksel silme - DB'den tamamen sil
        deleted_count, _ = products.delete()
        
        logger.info(
            f"[PRODUCTS] DELETE /api/products/delete-all/ | {status.HTTP_200_OK} | "
            f"Deleted {deleted_count} products | Tenant: {tenant.name} ({tenant.id})"
        )
        
        return Response({
            'success': True,
            'message': f'{deleted_count} ürün başarıyla silindi.',
            'deleted_count': deleted_count,
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"[PRODUCTS] DELETE /api/products/delete-all/ | {status.HTTP_500_INTERNAL_SERVER_ERROR} | Error: {str(e)}")
        return Response({
            'success': False,
            'message': f'Ürün silme hatası: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasStaffPermission])
def category_list_create(request):
    """
    Kategori listesi (GET) veya yeni kategori oluştur (POST).
    
    GET: /api/categories/
    POST: /api/categories/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        queryset = Category.objects.filter(tenant=tenant, is_deleted=False, parent=None)
        serializer = CategorySerializer(queryset, many=True)
        return Response({
            'success': True,
            'categories': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save(tenant=tenant)
            
            # Activity Log
            from apps.services.activity_log_service import ActivityLogService
            ActivityLogService.log(
                tenant=tenant,
                user=request.user,
                action="category_create",
                description=f"Yeni kategori oluşturuldu: {category.name}",
                content_type="Category",
                object_id=category.id,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({
                'success': True,
                'message': 'Kategori oluşturuldu.',
                'category': CategorySerializer(category).data,
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Kategori oluşturulamadı.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def category_list_public(request, tenant_slug=None):
    """
    Public kategori listesi (frontend için).
    
    GET: /api/public/categories/ (tenant_slug query parameter ile)
    GET: /api/public/{tenant_slug}/categories/ (path parameter ile)
    
    Tenant belirleme önceliği:
    1. Path parameter: tenant_slug
    2. Query parameter: ?tenant_slug=xxx
    3. Query parameter: ?tenant_id=xxx
    4. Header: X-Tenant-Slug
    5. Header: X-Tenant-ID
    6. Subdomain/Custom domain (otomatik)
    """
    tenant = None
    
    # 1. Path parameter'dan tenant_slug
    if tenant_slug:
        try:
            from apps.models import Tenant
            tenant = Tenant.objects.get(slug=tenant_slug, is_deleted=False)
        except Tenant.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Mağaza bulunamadı: {tenant_slug}',
            }, status=status.HTTP_404_NOT_FOUND)
    
    # 2. Query parameter'dan tenant_slug
    if not tenant:
        tenant_slug_param = request.query_params.get('tenant_slug')
        if tenant_slug_param:
            try:
                from apps.models import Tenant
                tenant = Tenant.objects.get(slug=tenant_slug_param, is_deleted=False)
            except Tenant.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Mağaza bulunamadı: {tenant_slug_param}',
                }, status=status.HTTP_404_NOT_FOUND)
    
    # 3. Query parameter'dan tenant_id
    if not tenant:
        tenant_id_param = request.query_params.get('tenant_id')
        if tenant_id_param:
            try:
                from apps.models import Tenant
                tenant = Tenant.objects.get(id=tenant_id_param, is_deleted=False)
            except Tenant.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Mağaza bulunamadı: {tenant_id_param}',
                }, status=status.HTTP_404_NOT_FOUND)
    
    # 4. Header'dan tenant_slug
    if not tenant:
        tenant_slug_header = request.headers.get('X-Tenant-Slug')
        if tenant_slug_header:
            try:
                from apps.models import Tenant
                tenant = Tenant.objects.get(slug=tenant_slug_header, is_deleted=False)
            except Tenant.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Mağaza bulunamadı: {tenant_slug_header}',
                }, status=status.HTTP_404_NOT_FOUND)
    
    # 5. Header'dan tenant_id
    if not tenant:
        tenant_id_header = request.headers.get('X-Tenant-ID')
        if tenant_id_header:
            try:
                from apps.models import Tenant
                tenant = Tenant.objects.get(id=tenant_id_header, is_deleted=False)
            except Tenant.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Mağaza bulunamadı: {tenant_id_header}',
                }, status=status.HTTP_404_NOT_FOUND)
    
    # 6. Middleware'den tenant (subdomain/custom domain)
    if not tenant:
        tenant = get_tenant_from_request(request)
    
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı. Lütfen tenant_slug veya tenant_id parametresi gönderin.',
            'hint': 'Örnek: /api/public/categories/?tenant_slug=magaza-adi veya Header: X-Tenant-Slug: magaza-adi',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece aktif kategorileri getir (ana kategoriler - parent=None)
    queryset = Category.objects.filter(
        tenant=tenant,
        is_deleted=False,
        parent=None,
        is_active=True
    ).order_by('name')
    
    serializer = CategorySerializer(queryset, many=True, context={'request': request})
    logger.info(f"[CATEGORIES] GET /api/public/categories/ | 200 | Count: {queryset.count()} | Tenant: {tenant.name}")
    
    return Response({
        'success': True,
        'categories': serializer.data,
    })


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, HasStaffPermission])
def category_detail(request, category_id):
    """
    Kategori detayı (GET), güncelleme (PATCH) veya silme (DELETE).
    
    GET: /api/categories/{category_id}/
    PATCH: /api/categories/{category_id}/  (parent değiştirmek için)
    DELETE: /api/categories/{category_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        category = Category.objects.get(id=category_id, tenant=tenant, is_deleted=False)
    except Category.DoesNotExist:
        logger.warning(f"[CATEGORIES] {request.method} /api/categories/{category_id}/ | 404 | Category not found")
        return Response({
            'success': False,
            'message': 'Kategori bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Not: Yetki kontrolü HasStaffPermission dekoratörü tarafından zaten yapılıyor.
    
    if request.method == 'GET':
        serializer = CategorySerializer(category, context={'request': request})
        logger.info(
            f"[CATEGORIES] GET /api/categories/{category_id}/ - SUCCESS | "
            f"Tenant: {tenant.name} ({tenant.id}) | "
            f"CategoryID: {category.id} | "
            f"CategoryName: {category.name}"
        )
        return Response({
            'success': True,
            'category': serializer.data,
        })
    
    elif request.method == 'PATCH':
        serializer = CategorySerializer(
            category,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            
            # Activity Log
            from apps.services.activity_log_service import ActivityLogService
            ActivityLogService.log(
                tenant=tenant,
                user=request.user,
                action="category_update",
                description=f"Kategori güncellendi: {category.name}",
                content_type="Category",
                object_id=category.id,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            logger.info(
                f"[CATEGORIES] PATCH /api/categories/{category_id}/ - SUCCESS | "
                f"Tenant: {tenant.name} ({tenant.id}) | "
                f"User: {request.user.email} | "
                f"CategoryID: {category.id} | "
                f"CategoryName: {category.name}"
            )
            return Response({
                'success': True,
                'message': 'Kategori güncellendi.',
                'category': serializer.data,
            })
        logger.warning(
            f"[CATEGORIES] PATCH /api/categories/{category_id}/ - VALIDATION ERROR | "
            f"Tenant: {tenant.name} ({tenant.id}) | "
            f"Errors: {serializer.errors}"
        )
        return Response({
            'success': False,
            'message': 'Kategori güncellenemedi.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        category.is_deleted = True
        category.save()
        
        # Activity Log
        from apps.services.activity_log_service import ActivityLogService
        ActivityLogService.log(
            tenant=tenant,
            user=request.user,
            action="category_delete",
            description=f"Kategori silindi: {category.name}",
            content_type="Category",
            object_id=category.id,
            ip_address=get_client_ip(request)
        )
        
        logger.info(
            f"[CATEGORIES] DELETE /api/categories/{category_id}/ - SUCCESS | "
            f"Tenant: {tenant.name} ({tenant.id}) | "
            f"User: {request.user.email} | "
            f"CategoryID: {category.id} | "
            f"CategoryName: {category.name}"
        )
        return Response({
            'success': True,
            'message': 'Kategori silindi.',
        })

# Set staff permissions
product_list_create.cls.staff_permission = 'products'
product_detail.cls.staff_permission = 'products'
category_list_create.cls.staff_permission = 'products'
category_detail.cls.staff_permission = 'products'
