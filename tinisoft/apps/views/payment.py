"""
Payment views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.http import HttpResponse
from django.db import connection
from django.conf import settings
from apps.models import Payment, Order, Tenant, IntegrationProvider
from apps.serializers.payment import PaymentSerializer, CreatePaymentSerializer
from apps.services.payment_service import PaymentService
from apps.services.payment_providers import PaymentProviderFactory
from apps.permissions import IsTenantOwnerOfObject
from core.middleware import get_tenant_from_request
from core.db_router import set_tenant_schema, clear_tenant_schema
import logging

logger = logging.getLogger(__name__)


def force_tenant_schema_from_order_number(order_number: str):
    """
    MerchantOrderId'den tenant'ı bul ve schema'yı set et.
    Order number formatı: ORD-{TENANT_SLUG}-{timestamp}-{random}
    
    Bank callback'lerinde tenant header gelmez, bu nedenle order number'dan
    tenant bilgisini çıkarıp manuel olarak schema set etmemiz gerekir.
    """
    try:
        parts = (order_number or "").split("-")
        if len(parts) < 3 or parts[0].upper() != "ORD":
            logger.warning(f"Invalid order number format: {order_number}")
            return None
        slug = parts[1].lower()
    except Exception as e:
        logger.error(f"Error parsing order number: {str(e)}")
        return None
    
    # Slug ile tenant bul
    tenant = Tenant.objects.filter(slug__iexact=slug, is_deleted=False).first()
    if not tenant:
        # Subdomain ile de dene
        tenant = Tenant.objects.filter(subdomain__iexact=slug, is_deleted=False).first()
    if not tenant:
        logger.warning(f"Tenant not found for slug: {slug}")
        return None
    
    # Schema'yı set et
    schema = f"tenant_{tenant.subdomain}"
    set_tenant_schema(schema)
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{schema}", public;')
    
    logger.info(f"Tenant schema set to {schema} from order number {order_number}")
    return tenant


def html_redirect(url: str, message: str = "Yönlendiriliyorsunuz..."):
    """
    Tarayıcıya HTML redirect döndür.
    Bank POST callback'lerinde JSON döndürmek yerine HTML redirect döndürmek gerekir,
    çünkü kullanıcı tarayıcısı bankadan POST ile gelir.
    """
    return HttpResponse(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8"/>
            <meta http-equiv="refresh" content="0;url={url}" />
            <title>{message}</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding-top: 50px; }}
                .spinner {{ border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            </style>
        </head>
        <body>
            <div class="spinner"></div>
            <p>{message}</p>
            <script>window.location.href = "{url}";</script>
        </body>
        </html>
        """,
        content_type="text/html"
    )


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
    
    # Provider name mapping (payment provider name -> integration provider_type)
    provider_name_mapping = {
        'kuwait': 'kuveyt',
        'kuveyt': 'kuveyt',
        'iyzico': 'iyzico',
        'paytr': 'paytr',
        'vakif': 'vakif',
        'garanti': 'garanti',
        'akbank': 'akbank',
    }
    integration_provider_type = provider_name_mapping.get(provider_name.lower(), provider_name.lower())
    
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
                provider_type=integration_provider_type,
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
                    'payment_url': result.get('payment_url'),
                    'payment_html': result.get('payment_html'),  # Kuveyt için HTML dönebilir
                }
            )
            
            # Transaction ID'yi kaydet
            payment.transaction_id = result['transaction_id']
            payment.save()
            
            response_data = {
                'success': True,
                'message': 'Ödeme oluşturuldu.',
                'payment': PaymentSerializer(payment).data,
                'transaction_id': result['transaction_id'],
            }
            
            # Kuveyt gibi HTML dönen provider'lar için
            if result.get('payment_html'):
                response_data['payment_html'] = result['payment_html']
            elif result.get('payment_url'):
                response_data['payment_url'] = result['payment_url']
            
            return Response(response_data, status=status.HTTP_201_CREATED)
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


