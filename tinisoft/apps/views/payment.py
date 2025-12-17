"""
Payment views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.models import Payment, Order
from apps.serializers.payment import PaymentSerializer, CreatePaymentSerializer
from apps.services.payment_service import PaymentService
from apps.permissions import IsTenantOwnerOfObject
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def payment_list_create(request):
    """
    Ödeme listesi (GET) veya yeni ödeme oluştur (POST).
    
    GET: /api/payments/
    POST: /api/payments/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        # Permission kontrolü
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        queryset = Payment.objects.filter(tenant=tenant, is_deleted=False)
        
        # Sipariş filtresi
        order_id = request.query_params.get('order_id')
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        
        # Status filtresi
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        queryset = queryset.order_by('-created_at')
        
        serializer = PaymentSerializer(queryset, many=True)
        return Response({
            'success': True,
            'payments': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = CreatePaymentSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            try:
                order = Order.objects.get(
                    id=data['order_id'],
                    tenant=tenant,
                    is_deleted=False,
                )
            except Order.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Sipariş bulunamadı.',
                }, status=status.HTTP_404_NOT_FOUND)
            
            try:
                payment = PaymentService.create_payment(
                    order=order,
                    method=data['method'],
                    amount=data['amount'],
                    provider=data.get('provider'),
                )
                
                return Response({
                    'success': True,
                    'message': 'Ödeme oluşturuldu.',
                    'payment': PaymentSerializer(payment).data,
                }, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e),
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'message': 'Ödeme oluşturulamadı.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def payment_detail(request, payment_id):
    """
    Ödeme detayı (GET) veya güncelleme (PATCH).
    
    GET: /api/payments/{payment_id}/
    PATCH: /api/payments/{payment_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        payment = Payment.objects.get(id=payment_id, tenant=tenant, is_deleted=False)
    except Payment.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Ödeme bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Permission kontrolü
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = PaymentSerializer(payment)
        return Response({
            'success': True,
            'payment': serializer.data,
        })
    
    elif request.method == 'PATCH':
        action = request.data.get('action')
        
        if action == 'process':
            # Ödemeyi işle
            transaction_id = request.data.get('transaction_id')
            payment_intent_id = request.data.get('payment_intent_id')
            try:
                payment = PaymentService.process_payment(payment, transaction_id, payment_intent_id)
                return Response({
                    'success': True,
                    'message': 'Ödeme işlendi.',
                    'payment': PaymentSerializer(payment).data,
                })
            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e),
                }, status=status.HTTP_400_BAD_REQUEST)
        
        elif action == 'fail':
            # Ödemeyi başarısız olarak işaretle
            error_message = request.data.get('error_message', '')
            error_code = request.data.get('error_code', '')
            payment = PaymentService.fail_payment(payment, error_message, error_code)
            return Response({
                'success': True,
                'message': 'Ödeme başarısız olarak işaretlendi.',
                'payment': PaymentSerializer(payment).data,
            })
        
        elif action == 'refund':
            # Ödemeyi iade et
            amount = request.data.get('amount')
            try:
                payment = PaymentService.refund_payment(payment, amount)
                return Response({
                    'success': True,
                    'message': 'Ödeme iade edildi.',
                    'payment': PaymentSerializer(payment).data,
                })
            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e),
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'message': 'Geçersiz action.',
        }, status=status.HTTP_400_BAD_REQUEST)

