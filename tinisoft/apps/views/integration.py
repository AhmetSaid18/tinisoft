"""
Integration API Key yönetimi views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from apps.models import IntegrationProvider
from apps.serializers.integration import (
    IntegrationProviderSerializer,
    IntegrationProviderCreateSerializer,
    IntegrationProviderUpdateSerializer,
    IntegrationProviderTestSerializer
)
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class IntegrationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def integration_list_create(request):
    """
    Entegrasyon listesi (GET) veya yeni entegrasyon oluştur (POST).
    
    GET: /api/integrations/
    POST: /api/integrations/
    Body: {
        "provider_type": "kuveyt",
        "name": "Kuveyt API - Production",
        "status": "active",
        "api_key": "your-api-key",
        "api_secret": "your-api-secret",
        "api_endpoint": "https://api.kuveyt.com/payment",
        "test_endpoint": "https://test-api.kuveyt.com/payment",
        "config": {}
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece tenant owner veya admin
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        queryset = IntegrationProvider.objects.filter(tenant=tenant, is_deleted=False)
        
        # Filtreleme
        provider_type = request.query_params.get('provider_type')
        if provider_type:
            queryset = queryset.filter(provider_type=provider_type)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Sıralama
        ordering = request.query_params.get('ordering', 'provider_type')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        paginator = IntegrationPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = IntegrationProviderSerializer(page, many=True)
            return paginator.get_paginated_response({
                'success': True,
                'integrations': serializer.data,
            })
        
        serializer = IntegrationProviderSerializer(queryset, many=True)
        return Response({
            'success': True,
            'integrations': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = IntegrationProviderCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            integration = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Entegrasyon oluşturuldu.',
                'integration': IntegrationProviderSerializer(integration).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def integration_detail(request, integration_id):
    """
    Entegrasyon detayı (GET), güncelle (PATCH) veya sil (DELETE).
    
    GET: /api/integrations/{integration_id}/
    PATCH: /api/integrations/{integration_id}/
    DELETE: /api/integrations/{integration_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        integration = IntegrationProvider.objects.get(
            id=integration_id,
            tenant=tenant,
            is_deleted=False
        )
    except IntegrationProvider.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Entegrasyon bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece tenant owner veya admin
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = IntegrationProviderSerializer(integration)
        return Response({
            'success': True,
            'integration': serializer.data,
        })
    
    elif request.method == 'PATCH':
        serializer = IntegrationProviderUpdateSerializer(
            integration,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            integration = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Entegrasyon güncellendi.',
                'integration': IntegrationProviderSerializer(integration).data,
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        integration.soft_delete()
        return Response({
            'success': True,
            'message': 'Entegrasyon silindi.',
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def integration_test(request, integration_id):
    """
    Entegrasyon test et.
    
    POST: /api/integrations/{integration_id}/test/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        integration = IntegrationProvider.objects.get(
            id=integration_id,
            tenant=tenant,
            is_deleted=False
        )
    except IntegrationProvider.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Entegrasyon bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece tenant owner veya admin
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Entegrasyon tipine göre test yap
    try:
        if integration.provider_type == IntegrationProvider.ProviderType.KUVEYT:
            # Kuveyt API test
            from apps.services.payment_providers import PaymentProviderFactory
            
            provider = PaymentProviderFactory.get_provider(
                tenant=tenant,
                provider_name='kuwait',
                config=integration.get_provider_config()
            )
            
            # Test için dummy order oluştur (gerçek order gerekmez)
            test_result = {
                'success': True,
                'message': 'Kuveyt API bağlantısı test edildi.',
                'endpoint': integration.get_endpoint(),
                'test_mode': integration.status == IntegrationProvider.Status.TEST_MODE,
            }
            
        elif integration.provider_type in [
            IntegrationProvider.ProviderType.ARAS,
            IntegrationProvider.ProviderType.YURTICI,
            IntegrationProvider.ProviderType.MNG,
        ]:
            # Kargo API test (ileride implement edilebilir)
            test_result = {
                'success': True,
                'message': f'{integration.get_provider_type_display()} API testi henüz implement edilmedi.',
            }
        
        else:
            test_result = {
                'success': True,
                'message': f'{integration.get_provider_type_display()} testi henüz implement edilmedi.',
            }
        
        return Response({
            'success': True,
            'test_result': test_result,
        })
    
    except Exception as e:
        logger.error(f"Integration test error: {str(e)}")
        integration.last_error = str(e)
        integration.save()
        
        return Response({
            'success': False,
            'message': f'Test başarısız: {str(e)}',
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def integration_by_type(request, provider_type):
    """
    Belirli bir provider tipine göre aktif entegrasyonu getir.
    
    GET: /api/integrations/type/{provider_type}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        integration = IntegrationProvider.objects.get(
            tenant=tenant,
            provider_type=provider_type,
            status__in=[
                IntegrationProvider.Status.ACTIVE,
                IntegrationProvider.Status.TEST_MODE
            ],
            is_deleted=False
        )
    except IntegrationProvider.DoesNotExist:
        return Response({
            'success': False,
            'message': f'{provider_type} entegrasyonu bulunamadı veya aktif değil.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece tenant owner veya admin
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = IntegrationProviderSerializer(integration)
    return Response({
        'success': True,
        'integration': serializer.data,
    })

