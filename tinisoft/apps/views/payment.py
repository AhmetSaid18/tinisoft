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


def extract_tenant_slug_from_order_number(order_number: str):
    """
    Order number'dan tenant slug'ını çıkar.
    Order number formatı: ORD-{TENANT_SLUG}-{timestamp}-{random}
    
    Returns:
        str: Tenant slug veya None
    """
    try:
        parts = (order_number or "").split("-")
        if len(parts) < 3 or parts[0].upper() != "ORD":
            return None
        return parts[1].lower()
    except Exception:
        return None


def get_tenant_frontend_url(tenant=None, tenant_slug=None):
    """
    Tenant'ın frontend URL'ini al.
    Tenant'ın get_primary_frontend_url() metodunu kullanır.
    
    Öncelik sırası (Tenant.get_primary_frontend_url() içinde):
    1. Tenant'ın custom_domain field'ı (doğrulama gerektirmez)
    2. Primary domain (Domain modelinden, doğrulama gerektirmez)
    3. Herhangi bir domain
    4. Fallback: subdomain URL
    
    Args:
        tenant: Tenant instance (opsiyonel)
        tenant_slug: Tenant slug (opsiyonel, tenant yoksa kullanılır)
    
    Returns:
        str: Frontend URL (örn: https://avrupamutfak.com veya https://avrupamutfak.tinisoft.com.tr)
    """
    from core.db_router import clear_tenant_schema
    
    # Tenant varsa direkt get_primary_frontend_url() kullan
    if tenant:
        try:
            url = tenant.get_primary_frontend_url()
            logger.info(f"Using frontend URL: {url} for tenant {tenant.slug}")
            return url
        except Exception as e:
            logger.warning(f"Error getting frontend URL for tenant {tenant.id}: {str(e)}")
            # Fallback: Tenant slug'dan subdomain URL oluştur
            if tenant.slug:
                return f"https://{tenant.slug}.tinisoft.com.tr"
            elif tenant.subdomain:
                return f"https://{tenant.subdomain}.tinisoft.com.tr"
    
    # Tenant yoksa slug'dan tenant bul ve URL al
    if tenant_slug:
        try:
            # Public schema'da bu slug'a ait tenant'ı bul
            clear_tenant_schema()
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO public;')
            
            tenant_obj = Tenant.objects.filter(
                slug__iexact=tenant_slug,
                is_deleted=False
            ).first()
            
            if tenant_obj:
                url = tenant_obj.get_primary_frontend_url()
                logger.info(f"Using frontend URL: {url} for tenant slug {tenant_slug}")
                return url
        except Exception as e:
            logger.warning(f"Error getting frontend URL for tenant slug {tenant_slug}: {str(e)}")
        
        # Fallback: Slug'dan subdomain URL oluştur
        logger.info(f"Using fallback subdomain URL for tenant slug {tenant_slug}")
        return f"https://{tenant_slug}.tinisoft.com.tr"
    
    # Son fallback: API base URL'den domain çıkar
    api_base_url = getattr(settings, 'API_BASE_URL', 'https://api.tinisoft.com.tr')
    # api.tinisoft.com.tr -> tinisoft.com.tr
    if 'api.' in api_base_url:
        base_domain = api_base_url.replace('api.', '')
        return base_domain
    
    return 'https://tinisoft.com.tr'  # En son fallback


