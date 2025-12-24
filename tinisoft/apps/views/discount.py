"""
Discount views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, F
from django.utils import timezone
from decimal import Decimal
from apps.models import Coupon, Promotion
from apps.serializers.discount import (
    CouponSerializer, CouponValidateSerializer,
    PromotionSerializer
)
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class CouponPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def coupon_list_create(request):
    """
    Kupon listesi (GET) veya yeni kupon oluştur (POST).
    
    GET: /api/coupons/
    POST: /api/coupons/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        logger.warning(f"[COUPONS] {request.method} /api/coupons/ | 400 | Tenant not found")
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı. Lütfen subdomain, custom domain veya X-Tenant-ID header\'ı ile istek gönderin.',
            'error_code': 'TENANT_NOT_FOUND',
            'hint': 'Tenant bilgisi şu yollarla gönderilebilir: 1) Subdomain (örn: tenant-slug.tinisoft.com.tr), 2) Custom domain, 3) X-Tenant-ID header, 4) Authenticated user\'ın tenant\'ı'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        logger.warning(f"[COUPONS] {request.method} /api/coupons/ | 403 | Permission denied | User: {request.user.email}")
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        queryset = Coupon.objects.filter(tenant=tenant, is_deleted=False)
        
        # Filtreleme
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        code = request.query_params.get('code')
        if code:
            queryset = queryset.filter(code__icontains=code)
        
        # Sıralama
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        paginator = CouponPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = CouponSerializer(page, many=True, context={'request': request})
            response = paginator.get_paginated_response(serializer.data)
            response.data['success'] = True
            response.data['coupons'] = response.data.pop('results')
            logger.info(f"[COUPONS] GET /api/coupons/ | 200 | Count: {len(page)}/{paginator.page.paginator.count}")
            return response
        
        serializer = CouponSerializer(queryset, many=True, context={'request': request})
        logger.info(f"[COUPONS] GET /api/coupons/ | 200 | Count: {queryset.count()}")
        return Response({
            'success': True,
            'coupons': serializer.data,
        })
    
    elif request.method == 'POST':
        # Frontend camelCase -> backend snake_case dönüşümü
        data = dict(request.data)
        camel_to_snake = {
            'discountType': 'discount_type',
            'discountValue': 'discount_value',
            'minOrderAmount': 'min_order_amount',
            'maxDiscountAmount': 'max_discount_amount',
            'maxUsageCount': 'max_usage_count',
            'maxUsagePerCustomer': 'max_usage_per_customer',
            'validFrom': 'valid_from',
            'validTo': 'valid_to',
            'appliesToAllProducts': 'applies_to_all_products',
            'appliesToAllCustomers': 'applies_to_all_customers',
            'isActive': 'is_active',
        }
        
        # CamelCase field'ları snake_case'e çevir
        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in data:
                data[snake_key] = data.pop(camel_key)
        
        # discount_type değerini normalize et (Percentage -> percentage)
        if 'discount_type' in data:
            discount_type = str(data['discount_type']).lower()
            # Frontend'den gelebilecek değerler
            type_mapping = {
                'percentage': 'percentage',
                'fixed': 'fixed',
                'free_shipping': 'free_shipping',
                'freeshipping': 'free_shipping',
            }
            data['discount_type'] = type_mapping.get(discount_type, discount_type)
        
        serializer = CouponSerializer(data=data, context={'request': request})
        
        if not serializer.is_valid():
            logger.error(f"[COUPONS] POST /api/coupons/ | 400 | Validation failed | Errors: {list(serializer.errors.keys())}")
            return Response({
                'success': False,
                'message': 'Kupon oluşturma başarısız. Lütfen gerekli alanları kontrol edin.',
                'errors': serializer.errors,
                'received_fields': received_fields,
                'missing_required_fields': required_fields,
                'missing_optional_fields': optional_fields,
                'hint': 'Gerekli alanlar: code, name, discount_type, discount_value, is_active'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Code unique kontrolü
        code = serializer.validated_data['code']
        if Coupon.objects.filter(tenant=tenant, code=code, is_deleted=False).exists():
            logger.warning(f"[COUPONS] POST /api/coupons/ | 400 | Duplicate code: {code}")
            return Response({
                'success': False,
                'message': 'Bu kupon kodu zaten kullanılıyor.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        coupon = serializer.save(tenant=tenant)
        logger.info(f"[COUPONS] POST /api/coupons/ | 201 | Created | Code: {coupon.code}")
        return Response({
            'success': True,
            'message': 'Kupon oluşturuldu.',
            'coupon': CouponSerializer(coupon, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def coupon_detail(request, coupon_id):
    """
    Kupon detayı (GET), güncelle (PUT/PATCH) veya sil (DELETE).
    
    GET: /api/coupons/{coupon_id}/
    PUT: /api/coupons/{coupon_id}/ (tüm alanları güncelle)
    PATCH: /api/coupons/{coupon_id}/ (kısmi güncelleme)
    DELETE: /api/coupons/{coupon_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        logger.warning(f"[COUPONS] {request.method} /api/coupons/{coupon_id}/ | 400 | Tenant not found")
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        coupon = Coupon.objects.get(id=coupon_id, tenant=tenant, is_deleted=False)
    except Coupon.DoesNotExist:
        logger.warning(f"[COUPONS] {request.method} /api/coupons/{coupon_id}/ | 404 | Coupon not found")
        return Response({
            'success': False,
            'message': 'Kupon bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = CouponSerializer(coupon, context={'request': request})
        logger.info(f"[COUPONS] GET /api/coupons/{coupon_id}/ | 200 | Code: {coupon.code}")
        return Response({
            'success': True,
            'coupon': serializer.data,
        })
    
    elif request.method in ['PUT', 'PATCH']:
        # Sadece admin veya tenant owner
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            logger.warning(f"[COUPONS] {request.method} /api/coupons/{coupon_id}/ | 403 | Permission denied")
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Frontend camelCase -> backend snake_case dönüşümü
        data = dict(request.data)
        camel_to_snake = {
            'discountType': 'discount_type',
            'discountValue': 'discount_value',
            'minOrderAmount': 'min_order_amount',
            'maxDiscountAmount': 'max_discount_amount',
            'maxUsageCount': 'max_usage_count',
            'maxUsagePerCustomer': 'max_usage_per_customer',
            'validFrom': 'valid_from',
            'validTo': 'valid_to',
            'appliesToAllProducts': 'applies_to_all_products',
            'appliesToAllCustomers': 'applies_to_all_customers',
            'isActive': 'is_active',
        }
        
        # CamelCase field'ları snake_case'e çevir
        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in data:
                data[snake_key] = data.pop(camel_key)
        
        # discount_type değerini normalize et (Percentage -> percentage)
        if 'discount_type' in data:
            discount_type = str(data['discount_type']).lower()
            type_mapping = {
                'percentage': 'percentage',
                'fixed': 'fixed',
                'free_shipping': 'free_shipping',
                'freeshipping': 'free_shipping',
            }
            data['discount_type'] = type_mapping.get(discount_type, discount_type)
        
        serializer = CouponSerializer(
            coupon,
            data=data,
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Code değişikliği kontrolü
            if 'code' in serializer.validated_data:
                new_code = serializer.validated_data['code']
                if new_code != coupon.code:
                    if Coupon.objects.filter(tenant=tenant, code=new_code, is_deleted=False).exclude(id=coupon.id).exists():
                        logger.warning(f"[COUPONS] {request.method} /api/coupons/{coupon_id}/ | 400 | Duplicate code: {new_code}")
                        return Response({
                            'success': False,
                            'message': 'Bu kupon kodu zaten kullanılıyor.',
                        }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            logger.info(f"[COUPONS] {request.method} /api/coupons/{coupon_id}/ | 200 | Updated | Code: {coupon.code}")
            return Response({
                'success': True,
                'message': 'Kupon güncellendi.',
                'coupon': CouponSerializer(coupon, context={'request': request}).data,
            })
        
        logger.error(f"[COUPONS] {request.method} /api/coupons/{coupon_id}/ | 400 | Validation failed | Errors: {list(serializer.errors.keys())}")
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Sadece admin veya tenant owner
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            logger.warning(f"[COUPONS] DELETE /api/coupons/{coupon_id}/ | 403 | Permission denied")
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        coupon.soft_delete()
        logger.info(f"[COUPONS] DELETE /api/coupons/{coupon_id}/ | 200 | Deleted | Code: {coupon.code}")
        return Response({
            'success': True,
            'message': 'Kupon silindi.',
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def coupon_validate(request):
    """
    Kupon doğrula ve indirim tutarını hesapla.
    
    POST: /api/coupons/validate/
    Body: {"code": "KUPON123", "order_amount": 100.00, "customer_email": "customer@example.com"}
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = CouponValidateSerializer(data=request.data)
    
    if serializer.is_valid():
        code = serializer.validated_data['code']
        order_amount = Decimal(str(serializer.validated_data.get('order_amount', 0.00)))
        customer_email = serializer.validated_data.get('customer_email')
        
        # Kuponu bul
        try:
            coupon = Coupon.objects.get(
                code=code,
                tenant=tenant,
                is_deleted=False
            )
        except Coupon.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Kupon bulunamadı.',
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Kupon geçerliliğini kontrol et
        is_valid, message = coupon.is_valid(customer_email, order_amount)
        
        if not is_valid:
            return Response({
                'success': False,
                'message': message,
                'valid': False,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # İndirim tutarını hesapla
        discount_amount = coupon.calculate_discount(order_amount)
        final_amount = order_amount - discount_amount
        
        return Response({
            'success': True,
            'valid': True,
            'message': 'Kupon geçerli.',
            'coupon': {
                'id': str(coupon.id),
                'code': coupon.code,
                'name': coupon.name,
                'discount_type': coupon.discount_type,
                'discount_value': str(coupon.discount_value),
            },
            'discount': {
                'discount_amount': str(discount_amount),
                'order_amount': str(order_amount),
                'final_amount': str(final_amount),
            },
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'errors': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def coupon_list_public(request):
    """
    Public kupon listesi - Müşterilerin görebileceği aktif kuponlar.
    
    GET: /api/public/coupons/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    from django.utils import timezone
    
    # Sadece aktif ve geçerli kuponları göster
    queryset = Coupon.objects.filter(
        tenant=tenant,
        is_deleted=False,
        is_active=True
    )
    
    # Tarih kontrolü
    now = timezone.now()
    queryset = queryset.filter(
        valid_from__lte=now
    ).filter(
        Q(valid_until__isnull=True) | Q(valid_until__gte=now)
    )
    
    # Kullanım limiti kontrolü (limit varsa ve dolmuşsa gösterme)
    queryset = queryset.filter(
        Q(usage_limit__isnull=True) | Q(usage_count__lt=F('usage_limit'))
    )
    
    # Sıralama
    queryset = queryset.order_by('-created_at')
    
    # Basit serializer (sadece gerekli bilgiler)
    coupons_data = []
    for coupon in queryset:
        coupons_data.append({
            'code': coupon.code,
            'name': coupon.name,
            'description': coupon.description,
            'discount_type': coupon.discount_type,
            'discount_value': str(coupon.discount_value),
            'minimum_order_amount': str(coupon.minimum_order_amount),
            'valid_until': coupon.valid_until.isoformat() if coupon.valid_until else None,
        })
    
    return Response({
        'success': True,
        'coupons': coupons_data,
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def promotion_list_create(request):
    """
    Promosyon listesi (GET) veya yeni promosyon oluştur (POST).
    
    GET: /api/promotions/
    POST: /api/promotions/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        queryset = Promotion.objects.filter(tenant=tenant, is_deleted=False)
        
        # Filtreleme
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        promotion_type = request.query_params.get('promotion_type')
        if promotion_type:
            queryset = queryset.filter(promotion_type=promotion_type)
        
        # Sıralama
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        serializer = PromotionSerializer(queryset, many=True, context={'request': request})
        return Response({
            'success': True,
            'promotions': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = PromotionSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            promotion = serializer.save(tenant=tenant)
            
            return Response({
                'success': True,
                'message': 'Promosyon oluşturuldu.',
                'promotion': PromotionSerializer(promotion, context={'request': request}).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def promotion_detail(request, promotion_id):
    """
    Promosyon detayı (GET), güncelle (PATCH) veya sil (DELETE).
    
    GET: /api/promotions/{promotion_id}/
    PATCH: /api/promotions/{promotion_id}/
    DELETE: /api/promotions/{promotion_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        promotion = Promotion.objects.get(id=promotion_id, tenant=tenant, is_deleted=False)
    except Promotion.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Promosyon bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = PromotionSerializer(promotion, context={'request': request})
        return Response({
            'success': True,
            'promotion': serializer.data,
        })
    
    elif request.method == 'PATCH':
        # Sadece admin veya tenant owner
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PromotionSerializer(
            promotion,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Promosyon güncellendi.',
                'promotion': PromotionSerializer(promotion, context={'request': request}).data,
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Sadece admin veya tenant owner
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        promotion.soft_delete()
        return Response({
            'success': True,
            'message': 'Promosyon silindi.',
        }, status=status.HTTP_200_OK)

