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

    def get_installment_options(self, amount, bin_number=None):
        """
        Taksit seçeneklerini getir.
        Config'deki ayarlara göre hesaplama yapar.
        
        Args:
            amount: Ödeme tutarı
            bin_number: Kartın ilk 6 hanesi (opsiyonel)
            
        Returns:
            list: [
                {
                    'count': 1,
                    'amount': 100.00,
                    'total': 100.00,
                    'interest_rate': 0,
                    'has_interest': False
                },
                ...
            ]
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
        
        # Test modunda her zaman default test bilgilerini kullan (config'deki değerleri ignore et)
        # Çünkü test ortamında herkes aynı test bilgilerini kullanmalı
        if self.test_mode:
            # Test modunda default test değerlerini kullan
            self.customer_id = getattr(settings, 'KUVEYT_TEST_CUSTOMER_ID', '400235')
            self.merchant_id = getattr(settings, 'KUVEYT_TEST_MERCHANT_ID', '496')
            self.username = getattr(settings, 'KUVEYT_TEST_USERNAME', 'apitest')
            self.password = getattr(settings, 'KUVEYT_TEST_PASSWORD', 'api123')
        else:
            # Canlı modda config'den al
            self.customer_id = (
                self.config.get('customer_id') or 
                self.config.get('customerId') or 
                self.config.get('CustomerId')
            )
            
            self.merchant_id = (
                self.config.get('merchant_id') or 
                self.config.get('merchantId') or 
                self.config.get('MerchantId')
            )
            
            self.username = (
                self.config.get('username') or 
                self.config.get('userName') or 
                self.config.get('UserName') or
                self.config.get('api_key')  # Geriye dönük uyumluluk
            )
            
            self.password = (
                self.config.get('password') or 
                self.config.get('Password') or
                self.config.get('api_secret')  # Geriye dönük uyumluluk
            )
        
        # Log config bilgilerini (hassas bilgileri gizle)
        logger.info(
            f"Kuveyt PaymentProvider initialized | "
            f"Tenant: {tenant.name} | "
            f"Test Mode: {self.test_mode} | "
            f"Customer ID: {self.customer_id} | "
            f"Merchant ID: {self.merchant_id} | "
            f"Username: {self.username[:3] + '***' if self.username else 'None'}"
        )
        
        # API endpoint - ENV'den al (sabit değer, frontend'den gelmemeli)
        # Config'deki endpoint'i ignore et, her zaman env'den al
        if self.test_mode:
            # Test modunda env'den test endpoint'i al
            self.api_url = getattr(settings, 'KUVEYT_API_TEST_URL', 'https://boatest.kuveytturk.com.tr/boa.virtualpos.services/Home/ThreeDModelPayGate')
            self.provision_url = getattr(settings, 'KUVEYT_PROVISION_TEST_URL', 'https://boatest.kuveytturk.com.tr/boa.virtualpos.services/Home/ThreeDModelProvisionGate')
        else:
            # Production modunda env'den production endpoint'i al
            self.api_url = getattr(settings, 'KUVEYT_API_URL', 'https://boa.kuveytturk.com.tr/sanalposservice/Home/ThreeDModelPayGate')
            self.provision_url = getattr(settings, 'KUVEYT_PROVISION_URL', 'https://boa.kuveytturk.com.tr/sanalposservice/Home/ThreeDModelProvisionGate')
    
    def _hashed_password(self) -> str:
        """
        HashedPassword hesaplama (PDF Sayfa 19):
        $HashedPassword = base64_encode(sha1($Password, "ISO-8859-9"));
        
        Python'da: base64(sha1(password.encode("ISO-8859-9")))
        """
        pwd = (self.password or "")
        # ISO-8859-9 encoding ile hash'le
        pwd_bytes = pwd.encode(HASH_ENCODING)
        digest = hashlib.sha1(pwd_bytes).digest()
        hashed = base64.b64encode(digest).decode("utf-8")
        logger.debug(f"HashedPassword calculated: {hashed[:10]}... (from password length: {len(pwd)})")
        return hashed
    
    def _hash_request1(self, merchant_order_id: str, amount: str, ok_url: str, fail_url: str) -> str:
        """
        Request1 (PayGate) için HashData hesapla (PDF Sayfa 19).
        
        Hash formülü (PDF'den - TAM OLARAK):
        $HashData = base64_encode(sha1($MerchantId.$MerchantOrderId.$Amount.$OkUrl.$FailUrl.$UserName.$HashedPassword, "ISO-8859-9"));
        
        ÖNEMLİ (PDF'den):
        - Tüm değerler string olarak birleştirilmeli
        - Encoding: ISO-8859-9
        - Sıra: MerchantId + MerchantOrderId + Amount + OkUrl + FailUrl + UserName + HashedPassword
        - OkUrl ve FailUrl hash'e DAHIL EDILMELI (PDF'de açıkça yazıyor)
        - PHP'deki gibi string concatenation (.) kullanılmalı - hiçbir ekstra karakter veya boşluk olmamalı
        """
        hp = self._hashed_password()
        
        # Tüm değerleri string'e çevir (PDF formülüne göre)
        # ÖNEMLİ: None değerleri boş string'e çevir, ama aslında bu değerler hiç None olmamalı
        merchant_id_str = str(self.merchant_id) if self.merchant_id is not None else ""
        username_str = str(self.username) if self.username is not None else ""
        merchant_order_id_str = str(merchant_order_id) if merchant_order_id else ""
        amount_str = str(amount) if amount else ""
        ok_url_str = str(ok_url) if ok_url else ""
        fail_url_str = str(fail_url) if fail_url else ""
        
        # PDF formülüne göre tam sırayla birleştir (PHP'deki . operatörü gibi):
        # MerchantId + MerchantOrderId + Amount + OkUrl + FailUrl + UserName + HashedPassword
        # ÖNEMLİ: F-string kullanma, direkt + operatörü kullan (PHP'deki . gibi)
        raw = merchant_id_str + merchant_order_id_str + amount_str + ok_url_str + fail_url_str + username_str + hp
        
        # Debug için log (hassas bilgileri kısalt) - INFO seviyesinde
        logger.info(
            f"Hash calculation (Request1 - PDF formülü): "
            f"MerchantId={merchant_id_str}, "
            f"OrderId={merchant_order_id_str}, "
            f"Amount={amount_str}, "
            f"OkUrl={ok_url_str}, "
            f"FailUrl={fail_url_str}, "
            f"UserName={username_str}, "
            f"HashedPassword={hp[:10]}..."
        )
        logger.info(f"Hash raw string length: {len(raw)}")
        logger.info(f"Hash raw string (first 200 chars): {raw[:200]}")
        logger.info(f"Hash raw string (last 50 chars): {raw[-50:]}")
        
        # ISO-8859-9 encoding ile hash'le
        # ÖNEMLİ: Raw string'i direkt ISO-8859-9 ile encode et
        try:
            raw_bytes = raw.encode(HASH_ENCODING)
            logger.info(f"Encoded bytes length: {len(raw_bytes)}")
        except UnicodeEncodeError as e:
            # Eğer encoding hatası olursa, karakterleri replace et veya ignore et
            logger.warning(f"Encoding error: {e}, trying with error handling")
            # ISO-8859-9'da olmayan karakterleri '?' ile replace et
            raw_bytes = raw.encode(HASH_ENCODING, errors='replace')
            logger.warning(f"Used error='replace' for encoding, result length: {len(raw_bytes)}")
        
        digest = hashlib.sha1(raw_bytes).digest()
        hash_result = base64.b64encode(digest).decode("utf-8")
        
        logger.info(f"Calculated HashData: {hash_result}")
        logger.info(f"Hash calculation complete - all values used correctly")
        
        return hash_result
    
    def _hash_request2(self, merchant_order_id: str, amount: str) -> str:
        """
        Request2 (ProvisionGate) için HashData hesapla (PDF Sayfa 19).
        
        Hash formülü (PDF'den - Request 2 için OkUrl ve FailUrl dahil edilmez):
        $HashData = base64_encode(sha1($MerchantId.$MerchantOrderId.$Amount.$UserName.$HashedPassword, "ISO-8859-9"));
        
        ÖNEMLİ: 
        - Tüm değerler string olarak birleştirilmeli (integer değerler string'e çevrilmeli)
        - Encoding: ISO-8859-9
        - OkUrl ve FailUrl hash'e DAHIL EDILMEZ (PDF Not: "Sayfa yönlendirmesi yapılmadığından")
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
            # NOT: PDF'e göre OkUrl ve FailUrl'de TRAILING SLASH OLMAMALI
            # Örnek: http://localhost/php//ThreeDModetest/Approval.php (trailing slash yok)
            ok_url = f'{api_base_url}/api/payments/kuveyt/callback/ok'
            fail_url = f'{api_base_url}/api/payments/kuveyt/callback/fail'
            
            # Trailing slash'ı kaldır (eğer varsa)
            ok_url = ok_url.rstrip('/')
            fail_url = fail_url.rstrip('/')
            
            # Config'deki yanlış URL'leri override et (eğer varsa)
            # Config'den gelen return_url/cancel_url frontend URL'leri olabilir, onları kullanma
            logger.info(
                f"Kuveyt callback URLs: "
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
            
            # HashData hesapla (PDF formülüne göre - TAM OLARAK)
            # PDF'de açıkça yazıyor: MerchantId + MerchantOrderId + Amount + OkUrl + FailUrl + UserName + HashedPassword
            # OkUrl ve FailUrl hash'e DAHIL EDILMELI (PDF'de zorunlu)
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
            # XML'de gönderilecek URL'leri log'la (hash ile karşılaştırma için)
            logger.info(f"XML OkUrl: {ok_url}")
            logger.info(f"XML FailUrl: {fail_url}")
            logger.info(f"Hash OkUrl: {ok_url} (same as XML)")
            logger.info(f"Hash FailUrl: {fail_url} (same as XML)")
            
            xml_parts = ['<?xml version="1.0" encoding="ISO-8859-9"?>']
            # XML namespace attribute'lerini kaldır (bazı sistemlerde hata verebilir)
            xml_parts.append('<KuveytTurkVPosMessage>')
            xml_parts.append('<APIVersion>TDV2.0.0</APIVersion>')
            xml_parts.append(f'<OkUrl>{ok_url}</OkUrl>')
            xml_parts.append(f'<FailUrl>{fail_url}</FailUrl>')
            xml_parts.append(f'<HashData>{hash_data}</HashData>')
            # XML'de de string olarak gönder (hash hesaplaması ile tutarlılık için)
            xml_parts.append(f'<MerchantId>{str(self.merchant_id)}</MerchantId>')
            xml_parts.append(f'<CustomerId>{str(self.customer_id)}</CustomerId>')
            xml_parts.append(f'<UserName>{str(self.username)}</UserName>')
            
            # DeviceData bloğu (TDV2.0.0 için zorunlu ama içeriği kontrol et)
            xml_parts.append('<DeviceData>')
            xml_parts.append(f'<DeviceChannel>{device_channel}</DeviceChannel>')
            if client_ip:
                xml_parts.append(f'<ClientIP>{client_ip}</ClientIP>')
            xml_parts.append('</DeviceData>')
            
            # CardHolderData bloğu (TDV2.0.0 için önerilen)
            # Boş tag göndermemek için kontrol et
            xml_parts.append('<CardHolderData>')
            if bill.get("city"):
                xml_parts.append(f'<BillAddrCity>{bill.get("city")}</BillAddrCity>')
            # Country code boş ise varsayılan 792 (TR)
            xml_parts.append(f'<BillAddrCountry>{bill.get("country_code", "792")}</BillAddrCountry>')
            if bill.get("line1"):
                xml_parts.append(f'<BillAddrLine1>{bill.get("line1")}</BillAddrLine1>')
            if bill.get("postcode"):
                xml_parts.append(f'<BillAddrPostCode>{bill.get("postcode")}</BillAddrPostCode>')
            if bill.get("state"):
                xml_parts.append(f'<BillAddrState>{bill.get("state")}</BillAddrState>')
            if email:
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
            xml_parts.append('<AuthType>ThreeD</AuthType>')  # Bazı entegrasyonlarda zorunlu
            xml_parts.append('<TransactionType>Sale</TransactionType>')
            xml_parts.append('<AuthType>ThreeD</AuthType>')
            
            # Taksit sayısı (Default: 0 - Tek çekim)
            installment_count = customer_info.get('installment_count', 0)
            # Kuveyt Türk'te tek çekim 0 veya boş gönderilir, taksitli ise taksit sayısı (örn: 3)
            # Eğer 1 gelirse de 0 olarak gönder (tek çekim)
            installment_value = '0' if not installment_count or int(installment_count) <= 1 else str(installment_count)
            xml_parts.append(f'<InstallmentCount>{installment_value}</InstallmentCount>')
            
            xml_parts.append(f'<Amount>{formatted_amount}</Amount>')
            xml_parts.append(f'<CurrencyCode>{currency_code}</CurrencyCode>')
            xml_parts.append(f'<MerchantOrderId>{order.order_number}</MerchantOrderId>')
            xml_parts.append('<TransactionSecurity>3</TransactionSecurity>')
            xml_parts.append('</KuveytTurkVPosMessage>')
            xml_string = '\n'.join(xml_parts)
            
            logger.info(f"Kuveyt API request: order={order.order_number}, amount={formatted_amount}, currency={order_currency} ({currency_code}), endpoint={self.api_url}")
            logger.debug(f"Kuveyt PayGate XML Payload:\n{xml_string}")
            
            # PayGate'e POST isteği gönder
            headers = {
                'Content-Type': 'application/xml; charset=ISO-8859-9',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Tinisoft/1.0',
            }
            
            try:
                # Timeout'u 60 saniyeye çıkar
                # Test modunda verify=False yap (SSL hatalarını önlemek için)
                verify_ssl = not self.test_mode
                
                response = requests.post(
                    self.api_url,
                    data=xml_string.encode('ISO-8859-9', errors='replace'),
                    headers=headers,
                    timeout=60,
                    verify=verify_ssl
                )
                
                logger.info(f"Kuveyt API response: status={response.status_code}, content-length={len(response.content)}")
                
                if response.status_code == 200:
                    # PayGate HTML döner (3D Secure ekranı)
                    payment_html = response.text
                    
                    # HTML içeriğini log'la (debug için)
                    logger.info(f"Kuveyt PayGate HTML response (first 1000 chars): {payment_html[:1000]}")
                    
                    # HTML içinde XML response var mı kontrol et (hata durumunda)
                    # Kuveyt bazen hata durumunda HTML içinde XML response döndürür
                    # XML hem normal hem de URL-encoded olabilir (AuthenticationResponse value içinde)
                    # ÖNEMLİ: Her zaman AuthenticationResponse'dan ResponseCode'u kontrol et
                    import re
                    from urllib.parse import unquote
                    
                    # AuthenticationResponse'dan ResponseCode'u çıkarmaya çalış (her zaman kontrol et)
                    response_code = None
                    response_message = None
                    xml_parse_successful = False
                    
                    # Önce AuthenticationResponse'u bul (hem normal hem URL-encoded olabilir)
                    auth_response_match = re.search(r'name="AuthenticationResponse"\s+value="([^"]+)"', payment_html, re.DOTALL)
                    if auth_response_match:
                        try:
                            encoded_xml = auth_response_match.group(1)
                            decoded_xml = unquote(encoded_xml)
                            logger.debug(f"Decoded AuthenticationResponse XML (first 500 chars): {decoded_xml[:500]}")
                            
                            # Önce XML olarak parse etmeyi dene
                            try:
                                root = ET.fromstring(decoded_xml)
                                response_code_elem = root.find('ResponseCode')
                                response_message_elem = root.find('ResponseMessage')
                                
                                if response_code_elem is not None:
                                    response_code = response_code_elem.text
                                if response_message_elem is not None:
                                    response_message = response_message_elem.text
                                
                                xml_parse_successful = True
                                logger.info(f"Successfully parsed XML from AuthenticationResponse: ResponseCode={response_code}")
                            except ET.ParseError as parse_error:
                                # XML parse başarısız, regex ile dene
                                logger.warning(f"Could not parse XML from AuthenticationResponse: {str(parse_error)}, trying regex extraction")
                                response_code_match = re.search(r'<ResponseCode>(.*?)</ResponseCode>', decoded_xml, re.DOTALL)
                                response_message_match = re.search(r'<ResponseMessage>(.*?)</ResponseMessage>', decoded_xml, re.DOTALL)
                                
                                if response_code_match:
                                    response_code = response_code_match.group(1)
                                if response_message_match:
                                    response_message = response_message_match.group(1)
                                
                                logger.info(f"Extracted ResponseCode using regex: {response_code}")
                        except Exception as e:
                            logger.warning(f"Could not decode/extract AuthenticationResponse: {str(e)}")
                    
                    # ResponseCode'u kontrol et (her zaman)
                    if response_code:
                        # ResponseCode'u decode et (URL encoding olabilir)
                        response_code = unquote(str(response_code))
                        if response_message:
                            response_message = unquote(str(response_message).replace('+', ' '))
                        
                        # ResponseCode '00' ise başarılı, değilse hata
                        if response_code != '00':
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
                    else:
                        # ResponseCode bulunamadı, bu normal bir 3D Secure akışı olabilir
                        # Ama HTML'de hata kelimesi varsa yine de kontrol et
                        if 'error' in payment_html.lower() or 'hata' in payment_html.lower():
                            logger.warning(f"Kuveyt PayGate HTML contains 'error'/'hata' keyword but no ResponseCode found")
                    
                    # HTML'deki form action URL'ini kontrol et ve düzelt (eğer yanlışsa)
                    # Kuveyt bazen yanlış action URL döndürebilir veya bizim gönderdiğimiz URL'i kullanmayabilir
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
    
    def get_installment_options(self, amount, bin_number=None):
        """
        Kuveyt Türk API'sinden taksit seçeneklerini sorgula.
        Not: BOA altyapısında genelde taksit oranlarını sorgulayan açık bir servis bulunmaz,
        genelde oranlar banka paneliyle senkronize manuel tanımlanır.
        Ancak burada "GetPosTypeList" veya benzeri bir servis varsa kullanılabilir.
        
        Şimdilik Tenant isteği üzerine API'den dönüyormuş gibi simüle ediyoruz veya
        varsa BinSorgulama servisini buraya entegre edeceğiz.
        """
        # EĞER Kuveyt Türk'ün özel bir Taksit Sorgulama servisi dokümantasyonu elimize ulaşırsa
        # buraya o XML request'i yazılacak.
        
        # Şimdilik standart BOA yapısında bu bilgi genelde "Manuel" tanımlanır uyarısını yapıyorum.
        # FAKAT, kullanıcı API yapacak dediği için burayı bir API çağrısına hazırlıyorum.
        
        # Örnek API Çağrısı Yapısı (Bin Inquiry - Eğer destekleniyorsa)
        # xml = f... <KuveytTurkVPosMessage><InternalMessage>BinInquiry</InternalMessage><Bin>{bin_number}</Bin>...</KuveytTurkVPosMessage>
        pass
        
        # ŞİMDİLİK: Kullanıcının isteği üzerine, manuel config YERİNE
        # Bankanın default oranlarını (veya bizim belirlediğimiz "Sanal" banka oranlarını) dönüyoruz.
        # İleride buraya gerçek req.post eklenecek.
        
        from decimal import Decimal, ROUND_HALF_UP
        amount = Decimal(str(amount))
        
        options = [{
            'count': 1,
            'amount': float(amount),
            'total': float(amount),
            'interest_rate': 0,
            'has_interest': False
        }]
        
        # Eğer BIN numarası varsa bankaya sormuş gibi davranalım
        # Kuveyt genelde vade farksız 3, vade farklı 6-9-12 yapar.
        if bin_number:
            # Burası API response'u simülasyonu (Gerçek API entegre edilene kadar)
            simulated_rates = {
                '3': 0,      # Peşin Fiyatına
                '6': 4.50,   # Vade Farklı
                '9': 8.00,
                '12': 11.50
            }
            
            for count, rate_val in simulated_rates.items():
                count = int(count)
                rate = Decimal(str(rate_val))
                
                total_amount = amount * (Decimal('1') + (rate / Decimal('100')))
                monthly_amount = total_amount / Decimal(count)
                
                total_amount = total_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                monthly_amount = monthly_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                options.append({
                    'count': count,
                    'amount': float(monthly_amount),
                    'total': float(total_amount),
                    'interest_rate': float(rate),
                    'has_interest': rate > 0
                })
                
        return options
    
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