def force_tenant_schema_from_order_number(order_number: str):
    """
    MerchantOrderId'den tenant'ı bul ve schema'yı set et.
    Order number formatı: ORD-{TENANT_SLUG}-{timestamp}-{random}
    
    Bank callback'lerinde tenant header gelmez, bu nedenle order number'dan
    tenant bilgisini çıkarıp manuel olarak schema set etmemiz gerekir.
    """
    from core.db_router import clear_tenant_schema
    
    tenant_slug = extract_tenant_slug_from_order_number(order_number)
    if not tenant_slug:
        logger.warning(f"Invalid order number format: {order_number}")
        return None
    
    # Tenant public schema'da, önce public schema'ya geç
    clear_tenant_schema()
    with connection.cursor() as cursor:
        cursor.execute('SET search_path TO public;')
    
    # Slug ile tenant bul (public schema'da)
    tenant = Tenant.objects.filter(slug__iexact=tenant_slug, is_deleted=False).first()
    if not tenant:
        # Subdomain ile de dene
        tenant = Tenant.objects.filter(subdomain__iexact=tenant_slug, is_deleted=False).first()
    if not tenant:
        logger.warning(f"Tenant not found for slug: {tenant_slug}")
        return None
    
    # Schema'yı set et (tenant-specific schema'ya geç)
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
    
    try:
        # AuthenticationResponse alanını al (UrlEncoded gelir)
        authentication_response = request.POST.get('AuthenticationResponse')
        if not authentication_response:
            logger.error("Kuveyt callback: AuthenticationResponse eksik")
            # Backend'in kendi endpoint'ine redirect yap
            api_base_url = getattr(settings, 'API_BASE_URL', 'https://api.tinisoft.com.tr')
            if not api_base_url.startswith('http'):
                api_base_url = f'https://{api_base_url}'
            callback_url = f"{api_base_url}/api/payments/callback-handler?status=fail&error=AuthenticationResponse+eksik"
            return html_redirect(callback_url, "Ödeme işleniyor...")
        
        # UrlDecode et - unquote_plus kullan çünkü + karakterleri boşluğa çevrilmeli
        # Önce + karakterlerini boşluğa çevir, sonra unquote yap
        decoded_xml = unquote(authentication_response.replace('+', ' '))
        logger.info(f"Kuveyt callback OK - Decoded XML (first 500 chars): {decoded_xml[:500]}")
        
        # XML parse et
        try:
            root = ET.fromstring(decoded_xml)
        except ET.ParseError as e:
            logger.error(f"Kuveyt callback XML parse error: {str(e)}")
            # Backend'in kendi endpoint'ine redirect yap
            api_base_url = getattr(settings, 'API_BASE_URL', 'https://api.tinisoft.com.tr')
            if not api_base_url.startswith('http'):
                api_base_url = f'https://{api_base_url}'
            callback_url = f"{api_base_url}/api/payments/callback-handler?status=fail&error=XML+parse+hatasi"
            return html_redirect(callback_url, "Ödeme işleniyor...")
        
        # Farklı XML yapılarını dene
        # TDV2.0.0'da AuthenticationResponse XML formatı:
        # - VPosTransactionResponseContract (root)
        #   - MerchantOrderId
        #   - MD
        #   - ResponseCode
        #   - ResponseMessage
        #   - IsEnrolled (true/false)
        merchant_order_id = None
        md = None
        response_code = None
        is_enrolled = None
        
        # Önce VPosTransactionResponseContract yapısını dene (TDV2.0.0 formatı)
        vpos_response = root.find('VPosTransactionResponseContract')
        if vpos_response is not None:
            merchant_order_id = vpos_response.findtext('MerchantOrderId')
            md = vpos_response.findtext('MD')
            response_code = vpos_response.findtext('ResponseCode')
            is_enrolled = vpos_response.findtext('IsEnrolled')
        
        # Eğer bulunamadıysa VERes yapısını dene (eski format)
        if not merchant_order_id:
            veres = root.find('.//VERes')
            if veres is not None:
                merchant_order_id = veres.findtext('MerchantOrderId')
                if not md:
                    md = veres.findtext('MD')
                if not response_code:
                    response_code = veres.findtext('Status')
        
        # Eğer hala bulunamadıysa direkt root'ta ara
        if not merchant_order_id:
            merchant_order_id = root.findtext('MerchantOrderId')
        if not md:
            md = root.findtext('MD')
        if not response_code:
            response_code = root.findtext('ResponseCode') or root.findtext('Status')
        if not is_enrolled:
            is_enrolled = root.findtext('IsEnrolled')
        
        logger.info(f"Kuveyt callback parsed: MerchantOrderId={merchant_order_id}, ResponseCode={response_code}, MD exists={bool(md)}, IsEnrolled={is_enrolled}")
        
        if not merchant_order_id:
            logger.error("Kuveyt callback: MerchantOrderId bulunamadı")
            logger.error(f"XML content (first 1000 chars): {decoded_xml[:1000]}")
            # Backend'in kendi endpoint'ine redirect yap
            api_base_url = getattr(settings, 'API_BASE_URL', 'https://api.tinisoft.com.tr')
            if not api_base_url.startswith('http'):
                api_base_url = f'https://{api_base_url}'
            callback_url = f"{api_base_url}/api/payments/callback-handler?status=fail&error=MerchantOrderId+bulunamadi"
            return html_redirect(callback_url, "Ödeme işleniyor...")
        
        # Tenant schema'yı MerchantOrderId'den set et
        tenant = force_tenant_schema_from_order_number(merchant_order_id)
        if not tenant:
            logger.error(f"Kuveyt callback: Tenant bulunamadı for order {merchant_order_id}")
            # Backend'in kendi endpoint'ine redirect yap
            api_base_url = getattr(settings, 'API_BASE_URL', 'https://api.tinisoft.com.tr')
            if not api_base_url.startswith('http'):
                api_base_url = f'https://{api_base_url}'
            callback_url = f"{api_base_url}/api/payments/callback-handler?order={merchant_order_id}&status=fail&error=Tenant+bulunamadi"
            return html_redirect(callback_url, "Ödeme işleniyor...")
        
        # Tenant'ın primary frontend URL'ini al (her tenant kendi domain'ine sahip)
        frontend_url = tenant.get_primary_frontend_url()
        logger.info(f"Kuveyt callback: Using tenant frontend URL: {frontend_url} for tenant {tenant.name}")
        
        # Kart doğrulama başarılı mı? (ResponseCode=00 veya IsEnrolled=true ve MD var)
        # TDV2.0.0'da ResponseCode kontrolü önemli
        is_verified = (
            response_code in ('00', '000', 'Y', 'Approved') or
            (is_enrolled == 'true' and md is not None)
        )
        
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
            
            # Backend'in kendi endpoint'ine redirect yap
            api_base_url = getattr(settings, 'API_BASE_URL', 'https://api.tinisoft.com.tr')
            if not api_base_url.startswith('http'):
                api_base_url = f'https://{api_base_url}'
            callback_url = f"{api_base_url}/api/payments/callback-handler?order={merchant_order_id}&status=fail&error=Kart+dogrulama+basarisiz"
            return html_redirect(callback_url, "Ödeme işleniyor...")
        
        # Payment kaydını bul
        payment = Payment.objects.filter(
            transaction_id=merchant_order_id,
            tenant=tenant,
            is_deleted=False
        ).first()
        
        if not payment:
            logger.error(f"Kuveyt callback: Payment bulunamadı for {merchant_order_id}")
            api_base_url = getattr(settings, 'API_BASE_URL', 'https://api.tinisoft.com.tr')
            if not api_base_url.startswith('http'):
                api_base_url = f'https://{api_base_url}'
            callback_url = f"{api_base_url}/api/payments/callback-handler?order={merchant_order_id}&status=fail&error=Payment+bulunamadi"
            return html_redirect(callback_url, "Ödeme işleniyor...")
        
        # Order'ı al
        order = payment.order
        if not order:
            logger.error(f"Kuveyt callback: Order bulunamadı for payment {payment.id}")
            api_base_url = getattr(settings, 'API_BASE_URL', 'https://api.tinisoft.com.tr')
            if not api_base_url.startswith('http'):
                api_base_url = f'https://{api_base_url}'
            callback_url = f"{api_base_url}/api/payments/callback-handler?order={merchant_order_id}&status=fail&error=Order+bulunamadi"
            return html_redirect(callback_url, "Ödeme işleniyor...")
        
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
            api_base_url = getattr(settings, 'API_BASE_URL', 'https://api.tinisoft.com.tr')
            if not api_base_url.startswith('http'):
                api_base_url = f'https://{api_base_url}'
            callback_url = f"{api_base_url}/api/payments/callback-handler?order={merchant_order_id}&status=fail&error=Entegrasyon+bulunamadi"
            return html_redirect(callback_url, "Ödeme işleniyor...")
        
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
        
        # Backend API base URL (kendi endpoint'ine redirect için)
        api_base_url = getattr(settings, 'API_BASE_URL', 'https://api.tinisoft.com.tr')
        if not api_base_url.startswith('http'):
            api_base_url = f'https://{api_base_url}'
        
        if provision_result['success']:
            # Ödeme başarılı - Payment'ı tamamla
            payment = PaymentService.process_payment(
                payment,
                transaction_id=merchant_order_id,
                payment_intent_id=provision_result.get('order_id')
            )
            
            logger.info(f"Kuveyt callback SUCCESS: Order {merchant_order_id} completed")
            
            # Backend'in kendi endpoint'ine redirect yap (frontend oradan durumu alacak)
            callback_url = f"{api_base_url}/api/payments/callback-handler?order={merchant_order_id}&status=success"
            return html_redirect(callback_url, "Ödeme işleniyor...")
        else:
            # Ödeme başarısız - Payment'ı fail yap
            error_msg = provision_result.get('error', 'ProvisionGate hatası')
            PaymentService.fail_payment(
                payment,
                error_message=error_msg,
                error_code=provision_result.get('response_code', '')
            )
            
            logger.error(f"Kuveyt callback FAIL: Order {merchant_order_id} - {error_msg}")
            
            # Backend'in kendi endpoint'ine redirect yap (frontend oradan durumu alacak)
            error_param = error_msg[:50].replace(' ', '+').replace('&', '%26')
            callback_url = f"{api_base_url}/api/payments/callback-handler?order={merchant_order_id}&status=fail&error={error_param}"
            return html_redirect(callback_url, "Ödeme işleniyor...")
    
    except Exception as e:
        logger.error(f"Kuveyt callback error: {str(e)}", exc_info=True)
        # Backend'in kendi endpoint'ine redirect yap
        api_base_url = getattr(settings, 'API_BASE_URL', 'https://api.tinisoft.com.tr')
        if not api_base_url.startswith('http'):
            api_base_url = f'https://{api_base_url}'
        callback_url = f"{api_base_url}/api/payments/callback-handler?status=fail&error=Sistem+hatasi"
        return html_redirect(callback_url, "Ödeme işleniyor...")


