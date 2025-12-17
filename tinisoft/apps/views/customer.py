"""
Customer views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from apps.models import Customer
from apps.serializers.customer import CustomerListSerializer, CustomerDetailSerializer
from apps.services.customer_service import CustomerService
from apps.permissions import IsTenantOwnerOfObject
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class CustomerPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_list(request):
    """
    Müşteri listesi.
    
    GET: /api/customers/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    queryset = Customer.objects.filter(tenant=tenant, is_deleted=False)
    
    # Arama
    search = request.query_params.get('search')
    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(phone__icontains=search)
        )
    
    # Aktif/pasif filtresi
    is_active = request.query_params.get('is_active')
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active.lower() == 'true')
    
    # Müşteri grubu filtresi
    customer_group = request.query_params.get('customer_group')
    if customer_group:
        queryset = queryset.filter(customer_group=customer_group)
    
    # Sıralama
    ordering = request.query_params.get('ordering', '-created_at')
    queryset = queryset.order_by(ordering)
    
    # Pagination
    paginator = CustomerPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = CustomerListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    serializer = CustomerListSerializer(queryset, many=True)
    return Response({
        'success': True,
        'customers': serializer.data,
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def customer_detail(request, customer_id):
    """
    Müşteri detayı (GET) veya güncelleme (PATCH).
    
    GET: /api/customers/{customer_id}/
    PATCH: /api/customers/{customer_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        customer = Customer.objects.get(id=customer_id, tenant=tenant, is_deleted=False)
    except Customer.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Müşteri bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Permission kontrolü
    # TenantUser sadece kendi profiline erişebilir
    if request.user.is_tenant_user:
        if customer.user != request.user:
            return Response({
                'success': False,
                'message': 'Bu müşteri profiline erişim yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
    elif not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = CustomerDetailSerializer(customer)
        return Response({
            'success': True,
            'customer': serializer.data,
        })
    
    elif request.method == 'PATCH':
        serializer = CustomerDetailSerializer(
            customer,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            
            # İstatistikleri güncelle
            CustomerService.update_customer_statistics(customer)
            
            return Response({
                'success': True,
                'message': 'Müşteri güncellendi.',
                'customer': serializer.data,
            })
        return Response({
            'success': False,
            'message': 'Müşteri güncellenemedi.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_customer_statistics(request, customer_id):
    """
    Müşteri istatistiklerini güncelle.
    
    POST: /api/customers/{customer_id}/update-statistics/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        customer = Customer.objects.get(id=customer_id, tenant=tenant, is_deleted=False)
    except Customer.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Müşteri bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    CustomerService.update_customer_statistics(customer)
    
    serializer = CustomerDetailSerializer(customer)
    return Response({
        'success': True,
        'message': 'Müşteri istatistikleri güncellendi.',
        'customer': serializer.data,
    })

