"""
Payment Provider Services - Kuveyt API ve diğer ödeme sağlayıcıları için.
"""
import requests
import logging
import hashlib
import base64
import xml.etree.ElementTree as ET
from decimal import Decimal
from django.conf import settings
from urllib.parse import urlencode, unquote

logger = logging.getLogger(__name__)


class PaymentProviderBase:
    """Base class for payment providers."""
    
    def __init__(self, tenant, config=None):
        """
        Args:
            tenant: Tenant instance
            config: Provider configuration dict (API keys, endpoints, etc.)
        """
        self.tenant = tenant
        self.config = config or {}
    
    def create_payment(self, order, amount, customer_info):
        """
        Ödeme oluştur.
        
        Returns:
            dict: {
                'success': bool,
                'payment_url': str,  # Redirect URL
                'transaction_id': str,
                'error': str (if failed)
            }
        """
        raise NotImplementedError
    
    def verify_payment(self, transaction_id):
        """
        Ödeme doğrula.
        
        Returns:
            dict: {
                'success': bool,
                'status': str,  # 'completed', 'failed', 'pending'
                'transaction_id': str,
                'error': str (if failed)
            }
        """
        raise NotImplementedError


class KuwaitPaymentProvider(PaymentProviderBase):
    """
    Kuveyt Türk 3D Secure ödeme sağlayıcısı.
    
    Config'de şu bilgiler olmalı:
    - customer_id: Müşteri Numarası (CustomerId)
    - merchant_id: Mağaza Numarası (MerchantId)
    - api_key / username: API Kullanıcı Adı (UserName)
    - api_secret / password: API Şifresi (Password)
    - api_endpoint: PayGate URL (Production)
    - test_endpoint: PayGate URL (Test)
    - provision_endpoint: ProvisionGate URL (Production)
    - test_provision_endpoint: ProvisionGate URL (Test)
    """
    
    # Currency Code mapping
    CURRENCY_CODES = {
        'TRY': '0949',
        'TL': '0949',
        'USD': '0840',
        'EUR': '0978',
        'GBP': '0826',
    }
    
    def __init__(self, tenant, config=None):
        super().__init__(tenant, config)
        self.test_mode = self.config.get('test_mode', False)
        
        # Test modunda ve config'de bilgi yoksa env'deki test bilgilerini kullan
        if self.test_mode:
            # Test modunda env'deki test bilgilerini öncelik ver
            self.customer_id = (
                self.config.get('customer_id') or 
                self.config.get('customerId') or 
                getattr(settings, 'KUVEYT_TEST_CUSTOMER_ID', '400235')
            )
            self.merchant_id = (
                self.config.get('merchant_id') or 
                self.config.get('merchantId') or 
                getattr(settings, 'KUVEYT_TEST_MERCHANT_ID', '496')
            )
            self.username = (
                self.config.get('api_key') or 
                self.config.get('username') or 
                self.config.get('userName') or 
                getattr(settings, 'KUVEYT_TEST_USERNAME', 'apitest')
            )
            self.password = (
                self.config.get('api_secret') or 
                self.config.get('password') or 
                self.config.get('Password') or 
                getattr(settings, 'KUVEYT_TEST_PASSWORD', 'api123')
            )
        else:
            # Production modunda config'den al (zorunlu)
            self.customer_id = self.config.get('customer_id') or self.config.get('customerId')
            self.merchant_id = self.config.get('merchant_id') or self.config.get('merchantId')
            self.username = self.config.get('api_key') or self.config.get('username') or self.config.get('userName')
            self.password = self.config.get('api_secret') or self.config.get('password') or self.config.get('Password')
        
        # PayGate endpoints
        # Test endpoint varsa ve doğru formatta ise kullan, yoksa default kullan
        test_endpoint = self.config.get('test_endpoint', '')
        test_provision = self.config.get('test_provision_endpoint', '')
        
        if self.test_mode:
            # Test modunda: Eğer test_endpoint doğru format değilse default kullan
            if test_endpoint and 'boatest.kuveytturk.com.tr' in test_endpoint:
                self.paygate_url = test_endpoint
            else:
                # Default test endpoint
                self.paygate_url = 'https://boatest.kuveytturk.com.tr/boa.virtualpos.services/Home/ThreeDModelPayGate'
            
            if test_provision and 'boatest.kuveytturk.com.tr' in test_provision:
                self.provision_url = test_provision
            else:
                # Default test provision endpoint
                self.provision_url = 'https://boatest.kuveytturk.com.tr/boa.virtualpos.services/Home/ThreeDModelProvisionGate'
        else:
            # Production modunda
            prod_endpoint = self.config.get('api_endpoint', '')
            prod_provision = self.config.get('provision_endpoint', '')
            
            if prod_endpoint and 'kuveytturk.com.tr' in prod_endpoint:
                self.paygate_url = prod_endpoint
            else:
                # Default production endpoint
                self.paygate_url = 'https://sanalpos.kuveytturk.com.tr/ServiceGateWay/Home/ThreeDModelPayGate'
            
            if prod_provision and 'kuveytturk.com.tr' in prod_provision:
                self.provision_url = prod_provision
            else:
                # Default production provision endpoint
                self.provision_url = 'https://sanalpos.kuveytturk.com.tr/ServiceGateWay/Home/ThreeDModelProvisionGate'
    
    def _calculate_hash(self, merchant_id, merchant_order_id, amount, ok_url, fail_url, username, password):
        """
        HashData hesapla.
        HashData = base64(sha1(MerchantId + MerchantOrderId + Amount + OkUrl + FailUrl + UserName + hashPassword, "ISO-8859-9"))
        """
        try:
            hash_string = f"{merchant_id}{merchant_order_id}{amount}{ok_url}{fail_url}{username}{password}"
            # ISO-8859-9 encoding ile sha1 hash
            hash_bytes = hash_string.encode('ISO-8859-9')
            sha1_hash = hashlib.sha1(hash_bytes).digest()
            hash_data = base64.b64encode(sha1_hash).decode('utf-8')
            return hash_data
        except Exception as e:
            logger.error(f"Hash calculation error: {str(e)}")
            raise ValueError(f"Hash hesaplama hatası: {str(e)}")
    
    def _format_amount(self, amount):
        """
        Amount formatı: Noktalama yok, gerçek tutarın 100 katı (1 TL → 100)
        """
        # Decimal'i float'a çevir, 100 ile çarp, noktayı kaldır
        amount_float = float(Decimal(str(amount)))
        amount_int = int(amount_float * 100)
        return str(amount_int)
    
    def _get_currency_code(self, currency):
        """
        Currency code mapping (TL=0949, USD=0840, EUR=0978)
        """
        currency_upper = currency.upper()
        return self.CURRENCY_CODES.get(currency_upper, '0949')  # Default: TRY
    
    def create_payment(self, order, amount, customer_info):
        """
        Kuveyt Türk 3D Secure ödeme oluştur (Adım 1: PayGate - Kart Doğrulama).
        
        Args:
            order: Order instance
            amount: Ödeme tutarı
            customer_info: {
                'email': str,
                'name': str,
                'phone': str,
                'address': dict,
                'card_number': str (optional, genelde frontend'den alınır),
                'card_cvv': str (optional),
                'card_expiry': str (optional, format: MM/YY)
            }
        
        Returns:
            dict: {
                'success': bool,
                'payment_html': str,  # PayGate'den dönen HTML (tarayıcıya gösterilecek)
                'transaction_id': str,  # Order number kullanılır
                'error': str (if failed)
            }
        """
        try:
            # Gerekli alanları kontrol et
            if not all([self.customer_id, self.merchant_id, self.username, self.password]):
                return {
                    'success': False,
                    'payment_html': None,
                    'transaction_id': None,
                    'error': 'Kuveyt API bilgileri eksik. CustomerId, MerchantId, UserName ve Password gerekli.',
                }
            
            # OkUrl ve FailUrl
            base_url = getattr(settings, 'FRONTEND_URL', 'https://api.tinisoft.com.tr')
            ok_url = self.config.get('return_url') or f'{base_url}/api/payments/kuveyt/callback/ok'
            fail_url = self.config.get('cancel_url') or f'{base_url}/api/payments/kuveyt/callback/fail'
            
            # & karakterini &amp; ile değiştir (XML'de gerekli)
            ok_url = ok_url.replace('&', '&amp;')
            fail_url = fail_url.replace('&', '&amp;')
            
            # Amount formatı (100 katı, noktalama yok)
            formatted_amount = self._format_amount(amount)
            
            # Currency code
            currency_code = self._get_currency_code(order.currency)
            
            # HashData hesapla
            hash_data = self._calculate_hash(
                merchant_id=self.merchant_id,
                merchant_order_id=order.order_number,
                amount=formatted_amount,
                ok_url=ok_url,
                fail_url=fail_url,
                username=self.username,
                password=self.password
            )
            
            # XML oluştur
            root = ET.Element('KuveytTurkVPosMessage')
            root.set('xmlns', 'http://boa.net/BOA.Integration.VirtualPos/Service')
            
            # APIVersion - TDV2.0.0 kullanılmalı
            ET.SubElement(root, 'APIVersion').text = 'TDV2.0.0'
            
            # OkUrl ve FailUrl
            ET.SubElement(root, 'OkUrl').text = ok_url
            ET.SubElement(root, 'FailUrl').text = fail_url
            
            # HashData
            ET.SubElement(root, 'HashData').text = hash_data
            
            # Merchant bilgileri
            ET.SubElement(root, 'MerchantId').text = str(self.merchant_id)
            ET.SubElement(root, 'CustomerId').text = str(self.customer_id)
            ET.SubElement(root, 'UserName').text = self.username
            
            # Kart bilgileri (opsiyonel - eğer yoksa boş gönderilebilir, frontend'den alınır)
            card_number = customer_info.get('card_number', '').replace(' ', '').replace('-', '')
            ET.SubElement(root, 'CardNumber').text = card_number
            ET.SubElement(root, 'CardExpireDateYear').text = customer_info.get('card_expiry_year', '')
            ET.SubElement(root, 'CardExpireDateMonth').text = customer_info.get('card_expiry_month', '')
            ET.SubElement(root, 'CardCVV2').text = customer_info.get('card_cvv', '')
            ET.SubElement(root, 'CardHolderName').text = customer_info.get('name', '')
            # Kart tipi otomatik belirlenir (ilk rakam 4 ise Visa, 5 ise MasterCard)
            card_type = 'V' if card_number and card_number[0] == '4' else 'M'
            ET.SubElement(root, 'CardType').text = card_type
            
            # Transaction bilgileri
            ET.SubElement(root, 'TransactionType').text = 'Sale'  # Sale: Satış
            ET.SubElement(root, 'InstallmentCount').text = '0'  # 0: Tek çekim
            ET.SubElement(root, 'Amount').text = formatted_amount
            ET.SubElement(root, 'CurrencyCode').text = currency_code
            ET.SubElement(root, 'MerchantOrderId').text = order.order_number
            
            # TransactionSecurity - 3D Secure için 3
            ET.SubElement(root, 'TransactionSecurity').text = '3'
            
            # ClientIP
            client_ip = customer_info.get('ip_address', '')
            ET.SubElement(root, 'ClientIP').text = client_ip
            
            # XML'i string'e çevir
            xml_string = ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')
            
            logger.info(f"Kuveyt PayGate request: order={order.order_number}, amount={formatted_amount}, endpoint={self.paygate_url}")
            logger.debug(f"Kuveyt PayGate XML: {xml_string}")
            
            # PayGate'e POST isteği gönder
            headers = {
                'Content-Type': 'application/xml; charset=utf-8',
            }
            
            try:
                response = requests.post(
                    self.paygate_url,
                    data=xml_string.encode('utf-8'),
                    headers=headers,
                    timeout=30
                )
                
                logger.info(f"Kuveyt PayGate response: status={response.status_code}, content-length={len(response.content)}")
                
                if response.status_code == 200:
                    # PayGate HTML döner (3D Secure ekranı)
                    payment_html = response.text
                    
                    # HTML'de hata var mı kontrol et
                    if 'error' in payment_html.lower() or 'hata' in payment_html.lower():
                        logger.error(f"Kuveyt PayGate HTML error detected: {payment_html[:500]}")
                        return {
                            'success': False,
                            'payment_html': None,
                            'transaction_id': order.order_number,
                            'error': 'PayGate\'den hata döndü. HTML response kontrol edilmeli.',
                        }
                    
                    return {
                        'success': True,
                        'payment_html': payment_html,  # Bu HTML tarayıcıya gösterilecek
                        'transaction_id': order.order_number,
                        'error': None,
                    }
                else:
                    error_msg = f'HTTP {response.status_code}: {response.text[:500]}'
                    logger.error(f"Kuveyt PayGate error: {error_msg}")
                    return {
                        'success': False,
                        'payment_html': None,
                        'transaction_id': order.order_number,
                        'error': error_msg,
                    }
            except requests.exceptions.RequestException as e:
                logger.error(f"Kuveyt PayGate request error: {str(e)}")
                return {
                    'success': False,
                    'payment_html': None,
                    'transaction_id': order.order_number,
                    'error': f'PayGate isteği başarısız: {str(e)}',
                }
        
        except Exception as e:
            logger.error(f"Kuveyt payment creation error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'payment_html': None,
                'transaction_id': None,
                'error': str(e),
            }
    
    def verify_payment(self, transaction_id):
        """
        Kuveyt API ile ödeme doğrula.
        
        Args:
            transaction_id: Transaction ID
        
        Returns:
            dict: Verification response
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
            
            response = requests.get(
                f'{self.api_endpoint}/verify/{transaction_id}',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'pending')
                
                return {
                    'success': True,
                    'status': 'completed' if status == 'success' else 'failed' if status == 'failed' else 'pending',
                    'transaction_id': transaction_id,
                    'error': None,
                }
            else:
                return {
                    'success': False,
                    'status': 'failed',
                    'transaction_id': transaction_id,
                    'error': 'Ödeme doğrulanamadı.',
                }
        
        except Exception as e:
            logger.error(f"Kuveyt payment verification error: {str(e)}")
            return {
                'success': False,
                'status': 'failed',
                'transaction_id': transaction_id,
                'error': str(e),
            }


class PaymentProviderFactory:
    """Payment provider factory."""
    
    PROVIDERS = {
        'kuwait': KuwaitPaymentProvider,
        'kuveyt': KuwaitPaymentProvider,  # Türkçe isim desteği
        # Diğer provider'lar buraya eklenebilir
        # 'iyzico': IyzicoPaymentProvider,
        # 'paytr': PayTRPaymentProvider,
    }
    
    @classmethod
    def get_provider(cls, tenant, provider_name='kuwait', config=None):
        """
        Provider instance oluştur.
        
        Args:
            tenant: Tenant instance
            provider_name: Provider adı ('kuwait', 'iyzico', vb.)
            config: Provider configuration dict (opsiyonel, integration'dan alınır)
        
        Returns:
            PaymentProviderBase: Provider instance
        """
        provider_class = cls.PROVIDERS.get(provider_name.lower())
        
        if not provider_class:
            raise ValueError(f"Unknown payment provider: {provider_name}")
        
        # Eğer config verilmemişse, integration'dan al
        if config is None:
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
                config = integration.get_provider_config()
            except IntegrationProvider.DoesNotExist:
                # Integration yoksa boş config ile devam et
                config = {}
        
        return provider_class(tenant, config)