@api_view(['POST'])
@permission_classes([AllowAny])
def kuveyt_callback_fail(request):
    """
    Kuveyt 3D Secure FailUrl callback (başarısız kart doğrulama).
    
    POST: /api/payments/kuveyt/callback/fail/
    """
    import xml.etree.ElementTree as ET
    from urllib.parse import unquote
    
    try:
        authentication_response = request.POST.get('AuthenticationResponse')
        error_message = 'Kart doğrulama başarısız'
        merchant_order_id = None
        
        if authentication_response:
            # UrlDecode et - + karakterlerini boşluğa çevir
            decoded_xml = unquote(authentication_response.replace('+', ' '))
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
        frontend_url = None
        if merchant_order_id:
            tenant = force_tenant_schema_from_order_number(merchant_order_id)
            if tenant:
                # Tenant'ın primary frontend URL'ini al
                frontend_url = tenant.get_primary_frontend_url()
                logger.info(f"Kuveyt callback FAIL: Using tenant frontend URL: {frontend_url} for tenant {tenant.name}")
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
        
        # Backend'in kendi endpoint'ine redirect yap
        api_base_url = getattr(settings, 'API_BASE_URL', 'https://api.tinisoft.com.tr')
        if not api_base_url.startswith('http'):
            api_base_url = f'https://{api_base_url}'
        
        error_param = error_message[:50].replace(' ', '+').replace('&', '%26') if error_message else ''
        if merchant_order_id:
            callback_url = f"{api_base_url}/api/payments/callback-handler?order={merchant_order_id}&status=fail&error={error_param}"
        else:
            callback_url = f"{api_base_url}/api/payments/callback-handler?status=fail&error={error_param}"
        
        return html_redirect(callback_url, "Ödeme işleniyor...")
    
    except Exception as e:
        logger.error(f"Kuveyt callback fail error: {str(e)}", exc_info=True)
        # Backend'in kendi endpoint'ine redirect yap
        api_base_url = getattr(settings, 'API_BASE_URL', 'https://api.tinisoft.com.tr')
        if not api_base_url.startswith('http'):
            api_base_url = f'https://{api_base_url}'
        callback_url = f"{api_base_url}/api/payments/callback-handler?status=fail&error=Sistem+hatasi"
        return html_redirect(callback_url, "Ödeme işleniyor...")


