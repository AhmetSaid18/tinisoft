"""
Payment Provider Services - Kuveyt API ve diğer ödeme sağlayıcıları için.
"""
import requests
import logging
import hashlib
import base64
import xml.etree.ElementTree as ET
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from urllib.parse import urlencode, unquote

logger = logging.getLogger(__name__)

# Kuveyt Türk PDF'e göre hash encoding'i
HASH_ENCODING = "iso-8859-9"


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
    
    # Currency Code mapping (Kuveyt Türk 4 haneli kodlar)
    CURRENCY_CODES = {
        'TRY': '0949',
        'TL': '0949',
        'USD': '0840',
        'EUR': '0979',  # Hata mesajına göre 0979 (0978 değil)
        'GBP': '0826',
    }
    
    def __init__(self, tenant, config=None):
        super().__init__(tenant, config)
        self.test_mode = self.config.get('test_mode', False)
        
        # Integration'dan gelen config'deki alanları kullan
        # Config JSON field'ında: merchant_id, customer_id
        # api_key -> username, api_secret -> password
        
        # Customer ID (Müşteri Numarası)
        self.customer_id = (
            self.config.get('customer_id') or 
            self.config.get('customerId') or 
            self.config.get('CustomerId')
        )
        
        # Merchant ID (Mağaza Numarası)
        self.merchant_id = (
            self.config.get('merchant_id') or 
            self.config.get('merchantId') or 
            self.config.get('MerchantId')
        )
        
        # Username (API Kullanıcı Adı)
        # Önce config JSON'dan direkt username kontrol et (daha net)
        # Sonra api_key field'ından al (geriye dönük uyumluluk)
        self.username = (
            self.config.get('username') or 
            self.config.get('userName') or 
            self.config.get('UserName') or
            self.config.get('api_key')  # Geriye dönük uyumluluk
        )
        
        # Password (API Şifresi)
        # Önce config JSON'dan direkt password kontrol et (daha net)
        # Sonra api_secret field'ından al (geriye dönük uyumluluk)
        self.password = (
            self.config.get('password') or 
            self.config.get('Password') or
            self.config.get('api_secret')  # Geriye dönük uyumluluk
        )
        
        # Test modunda ve config'de bilgi yoksa env'deki test bilgilerini kullan
        if self.test_mode:
            if not self.customer_id:
                self.customer_id = getattr(settings, 'KUVEYT_TEST_CUSTOMER_ID', '400235')
            if not self.merchant_id:
                self.merchant_id = getattr(settings, 'KUVEYT_TEST_MERCHANT_ID', '496')
            if not self.username:
                self.username = getattr(settings, 'KUVEYT_TEST_USERNAME', 'apitest')
            if not self.password:
                self.password = getattr(settings, 'KUVEYT_TEST_PASSWORD', 'api123')
        
        # Log config bilgilerini (hassas bilgileri gizle)
        logger.info(
            f"Kuveyt PaymentProvider initialized | "
            f"Tenant: {tenant.name} | "
            f"Test Mode: {self.test_mode} | "
            f"Customer ID: {self.customer_id} | "
            f"Merchant ID: {self.merchant_id} | "
            f"Username: {self.username[:3] + '***' if self.username else 'None'}"
        )
        
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
    
    def _hashed_password(self) -> str:
        """
        HashedPassword = base64(sha1(password))
        PDF'e göre password direkt kullanılmaz, önce hash'lenir.
        """
        pwd = (self.password or "")
        digest = hashlib.sha1(pwd.encode(HASH_ENCODING)).digest()
        return base64.b64encode(digest).decode("utf-8")
    
    def _hash_request1(self, merchant_order_id: str, amount: str, ok_url: str, fail_url: str) -> str:
        """
        Request1 (PayGate) için HashData hesapla.
        HashData = base64(sha1(MerchantId + MerchantOrderId + Amount + OkUrl + FailUrl + UserName + HashedPassword))
        
        ÖNEMLİ: Tüm değerler string olarak birleştirilmeli (integer değerler string'e çevrilmeli)
        """
        hp = self._hashed_password()
        
        # Tüm değerleri string'e çevir (merchant_id integer olabilir)
        merchant_id_str = str(self.merchant_id) if self.merchant_id else ""
        username_str = str(self.username) if self.username else ""
        
        # Hash hesaplamasında kullanılan değerleri birleştir
        raw = f"{merchant_id_str}{merchant_order_id}{amount}{ok_url}{fail_url}{username_str}{hp}"
        
        # Debug için log (hassas bilgileri kısalt)
        logger.debug(
            f"Hash calculation (Request1): "
            f"MerchantId={merchant_id_str}, "
            f"OrderId={merchant_order_id}, "
            f"Amount={amount}, "
            f"OkUrl={ok_url}, "
            f"FailUrl={fail_url}, "
            f"UserName={username_str}, "
            f"HashedPassword={hp[:10]}..."
        )
        logger.debug(f"Hash raw string length: {len(raw)}")
        
        digest = hashlib.sha1(raw.encode(HASH_ENCODING)).digest()
        hash_result = base64.b64encode(digest).decode("utf-8")
        
        logger.debug(f"Calculated HashData: {hash_result}")
        
        return hash_result
    
    def _hash_request2(self, merchant_order_id: str, amount: str) -> str:
        """
        Request2 (ProvisionGate) için HashData hesapla.
        HashData = base64(sha1(MerchantId + MerchantOrderId + Amount + UserName + HashedPassword))
        
        ÖNEMLİ: Tüm değerler string olarak birleştirilmeli (integer değerler string'e çevrilmeli)
        """
        hp = self._hashed_password()
        
        # Tüm değerleri string'e çevir
        merchant_id_str = str(self.merchant_id) if self.merchant_id else ""
        username_str = str(self.username) if self.username else ""
        
        raw = f"{merchant_id_str}{merchant_order_id}{amount}{username_str}{hp}"
        
        logger.debug(
            f"Hash calculation (Request2): "
            f"MerchantId={merchant_id_str}, "
            f"OrderId={merchant_order_id}, "
            f"Amount={amount}, "
            f"UserName={username_str}, "
            f"HashedPassword={hp[:10]}..."
        )
        
        digest = hashlib.sha1(raw.encode(HASH_ENCODING)).digest()
        return base64.b64encode(digest).decode("utf-8")
    
    def _hash_response1(self, merchant_order_id: str, response_code: str, order_id: str) -> str:
        """
        Response1 doğrulaması için hash hesapla.
        HashData = base64(sha1(MerchantOrderId + ResponseCode + OrderId + HashedPassword))
        """
        hp = self._hashed_password()
        raw = f"{merchant_order_id}{response_code}{order_id}{hp}"
        digest = hashlib.sha1(raw.encode(HASH_ENCODING)).digest()
        return base64.b64encode(digest).decode("utf-8")
    
    def _format_amount(self, amount):
        """
        Amount formatı: Noktalama yok, gerçek tutarın 100 katı (1 TL → 100)
        Decimal kullanarak yuvarlama hatalarını önle.
        """
        amount_dec = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        amount_int = int((amount_dec * 100).to_integral_value(rounding=ROUND_HALF_UP))
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
            
            # OkUrl ve FailUrl - API base URL kullan (callback endpoint'leri için)
            # NOT: Frontend URL değil, API URL kullanılmalı çünkü Kuveyt backend'e POST yapacak
            api_base_url = self.config.get('api_base_url') or getattr(settings, 'API_BASE_URL', 'https://api.tinisoft.com.tr')
            if not api_base_url.startswith('http'):
                api_base_url = f'https://{api_base_url}'
            
            # ÖNEMLİ: Config'deki return_url/cancel_url genelde frontend URL'leri olur
            # Biz backend callback URL'lerini kullanmalıyız, config'deki URL'leri görmezden gel
            # Doğru callback URL'leri her zaman backend endpoint'leri olmalı
            # Config'den gelen URL'leri override et
            # NOT: Hash hesaplamasında ve XML'de AYNI URL'ler kullanılmalı
            ok_url = f'{api_base_url}/api/payments/kuveyt/callback/ok/'
            fail_url = f'{api_base_url}/api/payments/kuveyt/callback/fail/'
            
            # Trailing slash olduğundan emin ol
            if not ok_url.endswith('/'):
                ok_url += '/'
            if not fail_url.endswith('/'):
                fail_url += '/'
            
            # Config'deki yanlış URL'leri override et (eğer varsa)
            # Config'den gelen return_url/cancel_url frontend URL'leri olabilir, onları kullanma
            logger.info(
                f"Kuveyt PayGate callback URLs: "
                f"OkUrl={ok_url}, "
                f"FailUrl={fail_url} | "
                f"Config return_url (ignored): {self.config.get('return_url', 'None')}, "
                f"Config cancel_url (ignored): {self.config.get('cancel_url', 'None')}"
            )
            
            # Amount formatı (100 katı, noktalama yok)
            formatted_amount = self._format_amount(amount)
            
            # Currency code - Order'dan al, 4 haneli format kullan (0949, 0840, 0979)
            order_currency = getattr(order, 'currency', 'TRY') or 'TRY'
            currency_code = self._get_currency_code(order_currency)
            
            # HashData hesapla (HashedPassword ile - PDF uyumlu)
            hash_data = self._hash_request1(
                merchant_order_id=order.order_number,
                amount=formatted_amount,
                ok_url=ok_url,
                fail_url=fail_url
            )
            
            # 3DS2 için gerekli bilgileri al
            device_channel = customer_info.get('device_channel') or '02'  # 02 = browser
            client_ip = customer_info.get('ip_address') or ''
            
            # Fatura/iletişim bilgileri (3DS2 CardHolderData)
            bill = customer_info.get('billing', {}) or {}
            email = customer_info.get('email') or ''
            gsm = customer_info.get('phone') or ''
            gsm = ''.join([c for c in gsm if c.isdigit()])  # Sadece rakamlar
            
            # XML oluştur (Kuveyt Türk TDV2.0.0 formatı)
            xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
            xml_parts.append('<KuveytTurkVPosMessage xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">')
            xml_parts.append('<APIVersion>TDV2.0.0</APIVersion>')
            xml_parts.append(f'<OkUrl>{ok_url}</OkUrl>')
            xml_parts.append(f'<FailUrl>{fail_url}</FailUrl>')
            xml_parts.append(f'<HashData>{hash_data}</HashData>')
            xml_parts.append(f'<MerchantId>{self.merchant_id}</MerchantId>')
            xml_parts.append(f'<CustomerId>{self.customer_id}</CustomerId>')
            xml_parts.append(f'<UserName>{self.username}</UserName>')
            
            # DeviceData bloğu (TDV2.0.0 için zorunlu)
            xml_parts.append('<DeviceData>')
            xml_parts.append(f'<DeviceChannel>{device_channel}</DeviceChannel>')
            xml_parts.append(f'<ClientIP>{client_ip}</ClientIP>')
            xml_parts.append('</DeviceData>')
            
            # CardHolderData bloğu (TDV2.0.0 için önerilen)
            xml_parts.append('<CardHolderData>')
            xml_parts.append(f'<BillAddrCity>{bill.get("city", "")}</BillAddrCity>')
            xml_parts.append(f'<BillAddrCountry>{bill.get("country_code", "792")}</BillAddrCountry>')
            xml_parts.append(f'<BillAddrLine1>{bill.get("line1", "")}</BillAddrLine1>')
            xml_parts.append(f'<BillAddrPostCode>{bill.get("postcode", "")}</BillAddrPostCode>')
            xml_parts.append(f'<BillAddrState>{bill.get("state", "")}</BillAddrState>')
            xml_parts.append(f'<Email>{email}</Email>')
            if gsm:
                xml_parts.append('<MobilePhone>')
                xml_parts.append('<Cc>90</Cc>')
                xml_parts.append(f'<Subscriber>{gsm}</Subscriber>')
                xml_parts.append('</MobilePhone>')
            xml_parts.append('</CardHolderData>')
            
            # Kart bilgileri
            card_number = customer_info.get('card_number', '').replace(' ', '').replace('-', '')
            if card_number:
                xml_parts.append(f'<CardNumber>{card_number}</CardNumber>')
                xml_parts.append(f'<CardExpireDateYear>{customer_info.get("card_expiry_year", "")}</CardExpireDateYear>')
                xml_parts.append(f'<CardExpireDateMonth>{customer_info.get("card_expiry_month", "")}</CardExpireDateMonth>')
                xml_parts.append(f'<CardCVV2>{customer_info.get("card_cvv", "")}</CardCVV2>')
                xml_parts.append(f'<CardHolderName>{customer_info.get("name", "")}</CardHolderName>')
                # Kart tipi otomatik belirlenir (ilk rakam 4 ise Visa, 5 ise MasterCard)
                card_type = 'V' if card_number and card_number[0] == '4' else 'M'
                xml_parts.append(f'<CardType>{card_type}</CardType>')
            
            xml_parts.append('<TransactionType>Sale</TransactionType>')
            xml_parts.append('<InstallmentCount>0</InstallmentCount>')
            xml_parts.append(f'<Amount>{formatted_amount}</Amount>')
            xml_parts.append(f'<CurrencyCode>{currency_code}</CurrencyCode>')
            xml_parts.append(f'<MerchantOrderId>{order.order_number}</MerchantOrderId>')
            xml_parts.append('<TransactionSecurity>3</TransactionSecurity>')
            xml_parts.append('</KuveytTurkVPosMessage>')
            xml_string = '\n'.join(xml_parts)
            
            logger.info(f"Kuveyt PayGate request: order={order.order_number}, amount={formatted_amount}, currency={order_currency} ({currency_code}), endpoint={self.paygate_url}")
            logger.debug(f"Kuveyt PayGate XML: {xml_string}")
            
            # PayGate'e POST isteği gönder
            headers = {
                'Content-Type': 'application/xml; charset=utf-8',
            }
            
            try:
                # Timeout'u 60 saniyeye çıkar (Kuveyt bazen yavaş yanıt verebilir)
                response = requests.post(
                    self.paygate_url,
                    data=xml_string.encode('utf-8'),
                    headers=headers,
                    timeout=60  # 30'dan 60'a çıkarıldı
                )
                
                logger.info(f"Kuveyt PayGate response: status={response.status_code}, content-length={len(response.content)}")
                
                if response.status_code == 200:
                    # PayGate HTML döner (3D Secure ekranı)
                    payment_html = response.text
                    
                    # HTML içeriğini log'la (debug için)
                    logger.info(f"Kuveyt PayGate HTML response (first 1000 chars): {payment_html[:1000]}")
                    
                    # HTML içinde XML response var mı kontrol et (hata durumunda)
                    # Kuveyt bazen hata durumunda HTML içinde XML response döndürür
                    import re
                    xml_match = re.search(r'<VPosTransactionResponseContract[^>]*>(.*?)</VPosTransactionResponseContract>', payment_html, re.DOTALL)
                    if xml_match:
                        try:
                            xml_content = xml_match.group(0)
                            root = ET.fromstring(xml_content)
                            
                            response_code = root.find('ResponseCode')
                            response_code = response_code.text if response_code is not None else None
                            
                            response_message = root.find('ResponseMessage')
                            response_message = response_message.text if response_message is not None else None
                            
                            if response_code and response_code != '00':
                                # Hata var - ResponseCode ve ResponseMessage'ı log'la
                                logger.error(
                                    f"Kuveyt PayGate error in response: "
                                    f"ResponseCode={response_code}, "
                                    f"ResponseMessage={response_message}"
                                )
                                
                                # Özel hata mesajları
                                error_message = response_message or 'Bilinmeyen hata'
                                user_friendly_message = error_message
                                
                                if response_code == 'ApiUserNotDefined':
                                    user_friendly_message = (
                                        'Kuveyt Türk API kullanıcısı tanımlanmamış. '
                                        'Lütfen Kuveyt Türk Sanal POS panelinde API rolünde kullanıcı oluşturun.'
                                    )
                                elif 'ApiUser' in response_code or 'User' in response_code:
                                    user_friendly_message = (
                                        'Kuveyt Türk API kullanıcı bilgileri hatalı. '
                                        'Lütfen API kullanıcı adı ve şifresini kontrol edin.'
                                    )
                                
                                return {
                                    'success': False,
                                    'payment_html': None,
                                    'transaction_id': order.order_number,
                                    'error': user_friendly_message,
                                    'error_code': response_code,
                                    'error_details': {
                                        'response_code': response_code,
                                        'response_message': response_message,
                                        'bank_error': True,
                                    },
                                }
                        except Exception as parse_error:
                            logger.warning(f"Could not parse XML from HTML response: {str(parse_error)}")
                            # XML parse edilemezse devam et (normal HTML response olabilir)
                    
                    # HTML'de hata var mı kontrol et (genel)
                    if 'error' in payment_html.lower() or 'hata' in payment_html.lower():
                        logger.error(f"Kuveyt PayGate HTML error detected: {payment_html[:500]}")
                        return {
                            'success': False,
                            'payment_html': None,
                            'transaction_id': order.order_number,
                            'error': 'PayGate\'den hata döndü. HTML response kontrol edilmeli.',
                        }
                    
                    # HTML'deki form action URL'ini kontrol et ve düzelt (eğer yanlışsa)
                    # Kuveyt bazen yanlış action URL döndürebilir veya bizim gönderdiğimiz URL'i kullanmayabilir
                    import re
                    # action="..." veya action='...' pattern'ini bul
                    action_pattern = r'action=["\']([^"\']+)["\']'
                    matches = re.findall(action_pattern, payment_html)
                    if matches:
                        logger.info(f"Kuveyt PayGate HTML form action URLs found: {matches}")
                        
                        # Eğer action URL yanlışsa (örn: /payment/cancel/ gibi), doğru callback URL ile değiştir
                        for wrong_url in matches:
                            # Yanlış URL pattern'lerini tespit et
                            if '/payment/cancel' in wrong_url or '/payment/return' in wrong_url:
                                logger.warning(f"Kuveyt PayGate HTML contains wrong action URL: {wrong_url}")
                                # Doğru URL ile değiştir
                                if '/cancel' in wrong_url:
                                    correct_url = fail_url
                                elif '/return' in wrong_url:
                                    correct_url = ok_url
                                else:
                                    # Bilinmeyen durumda fail_url kullan
                                    correct_url = fail_url
                                
                                # HTML'deki action URL'ini düzelt (regex ile replace yap)
                                payment_html = re.sub(
                                    rf'action=["\']{re.escape(wrong_url)}["\']',
                                    f'action="{correct_url}"',
                                    payment_html
                                )
                                logger.info(f"Fixed HTML action URL: {wrong_url} -> {correct_url}")
                    
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
    
    def provision_payment(self, merchant_order_id: str, amount, md: str):
        """
        Kuveyt Türk 3D Secure Adım 2: ProvisionGate'e Request2 gönder.
        Bank callback'ten gelen MD ile ödeme onayı al.
        
        Args:
            merchant_order_id: MerchantOrderId (Order number)
            amount: Ödeme tutarı
            md: Bankadan gelen MD değeri
        
        Returns:
            dict: {
                'success': bool,
                'response_code': str,
                'response_message': str,
                'order_id': str,  # VPosTransactionId
                'error': str (if failed)
            }
        """
        try:
            formatted_amount = self._format_amount(amount)
            hash_data = self._hash_request2(
                merchant_order_id=merchant_order_id,
                amount=formatted_amount
            )
            
            # Order'dan currency'yi al (merchant_order_id = order_number)
            order_currency = 'TRY'  # Default
            try:
                from apps.models import Order
                order = Order.objects.get(order_number=merchant_order_id)
                order_currency = getattr(order, 'currency', 'TRY') or 'TRY'
            except Order.DoesNotExist:
                logger.warning(f"Order not found for provision: {merchant_order_id}, using default currency TRY")
            
            currency_code = self._get_currency_code(order_currency)
            
            # XML oluştur (ProvisionGate - Request2)
            xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
            xml_parts.append('<KuveytTurkVPosMessage xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">')
            xml_parts.append('<APIVersion>TDV2.0.0</APIVersion>')
            xml_parts.append(f'<HashData>{hash_data}</HashData>')
            xml_parts.append(f'<MerchantId>{self.merchant_id}</MerchantId>')
            xml_parts.append(f'<CustomerId>{self.customer_id}</CustomerId>')
            xml_parts.append(f'<UserName>{self.username}</UserName>')
            xml_parts.append('<TransactionType>Sale</TransactionType>')
            xml_parts.append('<InstallmentCount>0</InstallmentCount>')
            xml_parts.append(f'<Amount>{formatted_amount}</Amount>')
            xml_parts.append(f'<CurrencyCode>{currency_code}</CurrencyCode>')
            xml_parts.append(f'<MerchantOrderId>{merchant_order_id}</MerchantOrderId>')
            xml_parts.append('<TransactionSecurity>3</TransactionSecurity>')
            
            # AdditionalData -> MD
            xml_parts.append('<KuveytTurkVPosAdditionalData>')
            xml_parts.append('<AdditionalData>')
            xml_parts.append('<Key>MD</Key>')
            xml_parts.append(f'<Data>{md}</Data>')
            xml_parts.append('</AdditionalData>')
            xml_parts.append('</KuveytTurkVPosAdditionalData>')
            
            xml_parts.append('</KuveytTurkVPosMessage>')
            xml_string = "\n".join(xml_parts)
            
            logger.info(f"Kuveyt ProvisionGate request: order={merchant_order_id}, amount={formatted_amount}")
            logger.debug(f"Kuveyt ProvisionGate XML: {xml_string}")
            
            headers = {"Content-Type": "application/xml; charset=utf-8"}
            response = requests.post(
                self.provision_url,
                data=xml_string.encode("utf-8"),
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Kuveyt ProvisionGate response: status={response.status_code}")
            logger.debug(f"Kuveyt ProvisionGate response body: {response.text[:1000]}")
            
            if response.status_code == 200:
                # XML parse et
                try:
                    root = ET.fromstring(response.text)
                    
                    # ResponseCode ve ResponseMessage değerlerini al
                    response_code = root.find('ResponseCode')
                    response_code = response_code.text if response_code is not None else None
                    
                    response_message = root.find('ResponseMessage')
                    response_message = response_message.text if response_message is not None else None
                    
                    order_id = root.find('OrderId')
                    order_id = order_id.text if order_id is not None else None
                    
                    if response_code == '00':
                        # Ödeme başarılı
                        return {
                            'success': True,
                            'response_code': response_code,
                            'response_message': response_message or 'Başarılı',
                            'order_id': order_id,
                            'error': None,
                        }
                    else:
                        # Ödeme başarısız
                        return {
                            'success': False,
                            'response_code': response_code,
                            'response_message': response_message or 'Bilinmeyen hata',
                            'order_id': order_id,
                            'error': f"ResponseCode: {response_code} - {response_message}",
                        }
                except ET.ParseError as e:
                    logger.error(f"Kuveyt ProvisionGate XML parse error: {str(e)}")
                    return {
                        'success': False,
                        'response_code': None,
                        'response_message': None,
                        'order_id': None,
                        'error': f"XML parse hatası: {str(e)}",
                    }
            else:
                return {
                    'success': False,
                    'response_code': None,
                    'response_message': None,
                    'order_id': None,
                    'error': f"HTTP {response.status_code}: {response.text[:500]}",
                }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Kuveyt ProvisionGate request error: {str(e)}")
            return {
                'success': False,
                'response_code': None,
                'response_message': None,
                'order_id': None,
                'error': f"ProvisionGate isteği başarısız: {str(e)}",
            }
        except Exception as e:
            logger.error(f"Kuveyt ProvisionGate error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'response_code': None,
                'response_message': None,
                'order_id': None,
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

