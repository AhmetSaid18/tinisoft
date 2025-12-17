"""
Loyalty views - Sadakat puanları yönetimi.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.models import LoyaltyProgram, LoyaltyPoints, LoyaltyTransaction
from apps.serializers.loyalty import (
    LoyaltyProgramSerializer, LoyaltyPointsSerializer, LoyaltyTransactionSerializer
)
from apps.services.loyalty_service import LoyaltyService
from apps.permissions import IsTenantOwnerOfObject
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([IsAuthenticated])
def loyalty_program(request):
    """
    Sadakat programı yönetimi.
    
    GET: /api/loyalty/program/ - Program bilgilerini getir
    POST: /api/loyalty/program/ - Program oluştur
    PATCH: /api/loyalty/program/ - Program güncelle (aktif/deaktif dahil)
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
    
    if request.method == 'GET':
        try:
            program = LoyaltyProgram.objects.get(tenant=tenant)
            serializer = LoyaltyProgramSerializer(program)
            return Response({
                'success': True,
                'program': serializer.data,
            })
        except LoyaltyProgram.DoesNotExist:
            # Program yoksa varsayılan ayarlarla oluştur
            program = LoyaltyService.get_or_create_loyalty_program(tenant)
            serializer = LoyaltyProgramSerializer(program)
            return Response({
                'success': True,
                'message': 'Sadakat programı oluşturuldu.',
                'program': serializer.data,
            })
    
    elif request.method == 'POST':
        # Program oluştur
        serializer = LoyaltyProgramSerializer(data=request.data)
        if serializer.is_valid():
            program = serializer.save(tenant=tenant)
            return Response({
                'success': True,
                'message': 'Sadakat programı oluşturuldu.',
                'program': LoyaltyProgramSerializer(program).data,
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Program oluşturulamadı.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'PATCH':
        # Program güncelle (aktif/deaktif dahil)
        try:
            program = LoyaltyProgram.objects.get(tenant=tenant)
        except LoyaltyProgram.DoesNotExist:
            program = LoyaltyService.get_or_create_loyalty_program(tenant)
        
        serializer = LoyaltyProgramSerializer(
            program,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            
            # Aktif/deaktif durumunu logla
            is_active = request.data.get('is_active')
            if is_active is not None:
                status_text = 'aktif' if is_active else 'deaktif'
                logger.info(f"Loyalty program {status_text} edildi for tenant {tenant.name} by {request.user.email}")
            
            return Response({
                'success': True,
                'message': 'Sadakat programı güncellendi.',
                'program': serializer.data,
            })
        return Response({
            'success': False,
            'message': 'Program güncellenemedi.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_loyalty_points(request):
    """
    Müşterinin kendi puanlarını görüntüle.
    
    GET: /api/loyalty/my-points/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece TenantUser erişebilir
    if not (request.user.is_tenant_user and request.user.tenant == tenant):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        loyalty_points = LoyaltyPoints.objects.get(
            tenant=tenant,
            customer=request.user
        )
        serializer = LoyaltyPointsSerializer(loyalty_points)
        return Response({
            'success': True,
            'loyalty_points': serializer.data,
        })
    except LoyaltyPoints.DoesNotExist:
        # Puan yoksa oluştur
        loyalty_points = LoyaltyService.get_or_create_loyalty_points(tenant, request.user)
        serializer = LoyaltyPointsSerializer(loyalty_points)
        return Response({
            'success': True,
            'loyalty_points': serializer.data,
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loyalty_transactions(request):
    """
    Sadakat puanı işlem geçmişi.
    
    GET: /api/loyalty/transactions/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # TenantUser sadece kendi işlemlerini görebilir
    # TenantOwner tüm işlemleri görebilir
    if request.user.is_tenant_user and request.user.tenant == tenant:
        # Müşteri - sadece kendi işlemleri
        try:
            loyalty_points = LoyaltyPoints.objects.get(
                tenant=tenant,
                customer=request.user
            )
            transactions = LoyaltyTransaction.objects.filter(
                loyalty_points=loyalty_points
            ).order_by('-created_at')
        except LoyaltyPoints.DoesNotExist:
            transactions = LoyaltyTransaction.objects.none()
    elif request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant):
        # Owner/TenantOwner - tüm işlemler
        transactions = LoyaltyTransaction.objects.filter(
            loyalty_points__tenant=tenant
        ).order_by('-created_at')
    else:
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = LoyaltyTransactionSerializer(transactions, many=True)
    return Response({
        'success': True,
        'transactions': serializer.data,
    })

