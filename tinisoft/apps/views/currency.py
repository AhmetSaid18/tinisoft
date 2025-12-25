"""
Currency views - Para birimi yönetimi ve TCMB entegrasyonu.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from apps.models import Currency
from apps.serializers.currency import CurrencySerializer
from apps.services.currency_service import CurrencyService
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def currency_list(request):
    """
    Aktif para birimlerini listele (public - frontend için).
    
    GET: /api/public/currencies/
    Header: X-Tenant-Slug veya X-Tenant-ID (opsiyonel)
    Query: ?tenant_slug=xxx veya ?tenant_id=xxx
    """
    tenant = get_tenant_from_request(request)
    
    # Tenant bulunamazsa query param'dan dene
    if not tenant:
        tenant_slug = request.query_params.get('tenant_slug')
        tenant_id = request.query_params.get('tenant_id')
        
        if tenant_slug:
            try:
                from apps.models import Tenant
                tenant = Tenant.objects.get(slug=tenant_slug, is_deleted=False)
            except Tenant.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Mağaza bulunamadı: {tenant_slug}',
                }, status=status.HTTP_404_NOT_FOUND)
        elif tenant_id:
            try:
                from apps.models import Tenant
                tenant = Tenant.objects.get(id=tenant_id, is_deleted=False)
            except Tenant.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Mağaza bulunamadı: {tenant_id}',
                }, status=status.HTTP_404_NOT_FOUND)
    
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı. Lütfen tenant_slug veya tenant_id parametresi gönderin.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Aktif para birimlerini getir
    currencies = Currency.objects.filter(
        tenant=tenant,
        is_active=True,
        is_deleted=False
    ).order_by('-is_default', 'code')
    
    serializer = CurrencySerializer(currencies, many=True)
    
    return Response({
        'success': True,
        'currencies': serializer.data,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def currency_exchange_rates(request):
    """
    TCMB'den güncel döviz kurlarını getir.
    
    GET: /api/public/currency/exchange-rates/
    """
    try:
        rates = CurrencyService.get_tcmb_exchange_rates()
        return Response({
            'success': True,
            'rates': rates,
            'source': 'TCMB',
        })
    except Exception as e:
        logger.error(f"Error fetching TCMB exchange rates: {e}")
        return Response({
            'success': False,
            'message': 'Döviz kurları alınamadı.',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def currency_update_rates(request):
    """
    Tenant'ın para birimlerinin exchange_rate değerlerini TCMB'den güncelle.
    
    POST: /api/currency/update-rates/
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
    
    try:
        CurrencyService.update_currency_exchange_rates(tenant)
        return Response({
            'success': True,
            'message': 'Para birimi kurları güncellendi.',
        })
    except Exception as e:
        logger.error(f"Error updating currency rates: {e}")
        return Response({
            'success': False,
            'message': 'Para birimi kurları güncellenemedi.',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

