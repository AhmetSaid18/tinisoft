"""
Payment views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from apps.models import Payment, Order
from apps.serializers.payment import PaymentSerializer, CreatePaymentSerializer
from apps.services.payment_service import PaymentService
from apps.services.payment_providers import PaymentProviderFactory
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


@api_view(['POST'])
@permission_classes([AllowAny])
def payment_create_with_provider(request):
    """
    Ödeme sağlayıcı ile ödeme oluştur (Kuveyt API vb.).
    
    POST: /api/payments/create/
    Body: {
        "order_id": "...",
        "provider": "kuwait",  # "kuwait", "iyzico", vb.
        "provider_config": {  # Tenant'a özel config (opsiyonel)
            "api_key": "...",
            "api_secret": "...",
            "endpoint": "..."
        },
        "customer_info": {
            "email": "...",
            "name": "...",
            "phone": "..."
        }
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    order_id = request.data.get('order_id')
    provider_name = request.data.get('provider', 'kuwait')
    provider_config = request.data.get('provider_config', {})
    customer_info = request.data.get('customer_info', {})
    
    if not order_id:
        return Response({
            'success': False,
            'message': 'Sipariş ID gereklidir.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        order = Order.objects.get(
            id=order_id,
            tenant=tenant,
            is_deleted=False,
        )
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Sipariş bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Müşteri bilgilerini doldur
    if not customer_info.get('email'):
        customer_info['email'] = order.customer_email
    if not customer_info.get('name'):
        customer_info['name'] = f"{order.customer_first_name} {order.customer_last_name}"
    if not customer_info.get('phone'):
        customer_info['phone'] = order.customer_phone
    
    # Integration'dan config al (eğer request'te config yoksa)
    if not provider_config:
        try:
            from apps.models import IntegrationProvider
            integration = IntegrationProvider.objects.get(
                tenant=tenant,
                provider_type=provider_name.lower(),
                status__in=[
                    IntegrationProvider.Status.ACTIVE,
                    IntegrationProvider.Status.TEST_MODE
                ],
                is_deleted=False
            )
            final_config = integration.get_provider_config()
        except IntegrationProvider.DoesNotExist:
            return Response({
                'success': False,
                'message': f'{provider_name} entegrasyonu bulunamadı veya aktif değil. Lütfen önce entegrasyonu yapılandırın.',
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        # Request'te config varsa onu kullan
        final_config = provider_config
    
    try:
        # Provider'ı oluştur
        provider = PaymentProviderFactory.get_provider(
            tenant=tenant,
            provider_name=provider_name,
            config=final_config
        )
        
        # Ödeme oluştur
        result = provider.create_payment(
            order=order,
            amount=order.total,
            customer_info=customer_info
        )
        
        if result['success']:
            # Payment kaydı oluştur
            payment = PaymentService.create_payment(
                order=order,
                method=Payment.PaymentMethod.CREDIT_CARD,  # Default, provider'a göre değişebilir
                amount=order.total,
                provider=provider_name,
                metadata={
                    'transaction_id': result['transaction_id'],
                    'payment_url': result['payment_url'],
                }
            )
            
            # Transaction ID'yi kaydet
            payment.transaction_id = result['transaction_id']
            payment.save()
            
            return Response({
                'success': True,
                'message': 'Ödeme oluşturuldu.',
                'payment': PaymentSerializer(payment).data,
                'payment_url': result['payment_url'],
                'transaction_id': result['transaction_id'],
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': result.get('error', 'Ödeme oluşturulamadı.'),
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except ValueError as e:
        return Response({
            'success': False,
            'message': str(e),
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Payment provider error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ödeme oluşturulurken bir hata oluştu.',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def payment_verify(request):
    """
    Ödeme doğrula (callback için).
    
    POST: /api/payments/verify/
    Body: {
        "transaction_id": "...",
        "provider": "kuwait"
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    transaction_id = request.data.get('transaction_id')
    provider_name = request.data.get('provider', 'kuwait')
    
    if not transaction_id:
        return Response({
            'success': False,
            'message': 'Transaction ID gereklidir.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Payment'ı bul
    try:
        payment = Payment.objects.get(
            transaction_id=transaction_id,
            tenant=tenant,
            is_deleted=False
        )
    except Payment.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Ödeme bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        # Provider'ı oluştur (config integration'dan otomatik alınır)
        provider = PaymentProviderFactory.get_provider(
            tenant=tenant,
            provider_name=provider_name,
            config=None  # None gönderilirse integration'dan otomatik alınır
        )
        
        # Ödeme doğrula
        result = provider.verify_payment(transaction_id)
        
        if result['success'] and result['status'] == 'completed':
            # Ödemeyi tamamla
            payment = PaymentService.process_payment(
                payment,
                transaction_id=transaction_id
            )
            
            return Response({
                'success': True,
                'message': 'Ödeme doğrulandı ve tamamlandı.',
                'payment': PaymentSerializer(payment).data,
            })
        else:
            # Ödemeyi başarısız olarak işaretle
            payment = PaymentService.fail_payment(
                payment,
                error_message=result.get('error', 'Ödeme doğrulanamadı.')
            )
            
            return Response({
                'success': False,
                'message': result.get('error', 'Ödeme doğrulanamadı.'),
                'payment': PaymentSerializer(payment).data,
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Payment verification error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ödeme doğrulanırken bir hata oluştu.',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