@api_view(['GET'])
@permission_classes([AllowAny])  # Frontend'den erişilebilir olmalı
def payment_callback_handler(request):
    """
    Payment callback handler - Frontend bu endpoint'ten payment durumunu alır.
    
    Backend callback'lerden sonra bu endpoint'e redirect yapar.
    HTML döndürür ve JavaScript ile otomatik redirect yapar.
    JSON istenirse Accept: application/json header'ı ile JSON döndürür.
    
    GET: /api/payments/callback-handler?order={order_number}&status={success|fail}&error={error_message}
    
    Response (HTML - default):
    HTML sayfa + JavaScript redirect
    
    Response (JSON - Accept: application/json):
    {
        "success": bool,
        "order_number": str,
        "payment_status": str,  # "completed", "failed", "pending"
        "redirect_url": str,  # Frontend'in kendi redirect URL'i (opsiyonel)
        "error": str (if failed)
    }
    """
    order_number = request.query_params.get('order')
    status_param = request.query_params.get('status', 'fail')  # success veya fail
    error_message = request.query_params.get('error', '')
    
    if not order_number:
        error_data = {
            'success': False,
            'message': 'Order number gereklidir.',
            'error': 'Order number bulunamadı'
        }
        # JSON isteniyorsa JSON döndür
        if request.headers.get('Accept', '').startswith('application/json'):
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
        # HTML döndür - generic fallback URL
        fallback_url = get_tenant_frontend_url()
        return html_redirect(
            f'{fallback_url}/checkout/fail?error=Order+number+bulunamadi',
            "Ödeme işleniyor..."
        )
    
    # Tenant schema'yı order number'dan set et
    tenant = force_tenant_schema_from_order_number(order_number)
    tenant_slug = extract_tenant_slug_from_order_number(order_number)
    
    if not tenant:
        logger.warning(f"Payment callback handler: Tenant bulunamadı for order {order_number}")
        error_data = {
            'success': False,
            'order_number': order_number,
            'payment_status': 'failed',
            'error': 'Tenant bulunamadı',
            'redirect_url': None
        }
        # JSON isteniyorsa JSON döndür
        if request.headers.get('Accept', '').startswith('application/json'):
            return Response(error_data, status=status.HTTP_200_OK)
        # HTML döndür - tenant slug'dan URL oluştur
        fallback_url = get_tenant_frontend_url(tenant_slug=tenant_slug)
        return html_redirect(
            f'{fallback_url}/checkout/fail?order={order_number}&error=Tenant+bulunamadi',
            "Ödeme işleniyor..."
        )
    
    # Payment'ı bul
    try:
        payment = Payment.objects.filter(
            transaction_id=order_number,
            tenant=tenant,
            is_deleted=False
        ).first()
        
        if not payment:
            logger.warning(f"Payment callback handler: Payment bulunamadı for order {order_number}")
            error_data = {
                'success': False,
                'order_number': order_number,
                'payment_status': 'failed',
                'error': 'Payment bulunamadı',
                'redirect_url': None
            }
            # JSON isteniyorsa JSON döndür
            if request.headers.get('Accept', '').startswith('application/json'):
                return Response(error_data, status=status.HTTP_200_OK)
            # HTML döndür - tenant'tan URL al
            frontend_url = get_tenant_frontend_url(tenant=tenant, tenant_slug=tenant_slug)
            return html_redirect(
                f'{frontend_url}/checkout/fail?order={order_number}&error=Payment+bulunamadi',
                "Ödeme işleniyor..."
            )
        
        # Payment durumunu al
        payment_status = payment.status
        is_success = payment_status == Payment.PaymentStatus.COMPLETED
        
        # Frontend URL'ini tenant'tan al
        frontend_url = get_tenant_frontend_url(tenant=tenant, tenant_slug=tenant_slug)
        
        # Redirect URL'i oluştur (frontend kendi redirect'ini yapacak)
        if is_success:
            redirect_url = f"{frontend_url}/checkout/success?order={order_number}"
        else:
            error_param = f"&error={error_message}" if error_message else ""
            redirect_url = f"{frontend_url}/checkout/fail?order={order_number}{error_param}"
        
        logger.info(
            f"Payment callback handler: Order {order_number}, "
            f"Status: {payment_status}, "
            f"Redirect URL: {redirect_url}"
        )
        
        # Response data
        response_data = {
            'success': is_success,
            'order_number': order_number,
            'payment_status': payment_status,
            'payment_id': str(payment.id),
            'payment_number': payment.payment_number,
            'amount': str(payment.amount),
            'currency': payment.currency,
            'redirect_url': redirect_url,
            'error': payment.error_message if not is_success else None,
            'error_code': payment.error_code if not is_success else None,
        }
        
        # JSON isteniyorsa JSON döndür
        if request.headers.get('Accept', '').startswith('application/json'):
            return Response(response_data, status=status.HTTP_200_OK)
        
        # HTML döndür (default) - JavaScript ile redirect yap
        import json as json_lib
        json_data = json_lib.dumps(response_data, ensure_ascii=False)
        
        return HttpResponse(
            f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8"/>
                <meta http-equiv="refresh" content="0;url={redirect_url}" />
                <title>Ödeme İşleniyor...</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding-top: 50px;
                        background: #f5f5f5;
                    }}
                    .container {{
                        max-width: 500px;
                        margin: 0 auto;
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .spinner {{
                        border: 4px solid #f3f3f3;
                        border-top: 4px solid #3498db;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 20px auto;
                    }}
                    @keyframes spin {{
                        0% {{ transform: rotate(0deg); }}
                        100% {{ transform: rotate(360deg); }}
                    }}
                    .message {{
                        color: {'#27ae60' if is_success else '#e74c3c'};
                        font-size: 18px;
                        margin: 20px 0;
                    }}
                    .data {{
                        display: none;
                        font-size: 12px;
                        color: #666;
                        margin-top: 20px;
                        text-align: left;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="spinner"></div>
                    <div class="message">
                        {'Ödeme başarılı! Yönlendiriliyorsunuz...' if is_success else 'Ödeme işleniyor...'}
                    </div>
                    <p>Eğer otomatik yönlendirme çalışmazsa, <a href="{redirect_url}">buraya tıklayın</a>.</p>
                    <div class="data" id="payment-data">{json_data}</div>
                </div>
                <script>
                    // Otomatik redirect
                    window.location.href = "{redirect_url}";
                    
                    // Fallback: 3 saniye sonra redirect
                    setTimeout(function() {{
                        window.location.href = "{redirect_url}";
                    }}, 3000);
                </script>
            </body>
            </html>
            """,
            content_type="text/html"
        )
        
    except Exception as e:
        logger.error(f"Payment callback handler error: {str(e)}", exc_info=True)
        # Exception handler'da tenant ve tenant_slug'ı tekrar al
        tenant_slug_from_order = extract_tenant_slug_from_order_number(order_number) if order_number else None
        
        error_response_data = {
            'success': False,
            'order_number': order_number,
            'payment_status': 'failed',
            'error': f'Sistem hatası: {str(e)}',
            'redirect_url': None
        }
        
        # JSON isteniyorsa JSON döndür
        if request.headers.get('Accept', '').startswith('application/json'):
            return Response(error_response_data, status=status.HTTP_200_OK)
        
        # HTML döndür - tenant slug'dan URL oluştur
        import json as json_lib
        json_data = json_lib.dumps(error_response_data, ensure_ascii=False)
        frontend_url = get_tenant_frontend_url(tenant=None, tenant_slug=tenant_slug_from_order)
        redirect_url = f"{frontend_url}/checkout/fail?order={order_number}&error=Sistem+hatasi"
        
        return HttpResponse(
            f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8"/>
                <meta http-equiv="refresh" content="0;url={redirect_url}" />
                <title>Ödeme Hatası</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding-top: 50px; }}
                    .spinner {{ border: 4px solid #f3f3f3; border-top: 4px solid #e74c3c; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }}
                    @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                </style>
            </head>
            <body>
                <div class="spinner"></div>
                <p>Ödeme işlenirken bir hata oluştu. Yönlendiriliyorsunuz...</p>
                <script>window.location.href = "{redirect_url}";</script>
            </body>
            </html>
            """,
            content_type="text/html"
        )

