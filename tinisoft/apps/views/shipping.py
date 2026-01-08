"""
Shipping views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from decimal import Decimal
from apps.models import ShippingMethod, ShippingAddress, ShippingZone, ShippingZoneRate
from apps.serializers.shipping import (
    ShippingMethodSerializer, ShippingAddressSerializer,
    ShippingZoneSerializer, ShippingZoneRateSerializer,
    ShippingCalculateSerializer
)
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def shipping_method_list_create(request):
    """
    Kargo yöntemi listesi (GET) veya yeni yöntem oluştur (POST).
    
    GET: /api/shipping/methods/
    POST: /api/shipping/methods/
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
        queryset = ShippingMethod.objects.filter(tenant=tenant, is_deleted=False)
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        queryset = queryset.order_by('name')
        
        serializer = ShippingMethodSerializer(queryset, many=True)
        return Response({
            'success': True,
            'shipping_methods': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = ShippingMethodSerializer(data=request.data)
        
        if serializer.is_valid():
            shipping_method = serializer.save(tenant=tenant)
            
            return Response({
                'success': True,
                'message': 'Kargo yöntemi oluşturuldu.',
                'shipping_method': ShippingMethodSerializer(shipping_method).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def shipping_method_detail(request, method_id):
    """
    Kargo yöntemi detayı (GET), güncelle (PATCH) veya sil (DELETE).
    
    GET: /api/shipping/methods/{method_id}/
    PATCH: /api/shipping/methods/{method_id}/
    DELETE: /api/shipping/methods/{method_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        shipping_method = ShippingMethod.objects.get(id=method_id, tenant=tenant, is_deleted=False)
    except ShippingMethod.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Kargo yöntemi bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ShippingMethodSerializer(shipping_method)
        return Response({
            'success': True,
            'shipping_method': serializer.data,
        })
    
    elif request.method == 'PATCH':
        # Sadece admin veya tenant owner
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ShippingMethodSerializer(shipping_method, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Kargo yöntemi güncellendi.',
                'shipping_method': ShippingMethodSerializer(shipping_method).data,
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
        
        shipping_method.soft_delete()
        return Response({
            'success': True,
            'message': 'Kargo yöntemi silindi.',
        }, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def shipping_address_list_create(request):
    """
    Kargo adresi listesi (GET) veya yeni adres oluştur (POST).
    
    GET: /api/shipping/addresses/
    POST: /api/shipping/addresses/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece tenant user'lar kendi adreslerini görebilir
    if not request.user.is_tenant_user or request.user.tenant != tenant:
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        queryset = ShippingAddress.objects.filter(
            tenant=tenant,
            user=request.user,
            is_deleted=False
        )
        
        # Adres tipine göre filtreleme (opsiyonel)
        address_type = request.query_params.get('type')  # billing veya shipping
        if address_type:
            queryset = queryset.filter(address_type=address_type)
        
        queryset = queryset.order_by('-is_default', '-created_at')
        
        serializer = ShippingAddressSerializer(queryset, many=True)
        return Response({
            'success': True,
            'shipping_addresses': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = ShippingAddressSerializer(data=request.data)
        
        if serializer.is_valid():
            # Eğer is_default=True ise, AYNI TİPTEKİ diğer adresleri is_default=False yap
            if serializer.validated_data.get('is_default', False):
                # Hangi tipte kaydediliyorsa o tiptekileri güncelle
                addr_type = serializer.validated_data.get('address_type', 'shipping')
                ShippingAddress.objects.filter(
                    tenant=tenant,
                    user=request.user,
                    address_type=addr_type,
                    is_default=True
                ).update(is_default=False)
            
            shipping_address = serializer.save(tenant=tenant, user=request.user)
            
            return Response({
                'success': True,
                'message': 'Kargo adresi oluşturuldu.',
                'shipping_address': ShippingAddressSerializer(shipping_address).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def shipping_address_detail(request, address_id):
    """
    Kargo adresi detayı (GET), güncelle (PATCH) veya sil (DELETE).
    
    GET: /api/shipping/addresses/{address_id}/
    PATCH: /api/shipping/addresses/{address_id}/
    DELETE: /api/shipping/addresses/{address_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        shipping_address = ShippingAddress.objects.get(id=address_id, tenant=tenant, is_deleted=False)
    except ShippingAddress.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Kargo adresi bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece sahibi erişebilir
    if shipping_address.user != request.user:
        return Response({
            'success': False,
            'message': 'Bu adrese erişim yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = ShippingAddressSerializer(shipping_address)
        return Response({
            'success': True,
            'shipping_address': serializer.data,
        })
    
    elif request.method == 'PATCH':
        serializer = ShippingAddressSerializer(shipping_address, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Eğer is_default=True yapılıyorsa, AYNI TİPTEKİ diğer adresleri is_default=False yap
            if serializer.validated_data.get('is_default', False):
                # Eğer tip değişiyorsa yeni tipi al, yoksa mevcut tipi kullan
                addr_type = serializer.validated_data.get('address_type', shipping_address.address_type)
                
                ShippingAddress.objects.filter(
                    tenant=tenant,
                    user=request.user,
                    address_type=addr_type,
                    is_default=True
                ).exclude(id=shipping_address.id).update(is_default=False)
            
            serializer.save()
            return Response({
                'success': True,
                'message': 'Kargo adresi güncellendi.',
                'shipping_address': ShippingAddressSerializer(shipping_address).data,
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        shipping_address.soft_delete()
        return Response({
            'success': True,
            'message': 'Kargo adresi silindi.',
        }, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def shipping_zone_list_create(request):
    """
    Kargo bölgesi listesi (GET) veya yeni bölge oluştur (POST).
    
    GET: /api/shipping/zones/
    POST: /api/shipping/zones/
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
        queryset = ShippingZone.objects.filter(tenant=tenant, is_deleted=False)
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        queryset = queryset.order_by('name')
        
        serializer = ShippingZoneSerializer(queryset, many=True, context={'request': request})
        return Response({
            'success': True,
            'shipping_zones': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = ShippingZoneSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            shipping_zone = serializer.save(tenant=tenant)
            
            return Response({
                'success': True,
                'message': 'Kargo bölgesi oluşturuldu.',
                'shipping_zone': ShippingZoneSerializer(shipping_zone, context={'request': request}).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def shipping_calculate(request):
    """
    Kargo ücreti hesapla.
    
    POST: /api/shipping/calculate/
    Body: {
        "shipping_method_id": "...",
        "country": "TR",
        "city": "Istanbul",
        "postal_code": "34000",
        "order_amount": 100.00,
        "total_weight": 1.5
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = ShippingCalculateSerializer(data=request.data)
    
    if serializer.is_valid():
        shipping_method_id = serializer.validated_data['shipping_method_id']
        country = serializer.validated_data['country']
        city = serializer.validated_data.get('city')
        postal_code = serializer.validated_data.get('postal_code')
        order_amount = Decimal(str(serializer.validated_data.get('order_amount', 0.00)))
        total_weight = Decimal(str(serializer.validated_data.get('total_weight', 0.00)))
        
        # Shipping method'u bul
        try:
            shipping_method = ShippingMethod.objects.get(
                id=shipping_method_id,
                tenant=tenant,
                is_active=True,
                is_deleted=False
            )
        except ShippingMethod.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Kargo yöntemi bulunamadı.',
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Shipping zone'u bul
        shipping_zone = None
        zones = ShippingZone.objects.filter(tenant=tenant, is_active=True, is_deleted=False)
        for zone in zones:
            if zone.matches(country, city, postal_code):
                shipping_zone = zone
                break
        
        # Zone rate'i bul
        shipping_cost = shipping_method.price  # Default price
        
        if shipping_zone:
            try:
                zone_rate = ShippingZoneRate.objects.get(
                    zone=shipping_zone,
                    shipping_method=shipping_method,
                    is_active=True,
                    is_deleted=False
                )
                shipping_cost = zone_rate.calculate_shipping_cost(order_amount, total_weight)
            except ShippingZoneRate.DoesNotExist:
                # Zone rate yoksa, shipping method'un default price'ını kullan
                pass
        
        # Free shipping kontrolü
        if shipping_method.free_shipping_threshold and order_amount >= shipping_method.free_shipping_threshold:
            shipping_cost = Decimal('0.00')
        
        return Response({
            'success': True,
            'shipping_cost': str(shipping_cost),
            'shipping_method': {
                'id': str(shipping_method.id),
                'name': shipping_method.name,
                'code': shipping_method.code,
            },
            'shipping_zone': {
                'id': str(shipping_zone.id) if shipping_zone else None,
                'name': shipping_zone.name if shipping_zone else None,
            } if shipping_zone else None,
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'errors': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def shipping_zone_detail(request, zone_id):
    """
    Shipping zone detayı (GET), güncelle (PATCH) veya sil (DELETE).
    
    GET: /api/shipping/zones/<zone_id>/
    PATCH: /api/shipping/zones/<zone_id>/
    DELETE: /api/shipping/zones/<zone_id>/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        shipping_zone = ShippingZone.objects.get(tenant=tenant, id=zone_id, is_deleted=False)
    except ShippingZone.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Shipping zone bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = ShippingZoneSerializer(shipping_zone)
        return Response({
            'success': True,
            'shipping_zone': serializer.data,
        })
    
    elif request.method == 'PATCH':
        serializer = ShippingZoneSerializer(shipping_zone, data=request.data, partial=True)
        
        if serializer.is_valid():
            shipping_zone = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Shipping zone güncellendi.',
                'shipping_zone': ShippingZoneSerializer(shipping_zone).data,
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        shipping_zone.is_deleted = True
        shipping_zone.save()
        
        return Response({
            'success': True,
            'message': 'Shipping zone silindi.',
        }, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def shipping_zone_rate_list_create(request, zone_id):
    """
    Shipping zone rate listesi (GET) veya yeni rate oluştur (POST).
    
    GET: /api/shipping/zones/<zone_id>/rates/
    POST: /api/shipping/zones/<zone_id>/rates/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        shipping_zone = ShippingZone.objects.get(tenant=tenant, id=zone_id, is_deleted=False)
    except ShippingZone.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Shipping zone bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        queryset = ShippingZoneRate.objects.filter(zone=shipping_zone, is_deleted=False)
        
        serializer = ShippingZoneRateSerializer(queryset, many=True)
        return Response({
            'success': True,
            'rates': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = ShippingZoneRateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            rate = serializer.save(zone=shipping_zone)
            
            return Response({
                'success': True,
                'message': 'Shipping zone rate oluşturuldu.',
                'rate': ShippingZoneRateSerializer(rate, context={'request': request}).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def shipping_zone_rate_detail(request, zone_id, rate_id):
    """
    Shipping zone rate detayı (GET), güncelle (PATCH) veya sil (DELETE).
    
    GET: /api/shipping/zones/<zone_id>/rates/<rate_id>/
    PATCH: /api/shipping/zones/<zone_id>/rates/<rate_id>/
    DELETE: /api/shipping/zones/<zone_id>/rates/<rate_id>/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        shipping_zone = ShippingZone.objects.get(tenant=tenant, id=zone_id, is_deleted=False)
        zone_rate = ShippingZoneRate.objects.get(zone=shipping_zone, id=rate_id, is_deleted=False)
    except (ShippingZone.DoesNotExist, ShippingZoneRate.DoesNotExist):
        return Response({
            'success': False,
            'message': 'Shipping zone veya rate bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = ShippingZoneRateSerializer(zone_rate, context={'request': request})
        return Response({
            'success': True,
            'rate': serializer.data,
        })
    
    elif request.method == 'PATCH':
        serializer = ShippingZoneRateSerializer(zone_rate, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            zone_rate = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Shipping zone rate güncellendi.',
                'rate': ShippingZoneRateSerializer(zone_rate, context={'request': request}).data,
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        zone_rate.is_deleted = True
        zone_rate.save()
        
        return Response({
            'success': True,
            'message': 'Shipping zone rate silindi.',
        }, status=status.HTTP_200_OK)

