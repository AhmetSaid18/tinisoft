"""
Review views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Avg, Count
from django.utils import timezone
from apps.models import ProductReview, ReviewHelpful, Product
from apps.serializers.review import (
    ProductReviewSerializer, ProductReviewCreateSerializer,
    ProductReviewUpdateSerializer
)
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class ReviewPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def review_list_create(request, product_id=None):
    """
    Ürün yorumları listesi (GET) veya yeni yorum oluştur (POST).
    
    GET: /api/products/{product_id}/reviews/
    POST: /api/products/{product_id}/reviews/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Ürünü kontrol et
    try:
        product = Product.objects.get(id=product_id, tenant=tenant, is_deleted=False)
    except Product.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Ürün bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Filtreleme
        queryset = ProductReview.objects.filter(
            product=product,
            tenant=tenant,
            is_deleted=False
        )
        
        # Status filtresi (sadece onaylananları göster - public için)
        status_filter = request.query_params.get('status', 'approved')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Rating filtresi
        rating = request.query_params.get('rating')
        if rating:
            queryset = queryset.filter(rating=rating)
        
        # Sıralama
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        paginator = ReviewPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = ProductReviewSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response({
                'success': True,
                'reviews': serializer.data,
                'summary': {
                    'total_reviews': queryset.count(),
                    'average_rating': queryset.aggregate(Avg('rating'))['rating__avg'] or 0,
                    'rating_distribution': queryset.values('rating').annotate(count=Count('id')).order_by('-rating')
                }
            })
        
        serializer = ProductReviewSerializer(queryset, many=True, context={'request': request})
        return Response({
            'success': True,
            'reviews': serializer.data,
        })
    
    elif request.method == 'POST':
        # Yeni yorum oluştur
        serializer = ProductReviewCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Müşteri bilgilerini al
            customer = None
            customer_name = serializer.validated_data.get('customer_name', '')
            customer_email = serializer.validated_data.get('customer_email', '')
            
            if request.user.is_authenticated:
                customer = request.user
                customer_name = customer.get_full_name() or customer_name
                customer_email = customer.email or customer_email
            
            # IP adresini al
            ip_address = None
            if request:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0]
                else:
                    ip_address = request.META.get('REMOTE_ADDR')
            
            # Verified purchase kontrolü (sipariş verdi mi?)
            verified_purchase = False
            if customer:
                from apps.models import Order
                verified_purchase = Order.objects.filter(
                    tenant=tenant,
                    customer_email=customer_email,
                    status__in=['completed', 'delivered']
                ).exists()
            
            # Yorum oluştur
            review = ProductReview.objects.create(
                tenant=tenant,
                product=product,
                customer=customer,
                customer_name=customer_name,
                customer_email=customer_email,
                rating=serializer.validated_data['rating'],
                title=serializer.validated_data.get('title', ''),
                comment=serializer.validated_data['comment'],
                images=serializer.validated_data.get('images', []),
                ip_address=ip_address,
                verified_purchase=verified_purchase,
                status='pending'  # Onay bekliyor
            )
            
            return Response({
                'success': True,
                'message': 'Yorumunuz gönderildi. Onay bekliyor.',
                'review': ProductReviewSerializer(review, context={'request': request}).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def review_detail(request, review_id):
    """
    Yorum detayı (GET), güncelle (PATCH) veya sil (DELETE).
    
    GET: /api/reviews/{review_id}/
    PATCH: /api/reviews/{review_id}/ (admin only)
    DELETE: /api/reviews/{review_id}/ (admin only)
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        review = ProductReview.objects.get(id=review_id, tenant=tenant, is_deleted=False)
    except ProductReview.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Yorum bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ProductReviewSerializer(review, context={'request': request})
        return Response({
            'success': True,
            'review': serializer.data,
        })
    
    elif request.method == 'PATCH':
        # Sadece admin veya tenant owner
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ProductReviewUpdateSerializer(
            review,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Yorum güncellendi.',
                'review': ProductReviewSerializer(review, context={'request': request}).data,
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
        
        review.soft_delete()
        return Response({
            'success': True,
            'message': 'Yorum silindi.',
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def review_helpful(request, review_id):
    """
    Yorum yardımcı oldu mu? (Like/Dislike)
    
    POST: /api/reviews/{review_id}/helpful/
    Body: {"is_helpful": true}
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        review = ProductReview.objects.get(id=review_id, tenant=tenant, is_deleted=False)
    except ProductReview.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Yorum bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    is_helpful = request.data.get('is_helpful', True)
    customer = request.user if request.user.is_authenticated else None
    
    # IP adresini al
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
    
    # Daha önce oy vermiş mi?
    helpful, created = ReviewHelpful.objects.get_or_create(
        review=review,
        customer=customer,
        ip_address=ip_address if not customer else None,
        defaults={'is_helpful': is_helpful}
    )
    
    if not created:
        # Zaten oy vermiş, güncelle
        helpful.is_helpful = is_helpful
        helpful.save()
    
    # Helpful count'u güncelle
    review.helpful_count = ReviewHelpful.objects.filter(review=review, is_helpful=True).count()
    review.save()
    
    return Response({
        'success': True,
        'message': 'Oyunuz kaydedildi.',
        'helpful_count': review.helpful_count,
    }, status=status.HTTP_200_OK)