@api_view(['POST'])
@permission_classes([AllowAny])  # Kuveyt'ten POST gelecek
def kuveyt_callback_ok(request):
    """
    Kuveyt 3D Secure OkUrl callback (başarılı kart doğrulama).
    Banka bu endpoint'e POST ile AuthenticationResponse gönderir.
    
    Flow:
    1. AuthenticationResponse'u parse et
    2. MerchantOrderId'den tenant schema'yı set et
    3. MD ile ProvisionGate'e Request2 gönder
    4. Ödeme durumunu güncelle
    5. Frontend'e HTML redirect yap
    
    POST: /api/payments/kuveyt/callback/ok/
    """
    import xml.etree.ElementTree as ET
    from urllib.parse import unquote
    
    # Frontend URL (redirect için)
    frontend_url = getattr(settings, 'STORE_FRONTEND_URL', None) or getattr(settings, 'FRONTEND_URL', 'https://avrupamutfak.com')
    
    try:
        # AuthenticationResponse alanını al (UrlEncoded gelir)
        authentication_response = request.POST.get('AuthenticationResponse')
        if not authentication_response:
            logger.error("Kuveyt callback: AuthenticationResponse eksik")
            return html_redirect(f"{frontend_url}/checkout/fail?error=AuthenticationResponse+eksik", "Ödeme başarısız")
        
        # UrlDecode et
        decoded_xml = unquote(authentication_response)
        logger.info(f"Kuveyt callback OK - Decoded XML (first 500 chars): {decoded_xml[:500]}")
        
        # XML parse et
        try:
            root = ET.fromstring(decoded_xml)
        except ET.ParseError as e:
            logger.error(f"Kuveyt callback XML parse error: {str(e)}")
            return html_redirect(f"{frontend_url}/checkout/fail?error=XML+parse+hatasi", "Ödeme başarısız")
        
        # Farklı XML yapılarını dene
        # TDV2.0.0'da VERes veya direkt root'ta olabilir
        merchant_order_id = None
        md = None
        response_code = None
        
        # Önce VERes yapısını dene
        veres = root.find('.//VERes')
        if veres is not None:
            merchant_order_id = veres.findtext('MerchantOrderId')
            md = veres.findtext('MD')
            response_code = veres.findtext('Status')
        
        # Eğer bulunamadıysa direkt root'ta ara
        if not merchant_order_id:
            merchant_order_id = root.findtext('MerchantOrderId')
        if not md:
            md = root.findtext('MD')
        if not response_code:
            response_code = root.findtext('ResponseCode') or root.findtext('Status')
        
        logger.info(f"Kuveyt callback parsed: MerchantOrderId={merchant_order_id}, ResponseCode={response_code}, MD exists={bool(md)}")
        
        if not merchant_order_id:
            logger.error("Kuveyt callback: MerchantOrderId bulunamadı")
            return html_redirect(f"{frontend_url}/checkout/fail?error=MerchantOrderId+bulunamadi", "Ödeme başarısız")
        
        # Tenant schema'yı MerchantOrderId'den set et
        tenant = force_tenant_schema_from_order_number(merchant_order_id)
        if not tenant:
            logger.error(f"Kuveyt callback: Tenant bulunamadı for order {merchant_order_id}")
            return html_redirect(f"{frontend_url}/checkout/fail?error=Tenant+bulunamadi", "Ödeme başarısız")
        
        # Kart doğrulama başarılı mı? (Status=Y veya ResponseCode'a göre)
        is_verified = response_code in ('Y', '00', 'Approved')
        
        if not is_verified or not md:
            logger.error(f"Kuveyt callback: Kart doğrulanamadı. ResponseCode={response_code}, MD exists={bool(md)}")
            # Payment'ı fail yap
            try:
                payment = Payment.objects.filter(
                    transaction_id=merchant_order_id,
                    tenant=tenant,
                    is_deleted=False
                ).first()
                if payment:
                    PaymentService.fail_payment(payment, f"Kart doğrulama başarısız: {response_code}")
            except Exception as e:
                logger.error(f"Failed to update payment status: {str(e)}")
            
            return html_redirect(
                f"{frontend_url}/checkout/fail?order={merchant_order_id}&error=Kart+dogrulama+basarisiz",
                "Kart doğrulama başarısız"
            )
        
        # Payment kaydını bul
        payment = Payment.objects.filter(
            transaction_id=merchant_order_id,
            tenant=tenant,
            is_deleted=False
        ).first()
        
        if not payment:
            logger.error(f"Kuveyt callback: Payment bulunamadı for {merchant_order_id}")
            return html_redirect(f"{frontend_url}/checkout/fail?error=Payment+bulunamadi", "Ödeme başarısız")
        
        # Order'ı al
        order = payment.order
        if not order:
            logger.error(f"Kuveyt callback: Order bulunamadı for payment {payment.id}")
            return html_redirect(f"{frontend_url}/checkout/fail?error=Order+bulunamadi", "Ödeme başarısız")
        
        # Provider config'i al
        try:
            integration = IntegrationProvider.objects.get(
                tenant=tenant,
                provider_type='kuveyt',
                status__in=[IntegrationProvider.Status.ACTIVE, IntegrationProvider.Status.TEST_MODE],
                is_deleted=False
            )
            config = integration.get_provider_config()
        except IntegrationProvider.DoesNotExist:
            logger.error(f"Kuveyt callback: Integration bulunamadı for tenant {tenant.id}")
            PaymentService.fail_payment(payment, "Kuveyt entegrasyonu bulunamadı")
            return html_redirect(f"{frontend_url}/checkout/fail?error=Entegrasyon+bulunamadi", "Ödeme başarısız")
        
        # Provider'ı oluştur ve ProvisionGate'e istek at
        provider = PaymentProviderFactory.get_provider(
            tenant=tenant,
            provider_name='kuveyt',
            config=config
        )
        
        logger.info(f"Kuveyt callback: Calling ProvisionGate for order {merchant_order_id}")
        provision_result = provider.provision_payment(
            merchant_order_id=merchant_order_id,
            amount=order.total,
            md=md
        )
        
        if provision_result['success']:
            # Ödeme başarılı - Payment'ı tamamla
            payment = PaymentService.process_payment(
                payment,
                transaction_id=merchant_order_id,
                payment_intent_id=provision_result.get('order_id')
            )
            
            logger.info(f"Kuveyt callback SUCCESS: Order {merchant_order_id} completed")
            
            return html_redirect(
                f"{frontend_url}/checkout/success?order={merchant_order_id}",
                "Ödeme başarılı"
            )
        else:
            # Ödeme başarısız - Payment'ı fail yap
            error_msg = provision_result.get('error', 'ProvisionGate hatası')
            PaymentService.fail_payment(
                payment,
                error_message=error_msg,
                error_code=provision_result.get('response_code', '')
            )
            
            logger.error(f"Kuveyt callback FAIL: Order {merchant_order_id} - {error_msg}")
            
            return html_redirect(
                f"{frontend_url}/checkout/fail?order={merchant_order_id}&error={error_msg[:50].replace(' ', '+')}",
                "Ödeme başarısız"
            )
    
    except Exception as e:
        logger.error(f"Kuveyt callback error: {str(e)}", exc_info=True)
        return html_redirect(
            f"{frontend_url}/checkout/fail?error=Sistem+hatasi",
            "Ödeme işlenirken hata oluştu"
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def kuveyt_callback_fail(request):
    """
    Kuveyt 3D Secure FailUrl callback (başarısız kart doğrulama).
    
    POST: /api/payments/kuveyt/callback/fail/
    """
    import xml.etree.ElementTree as ET
    from urllib.parse import unquote
    
    # Frontend URL (redirect için)
    frontend_url = getattr(settings, 'STORE_FRONTEND_URL', None) or getattr(settings, 'FRONTEND_URL', 'https://avrupamutfak.com')
    
    try:
        authentication_response = request.POST.get('AuthenticationResponse')
        error_message = 'Kart doğrulama başarısız'
        merchant_order_id = None
        
        if authentication_response:
            decoded_xml = unquote(authentication_response)
            logger.info(f"Kuveyt callback FAIL - Decoded XML (first 500 chars): {decoded_xml[:500]}")
            
            try:
                root = ET.fromstring(decoded_xml)
                
                # MerchantOrderId'yi bul
                veres = root.find('.//VERes')
                if veres is not None:
                    merchant_order_id = veres.findtext('MerchantOrderId')
                    error_message = veres.findtext('ErrorMessage') or veres.findtext('ResponseMessage') or error_message
                
                if not merchant_order_id:
                    merchant_order_id = root.findtext('MerchantOrderId')
                if error_message == 'Kart doğrulama başarısız':
                    error_message = root.findtext('ResponseMessage') or root.findtext('ErrorMessage') or error_message
                    
            except ET.ParseError:
                pass
        
        logger.warning(f"Kuveyt callback FAIL: MerchantOrderId={merchant_order_id}, Error={error_message}")
        
        # Tenant schema'yı set et ve payment'ı fail yap
        if merchant_order_id:
            tenant = force_tenant_schema_from_order_number(merchant_order_id)
            if tenant:
                try:
                    payment = Payment.objects.filter(
                        transaction_id=merchant_order_id,
                        tenant=tenant,
                        is_deleted=False
                    ).first()
                    if payment:
                        PaymentService.fail_payment(payment, error_message)
                except Exception as e:
                    logger.error(f"Failed to update payment status: {str(e)}")
        
        return html_redirect(
            f"{frontend_url}/checkout/fail?order={merchant_order_id or ''}&error={error_message[:50].replace(' ', '+')}",
            "Ödeme başarısız"
        )
    
    except Exception as e:
        logger.error(f"Kuveyt callback fail error: {str(e)}", exc_info=True)
        return html_redirect(
            f"{frontend_url}/checkout/fail?error=Sistem+hatasi",
            "Kart doğrulama başarısız"
        )

