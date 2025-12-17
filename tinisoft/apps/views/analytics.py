"""
Analytics views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.models import AnalyticsEvent, SalesReport, ProductAnalytics, Order, OrderItem
from apps.serializers.analytics import (
    AnalyticsEventSerializer, AnalyticsEventCreateSerializer,
    SalesReportSerializer, ProductAnalyticsSerializer
)
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class AnalyticsPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


@api_view(['POST'])
@permission_classes([AllowAny])  # Public endpoint - analytics tracking için
def analytics_event_create(request):
    """
    Analytics event oluştur (public endpoint).
    
    POST: /api/analytics/events/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = AnalyticsEventCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        # IP adresini al
        ip_address = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        # User agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Referrer
        referrer = request.META.get('HTTP_REFERER', '')
        
        # URL
        url = request.build_absolute_uri()
        
        # Customer bilgisi
        customer = None
        if request.user.is_authenticated:
            customer = request.user
        
        event = AnalyticsEvent.objects.create(
            tenant=tenant,
            customer=customer,
            session_id=serializer.validated_data.get('session_id', ''),
            event_type=serializer.validated_data['event_type'],
            event_data=serializer.validated_data.get('event_data', {}),
            ip_address=ip_address or serializer.validated_data.get('ip_address'),
            user_agent=user_agent or serializer.validated_data.get('user_agent', ''),
            referrer=referrer or serializer.validated_data.get('referrer', ''),
            url=url or serializer.validated_data.get('url', ''),
        )
        
        return Response({
            'success': True,
            'message': 'Event kaydedildi.',
            'event': AnalyticsEventSerializer(event).data,
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'errors': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_events_list(request):
    """
    Analytics events listesi.
    
    GET: /api/analytics/events/
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
    
    queryset = AnalyticsEvent.objects.filter(tenant=tenant)
    
    # Filtreleme
    event_type = request.query_params.get('event_type')
    if event_type:
        queryset = queryset.filter(event_type=event_type)
    
    customer_id = request.query_params.get('customer_id')
    if customer_id:
        queryset = queryset.filter(customer_id=customer_id)
    
    session_id = request.query_params.get('session_id')
    if session_id:
        queryset = queryset.filter(session_id=session_id)
    
    # Tarih aralığı
    date_from = request.query_params.get('date_from')
    if date_from:
        queryset = queryset.filter(created_at__gte=date_from)
    
    date_to = request.query_params.get('date_to')
    if date_to:
        queryset = queryset.filter(created_at__lte=date_to)
    
    # Sıralama
    queryset = queryset.order_by('-created_at')
    
    # Pagination
    paginator = AnalyticsPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = AnalyticsEventSerializer(page, many=True)
        return paginator.get_paginated_response({
            'success': True,
            'events': serializer.data,
        })
    
    serializer = AnalyticsEventSerializer(queryset, many=True)
    return Response({
        'success': True,
        'events': serializer.data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_dashboard(request):
    """
    Analytics dashboard verileri.
    
    GET: /api/analytics/dashboard/
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
    
    # Tarih aralığı (varsayılan: son 30 gün)
    days = int(request.query_params.get('days', 30))
    date_from = timezone.now() - timedelta(days=days)
    
    # Toplam siparişler
    total_orders = Order.objects.filter(
        tenant=tenant,
        created_at__gte=date_from,
        is_deleted=False
    ).count()
    
    # Toplam gelir
    total_revenue = Order.objects.filter(
        tenant=tenant,
        created_at__gte=date_from,
        status__in=['delivered'],
        is_deleted=False
    ).aggregate(Sum('total'))['total__sum'] or Decimal('0.00')
    
    # Ortalama sipariş değeri
    avg_order_value = Order.objects.filter(
        tenant=tenant,
        created_at__gte=date_from,
        status__in=['delivered'],
        is_deleted=False
    ).aggregate(Avg('total'))['total__avg'] or Decimal('0.00')
    
    # Toplam ürün satışı
    total_products_sold = OrderItem.objects.filter(
        order__tenant=tenant,
        order__created_at__gte=date_from,
        order__status__in=['delivered'],
        order__is_deleted=False
    ).aggregate(Sum('quantity'))['quantity__sum'] or 0
    
    # Yeni müşteriler
    new_customers = Order.objects.filter(
        tenant=tenant,
        created_at__gte=date_from,
        is_deleted=False
    ).values('customer_email').distinct().count()
    
    # Event istatistikleri
    event_stats = AnalyticsEvent.objects.filter(
        tenant=tenant,
        created_at__gte=date_from
    ).values('event_type').annotate(count=Count('id')).order_by('-count')
    
    return Response({
        'success': True,
        'dashboard': {
            'period': {
                'days': days,
                'date_from': date_from,
                'date_to': timezone.now(),
            },
            'orders': {
                'total': total_orders,
                'total_revenue': str(total_revenue),
                'average_order_value': str(avg_order_value),
                'total_products_sold': total_products_sold,
            },
            'customers': {
                'new_customers': new_customers,
            },
            'events': list(event_stats),
        },
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_reports_list(request):
    """
    Sales reports listesi.
    
    GET: /api/analytics/reports/
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
    
    queryset = SalesReport.objects.filter(tenant=tenant)
    
    # Filtreleme
    period = request.query_params.get('period')
    if period:
        queryset = queryset.filter(period=period)
    
    # Sıralama
    queryset = queryset.order_by('-period_start')
    
    # Pagination
    paginator = AnalyticsPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = SalesReportSerializer(page, many=True)
        return paginator.get_paginated_response({
            'success': True,
            'reports': serializer.data,
        })
    
    serializer = SalesReportSerializer(queryset, many=True)
    return Response({
        'success': True,
        'reports': serializer.data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def product_analytics_list(request):
    """
    Product analytics listesi.
    
    GET: /api/analytics/products/
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
    
    queryset = ProductAnalytics.objects.filter(tenant=tenant)
    
    # Filtreleme
    product_id = request.query_params.get('product_id')
    if product_id:
        queryset = queryset.filter(product_id=product_id)
    
    date_from = request.query_params.get('date_from')
    if date_from:
        queryset = queryset.filter(report_date__gte=date_from)
    
    date_to = request.query_params.get('date_to')
    if date_to:
        queryset = queryset.filter(report_date__lte=date_to)
    
    # Sıralama
    ordering = request.query_params.get('ordering', '-report_date')
    queryset = queryset.order_by(ordering)
    
    # Pagination
    paginator = AnalyticsPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = ProductAnalyticsSerializer(page, many=True)
        return paginator.get_paginated_response({
            'success': True,
            'analytics': serializer.data,
        })
    
    serializer = ProductAnalyticsSerializer(queryset, many=True)
    return Response({
        'success': True,
        'analytics': serializer.data,
    })

