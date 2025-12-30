"""
Aras Kargo XML/SOAP Service.
Integration modelinden API bilgilerini alır ve kullanır.
Aras Kargo XML Servisleri kullanır (SOAP).
"""
import requests
import logging
from typing import Dict, Optional, Any
from django.utils import timezone
from apps.models import IntegrationProvider, Order
from django.db import models
import xml.etree.ElementTree as ET
from xml.dom import minidom

logger = logging.getLogger(__name__)


class ArasCargoService:
    """Aras Kargo XML/SOAP servisi."""
    
    # Aras Kargo XML Servis endpoint'leri
    # WSDL sayfasından doğrulanan endpoint'ler:
    # Test: https://customerservicestest.araskargo.com.tr/ArasCargoIntegrationService.svc (HTTPS)
    # WSDL: https://customerservicestest.araskargo.com.tr/ArasCargoIntegrationService.svc?wsdl
    # Canlı: http://customerservices.araskargo.com.tr/ArasCargoCustomerIntegrationService/ArasCargoIntegrationService.svc
    DEFAULT_API_ENDPOINT = "http://customerservices.araskargo.com.tr/ArasCargoCustomerIntegrationService/ArasCargoIntegrationService.svc"
    DEFAULT_TEST_ENDPOINT = "https://customerservicestest.araskargo.com.tr/ArasCargoIntegrationService.svc"
    
    @staticmethod
    def get_integration(tenant) -> Optional[IntegrationProvider]:
        """Tenant için Aras Kargo entegrasyonunu getir."""
        try:
            integration = IntegrationProvider.objects.get(
                tenant=tenant,
                provider_type=IntegrationProvider.ProviderType.ARAS,
                is_deleted=False
            )
            
            # Aktif veya test modunda olmalı
            if integration.status not in [IntegrationProvider.Status.ACTIVE, IntegrationProvider.Status.TEST_MODE]:
                logger.warning(f"Aras Kargo integration is not active for tenant {tenant.slug}")
                return None
            
            return integration
        except IntegrationProvider.DoesNotExist:
            logger.warning(f"Aras Kargo integration not found for tenant {tenant.slug}")
            return None
        except Exception as e:
            logger.error(f"Error getting Aras Kargo integration: {str(e)}")
            return None
    
    @staticmethod
    def _get_api_credentials(integration: IntegrationProvider, service_type: str = 'query') -> Dict[str, str]:
        """
        API credentials'ları al.
        
        Args:
            integration: IntegrationProvider instance
            service_type: 'query' (GetQueryDS için) veya 'setorder' (SetOrder için)
        """
        config = integration.config or {}
        
        if service_type == 'setorder':
            # SetOrder için ayrı credentials (email'den gelen bilgiler)
            setorder_config = config.get('setorder', {})
            return {
                'username': setorder_config.get('username') or integration.get_api_key(),
                'password': setorder_config.get('password') or integration.get_api_secret(),
                'customer_code': setorder_config.get('customer_code') or config.get('customer_code', ''),
                'customer_username': config.get('customer_username', ''),  # Müşteri Kullanıcı Adı
                'customer_password': config.get('customer_password', ''),  # Müşteri Şifre
                'branch': config.get('branch', ''),  # Şube
            }
        else:
            # Query servisleri için (GetQueryDS)
            query_config = config.get('query', {})
            return {
                'username': query_config.get('username') or integration.get_api_key(),
                'password': query_config.get('password') or integration.get_api_secret(),
                'customer_code': query_config.get('customer_code') or config.get('customer_code', ''),
                'customer_username': config.get('customer_username', ''),  # Müşteri Kullanıcı Adı
                'customer_password': config.get('customer_password', ''),  # Müşteri Şifre
            }
    
    @staticmethod
    def get_tracking_url(tenant, tracking_reference: str, tracking_type: str = 'order_number') -> str:
        """
        Aras Kargo takip URL'i oluştur.
        
        Args:
            tenant: Tenant instance
            tracking_reference: Takip referansı (takip numarası, sipariş numarası veya barkod kodu)
            tracking_type: Takip tipi - 'tracking_number', 'order_number', 'barcode'
                - 'tracking_number': 13 haneli kargo takip numarası (code parametresi)
                - 'order_number': Sipariş numarası/referans numarası (accountid, sifre, alici_kod parametreleri)
                - 'barcode': 20 haneli barkod kodu (Cargo_Code parametresi)
        
        Returns:
            str: Tracking URL
        """
        integration = ArasCargoService.get_integration(tenant)
        if not integration:
            return ''
        
        if tracking_type == 'tracking_number':
            # Format 1: Kargo Takip Numarası ile (13 haneli kod)
            # http://kargotakip.araskargo.com.tr/mainpage.aspx?code=3513773163316
            return f"http://kargotakip.araskargo.com.tr/mainpage.aspx?code={tracking_reference}"
        
        elif tracking_type == 'order_number':
            # Format 2: Sipariş Numarası ile (accountid, alici_kod)
            # Yeni format: https://kargotakip.araskargo.com.tr/mainpage.aspx?accountid=XXX&alici_kod=ZZZ
            # Eski format (sifre varsa): http://kargotakip.araskargo.com.tr/mainpage.aspx?accountid=XXX&sifre=YYY&alici_kod=ZZZ
            account_id = integration.config.get('account_id', '')
            tracking_password = integration.config.get('tracking_password', '')  # Güvenlik şifresi (opsiyonel)
            
            if not account_id:
                logger.warning("Aras Kargo account_id bulunamadı. Tracking URL oluşturulamadı.")
                return ''
            
            # URL encoding için urllib kullan
            from urllib.parse import quote_plus
            
            # Yeni format: sifre yok, sadece accountid ve alici_kod
            if tracking_password:
                # Eski format: sifre varsa onu da ekle
                return f"https://kargotakip.araskargo.com.tr/mainpage.aspx?accountid={quote_plus(account_id)}&sifre={quote_plus(tracking_password)}&alici_kod={quote_plus(tracking_reference)}"
            else:
                # Yeni format: sifre yok
                return f"https://kargotakip.araskargo.com.tr/mainpage.aspx?accountid={quote_plus(account_id)}&alici_kod={quote_plus(tracking_reference)}"
        
        elif tracking_type == 'barcode':
            # Format 3: Kargo Barkod Kodu ile (20 haneli barkod)
            # http://kargotakip.araskargo.com.tr/yurticigonbil.aspx?Cargo_Code=0805513773163332313
            return f"http://kargotakip.araskargo.com.tr/yurticigonbil.aspx?Cargo_Code={tracking_reference}"
        
        else:
            logger.warning(f"Bilinmeyen tracking_type: {tracking_type}")
            return ''
    
    @staticmethod
    def _get_base_url(integration: IntegrationProvider) -> str:
        """
        Base URL'i al (test veya production).
        
        - Test mode ise: test_endpoint (config) veya DEFAULT_TEST_ENDPOINT
        - Canlı mode ise: api_endpoint (config) veya DEFAULT_API_ENDPOINT
        """
        if integration.status == IntegrationProvider.Status.TEST_MODE:
            # Test modunda test endpoint kullan
            # Önce integration'da tanımlı test_endpoint, yoksa default test endpoint
            return integration.test_endpoint or ArasCargoService.DEFAULT_TEST_ENDPOINT
        else:
            # Canlı modda production endpoint kullan
            # Önce integration'da tanımlı api_endpoint, yoksa default canlı endpoint
            return integration.api_endpoint or ArasCargoService.DEFAULT_API_ENDPOINT
    
    @staticmethod
    def _build_login_info_xml(credentials: Dict) -> str:
        """
        LoginInfo XML parametresini oluştur (Aras Kargo formatına göre).
        
        Args:
            credentials: API credentials (username, password, customer_code)
        
        Returns:
            str: LoginInfo XML string
        """
        login_info = ET.Element('LoginInfo')
        
        username = ET.SubElement(login_info, 'UserName')
        username.text = credentials.get('username', '')
        
        password = ET.SubElement(login_info, 'Password')
        password.text = credentials.get('password', '')
        
        customer_code = ET.SubElement(login_info, 'CustomerCode')
        customer_code.text = credentials.get('customer_code', '')
        
        xml_str = ET.tostring(login_info, encoding='utf-8', method='xml')
        return xml_str.decode('utf-8')
    
    @staticmethod
    def _build_query_info_xml(query_type: int, query_params: Dict) -> str:
        """
        QueryInfo XML parametresini oluştur (Aras Kargo formatına göre).
        
        Args:
            query_type: QueryType değeri (1-102 arası)
            query_params: Query parametreleri (IntegrationCode, Date, vb.)
        
        Returns:
            str: QueryInfo XML string
        """
        query_info = ET.Element('QueryInfo')
        
        query_type_elem = ET.SubElement(query_info, 'QueryType')
        query_type_elem.text = str(query_type)
        
        # Diğer parametreleri ekle
        for key, value in query_params.items():
            if value is not None and value != '':
                param = ET.SubElement(query_info, key)
                param.text = str(value)
        
        xml_str = ET.tostring(query_info, encoding='utf-8', method='xml')
        return xml_str.decode('utf-8')
    
    @staticmethod
    def _build_soap_envelope(service_method: str, credentials: Dict, data: Dict) -> str:
        """
        SOAP XML envelope oluştur.
        
        Aras Kargo API'si için SOAP request oluşturur.
        - GetQueryDS, GetQueryXML, GetQueryJSON: loginInfo ve queryInfo parametreleri
        - SetOrder: loginInfo ve orderInfo parametreleri (farklı format)
        
        Args:
            service_method: Service metod adı (örn: GetQueryDS, SetOrder)
            credentials: API credentials (username, password, customer_code)
            data: Method parametreleri
        
        Returns:
            str: SOAP XML string
        """
        # GetQueryDS ve SetDataXML için mevcut format (WSDL'e göre aynı format)
        # SOAP Envelope oluştur
        envelope = ET.Element('soap:Envelope')
        envelope.set('xmlns:soap', 'http://schemas.xmlsoap.org/soap/envelope/')
        envelope.set('xmlns:tem', 'http://tempuri.org/')
        
        # Body
        body = ET.SubElement(envelope, 'soap:Body')
        
        # Service Method
        method = ET.SubElement(body, f'tem:{service_method}')
        
        # LoginInfo parametresi (XML string olarak)
        login_info_xml = ArasCargoService._build_login_info_xml(credentials)
        login_info_param = ET.SubElement(method, 'tem:loginInfo')
        login_info_param.text = login_info_xml
        
        # QueryInfo parametresi (XML string olarak)
        # SetDataXML için gönderi bilgileri, GetQueryDS için query parametreleri
        if service_method == 'SetDataXML':
            # SetDataXML için gönderi bilgilerini queryInfo olarak gönder
            # queryInfo içinde gönderi bilgileri XML formatında olmalı
            query_info_xml = ArasCargoService._build_shipment_query_info_xml(data)
        else:
            # GetQueryDS, GetQueryXML, GetQueryJSON için query parametreleri
            query_type = data.get('query_type', 1)
            query_params = data.get('query_params', {})
            query_info_xml = ArasCargoService._build_query_info_xml(query_type, query_params)
        
        query_info_param = ET.SubElement(method, 'tem:queryInfo')
        query_info_param.text = query_info_xml
        
        # XML string'e çevir
        xml_str = ET.tostring(envelope, encoding='utf-8', method='xml')
        # Pretty print için minidom kullan
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
    
    @staticmethod
    def _build_shipment_query_info_xml(data: Dict) -> str:
        """
        SetDataXML için queryInfo XML parametresini oluştur.
        
        WSDL'e göre SetDataXML, GetQueryDS ile aynı formatı kullanır:
        - loginInfo: Kullanıcı bilgileri
        - queryInfo: Gönderi bilgileri (XML string)
        
        Args:
            data: Gönderi bilgileri (orderNumber, receiverName, vb.)
        
        Returns:
            str: QueryInfo XML string
        """
        # QueryInfo XML oluştur (SetDataXML için gönderi bilgileri)
        # Not: Gerçek field isimleri Aras Kargo dokümantasyonunda olabilir
        query_info = ET.Element('QueryInfo')
        
        # Gönderi bilgilerini XML'e çevir
        for key, value in data.items():
            if value is not None and value != '':
                element = ET.SubElement(query_info, key)
                element.text = str(value)
        
        xml_str = ET.tostring(query_info, encoding='utf-8', method='xml')
        return xml_str.decode('utf-8')
    
    @staticmethod
    def _parse_soap_response(xml_response: str) -> Dict[str, Any]:
        """
        SOAP XML response'u parse et.
        
        Args:
            xml_response: SOAP XML response string
        
        Returns:
            dict: Parsed data
        """
        try:
            root = ET.fromstring(xml_response)
            # SOAP namespace
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'tem': 'http://tempuri.org/'
            }
            
            # Body içindeki response'u bul
            body = root.find('.//soap:Body', namespaces)
            if body is not None:
                # İlk child'ı al (method response)
                response_element = list(body)[0] if list(body) else None
                if response_element is not None:
                    # Tüm child elementleri dict'e çevir
                    result = {}
                    for child in response_element:
                        tag = child.tag.split('}')[-1]  # Namespace'i kaldır
                        result[tag] = child.text if child.text else ''
                        # Nested elements
                        if list(child):
                            result[tag] = {}
                            for sub_child in child:
                                sub_tag = sub_child.tag.split('}')[-1]
                                result[tag][sub_tag] = sub_child.text if sub_child.text else ''
                    return result
            return {}
        except Exception as e:
            logger.error(f"Error parsing SOAP response: {str(e)}")
            return {}
    
    @staticmethod
    def _make_soap_request(
        integration: IntegrationProvider,
        service_method: str,
        data: Optional[Dict] = None,
        credentials: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Aras Kargo SOAP/XML servisine istek gönder.
        
        Args:
            integration: IntegrationProvider instance
            service_method: Service metod adı (GetQueryDS, CreateShipment, vb.)
            data: Method parametreleri
        
        Returns:
            dict: API response
        """
        base_url = ArasCargoService._get_base_url(integration)
        if credentials is None:
            credentials = ArasCargoService._get_api_credentials(integration)
        
        # SOAP XML oluştur
        soap_xml = ArasCargoService._build_soap_envelope(service_method, credentials, data or {})
        
        # SOAP Action header
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': f'http://tempuri.org/IArasCargoIntegrationService/{service_method}',
        }
        
        try:
            logger.info(f"Aras Kargo SOAP request: {service_method} to {base_url}")
            # SOAP XML'i logla (debug için) - ilk 1500 karakter
            logger.debug(f"SOAP XML (first 1500 chars): {soap_xml[:1500]}")
            
            response = requests.post(
                url=base_url,
                data=soap_xml.encode('utf-8'),
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            # SOAP response'u parse et
            parsed_data = ArasCargoService._parse_soap_response(response.text)
            
            result = {
                'success': True,
                'data': parsed_data,
                'status_code': response.status_code,
                'raw_response': response.text,  # Debug için
            }
            
            # Son kullanım zamanını güncelle
            integration.last_used_at = timezone.now()
            integration.last_error = ''
            integration.save(update_fields=['last_used_at', 'last_error'])
            
            logger.info(f"Aras Kargo SOAP response: {response.status_code}")
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Aras Kargo SOAP error: {str(e)}"
            
            # Response body'yi logla (500 hatalarında hata detayları burada olur)
            if hasattr(e, 'response') and e.response is not None:
                response_text = e.response.text[:1000] if e.response.text else 'No response body'
                logger.error(f"{error_msg}\nResponse body: {response_text}")
                logger.error(f"Request SOAP XML: {soap_xml[:1000]}")  # İlk 1000 karakter
            else:
                logger.error(error_msg)
            
            # Hata kaydet
            integration.last_error = error_msg
            integration.save(update_fields=['last_error'])
            
            return {
                'success': False,
                'error': error_msg,
                'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
                'response_body': getattr(e.response, 'text', '')[:500] if hasattr(e, 'response') and e.response else None,
            }
        except Exception as e:
            error_msg = f"Unexpected error in Aras Kargo SOAP: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            integration.last_error = error_msg
            integration.save(update_fields=['last_error'])
            
            return {
                'success': False,
                'error': error_msg,
            }
    
    @staticmethod
    def create_shipment(tenant, order: Order, shipping_address: Dict) -> Dict[str, Any]:
        """
        Gönderi oluştur (SetOrder API kullanarak).
        
        SetOrder API ile gönderi oluşturur ve takip linki döndürür.
        Müşteri bu link ile kargo durumunu takip edebilir.
        
        Args:
            tenant: Tenant instance
            order: Order instance
            shipping_address: Kargo adresi bilgileri
        
        Returns:
            dict: {
                'success': bool,
                'tracking_number': str,
                'tracking_url': str,  # Müşteriye gönderilecek link
                'barcode': str,
                'label_url': str,
                'data': dict
            }
        """
        integration = ArasCargoService.get_integration(tenant)
        if not integration:
            return {
                'success': False,
                'error': 'Aras Kargo entegrasyonu bulunamadı veya aktif değil.',
            }
        
        # SetOrder için credentials al
        setorder_credentials = ArasCargoService._get_api_credentials(integration, 'setorder')
        
        # SetOrder endpoint'i
        # Önce config'de tanımlı endpoint, yoksa test/production moduna göre default endpoint
        setorder_endpoint = integration.config.get('setorder', {}).get('endpoint')
        
        if not setorder_endpoint:
            # Test modundaysa test endpoint, değilse production endpoint
            if integration.status == IntegrationProvider.Status.TEST_MODE:
                # Test endpoint - SetOrder için de aynı endpoint kullanılır (PDF'de belirtilen)
                setorder_endpoint = ArasCargoService.DEFAULT_TEST_ENDPOINT
            else:
                # Production endpoint
                setorder_endpoint = ArasCargoService.DEFAULT_API_ENDPOINT
        
        # Gönderi bilgilerini hazırla (SetOrder API formatına göre)
        # Not: SetOrder API formatı farklı olabilir, gerçek dokümantasyona göre güncellenebilir
        shipment_data = {
            'orderNumber': order.order_number,  # Müşteri özel kodu (M.Ö.K) - takip için kullanılacak
            'senderName': tenant.name,
            'senderPhone': tenant.owner.phone or '',
            'senderAddress': integration.config.get('sender_address', {}).get('address_line_1', ''),
            'senderCity': integration.config.get('sender_address', {}).get('city', ''),
            'senderPostalCode': integration.config.get('sender_address', {}).get('postal_code', ''),
            'receiverName': f"{shipping_address.get('first_name', '')} {shipping_address.get('last_name', '')}",
            'receiverPhone': shipping_address.get('phone', ''),
            'receiverAddress': shipping_address.get('address_line_1', ''),
            'receiverAddress2': shipping_address.get('address_line_2', ''),
            'receiverCity': shipping_address.get('city', ''),
            'receiverState': shipping_address.get('state', ''),
            'receiverPostalCode': shipping_address.get('postal_code', ''),
            'receiverCountry': shipping_address.get('country', 'TR'),
            'weight': float(order.items.aggregate(total_weight=models.Sum('product__weight'))['total_weight'] or 1.0),
            'pieceCount': order.items.count(),
            'content': ', '.join([item.product.name for item in order.items.all()[:3]]),
            'paymentType': 'prepaid',  # Ön ödemeli
            'serviceType': integration.config.get('service_type', 'standard'),
        }
        
        # SetDataXML API metod adı (WSDL'de SetOrder yok, SetDataXML var)
        service_method = integration.config.get('setorder', {}).get('method', 'SetDataXML')
        
        # SetOrder için SOAP request gönder
        # Geçici olarak mevcut _make_soap_request metodunu kullan
        # SetOrder endpoint'i ve credentials'ları override et
        old_endpoint = integration.api_endpoint
        integration.api_endpoint = setorder_endpoint
        
        try:
            response = ArasCargoService._make_soap_request(
                integration=integration,
                service_method=service_method,
                data=shipment_data,
                credentials=setorder_credentials
            )
        finally:
            integration.api_endpoint = old_endpoint
        
        if response.get('success'):
            data = response.get('data', {})
            # Response'dan tracking number ve label URL'i al
            tracking_number = data.get('trackingNumber') or data.get('tracking_number') or data.get('awbNumber') or data.get('KargoTakipNo', '')
            barcode = data.get('barcode') or data.get('barcodeCode') or data.get('cargoCode', '') or data.get('KargoKodu', '')
            
            # Tracking URL oluştur - müşteriye gönderilecek link
            tracking_url = ''
            
            # Öncelik sırası: tracking_number (13 haneli) > barcode (20 haneli) > order_number (M.Ö.K)
            if tracking_number:
                if len(str(tracking_number).strip()) == 13:
                    # 13 haneli takip numarası varsa onu kullan
                    tracking_url = ArasCargoService.get_tracking_url(tenant, str(tracking_number).strip(), 'tracking_number')
                elif len(str(tracking_number).strip()) == 20:
                    # 20 haneli barkod varsa onu kullan
                    tracking_url = ArasCargoService.get_tracking_url(tenant, str(tracking_number).strip(), 'barcode')
            
            # Eğer hala tracking_url yoksa ve barcode varsa onu dene
            if not tracking_url and barcode:
                if len(str(barcode).strip()) == 20:
                    tracking_url = ArasCargoService.get_tracking_url(tenant, str(barcode).strip(), 'barcode')
            
            # Eğer hala tracking_url yoksa order_number (M.Ö.K) ile dene
            if not tracking_url and order.order_number:
                tracking_url = ArasCargoService.get_tracking_url(tenant, order.order_number, 'order_number')
            
            return {
                'success': True,
                'tracking_number': tracking_number,
                'tracking_url': tracking_url,  # ✅ Müşteriye gönderilecek link
                'barcode': barcode,
                'label_url': data.get('labelUrl') or data.get('label_url', ''),
                'data': data,
            }
        else:
            return {
                'success': False,
                'error': response.get('error', 'Gönderi oluşturulamadı.'),
            }
    
    @staticmethod
    def track_shipment(tenant, tracking_reference: str, query_type: int = 1) -> Dict[str, Any]:
        """
        Gönderi takip (GetQueryDS SOAP metodu).
        
        QueryType 1: Müşteri referans bilgisine (Müşteri Özel Kodu) göre belirli bir kargonun bilgisini verir
        
        Args:
            tenant: Tenant instance
            tracking_reference: Takip referansı (IntegrationCode / Müşteri Özel Kodu)
            query_type: QueryType değeri (1 = IntegrationCode ile, diğerleri için dokümantasyona bak)
        
        Returns:
            dict: {
                'success': bool,
                'status': str,
                'events': list,
                'tracking_url': str,
                'data': dict
            }
        """
        integration = ArasCargoService.get_integration(tenant)
        if not integration:
            return {
                'success': False,
                'error': 'Aras Kargo entegrasyonu bulunamadı veya aktif değil.',
            }
        
        # Service metod adı (config'den al veya default)
        service_method = integration.config.get('track_shipment_method', 'GetQueryDS')
        
        # Query parametreleri - QueryType 1 için IntegrationCode gerekli
        query_params = {
            'IntegrationCode': tracking_reference,
        }
        
        # QueryType 2 (tarihe göre) için Date parametresi gerekli
        if query_type == 2:
            from django.utils import timezone
            query_params = {
                'Date': timezone.now().strftime('%Y-%m-%d'),
            }
        
        track_data = {
            'query_type': query_type,
            'query_params': query_params,
        }
        
        # SOAP request gönder
        response = ArasCargoService._make_soap_request(
            integration=integration,
            service_method=service_method,
            data=track_data
        )
        
        if response.get('success'):
            data = response.get('data', {})
            
            # Tracking URL oluştur
            tracking_url = ''
            if tracking_reference:
                # 13 haneli ise tracking_number tipi
                if len(tracking_reference) == 13:
                    tracking_url = ArasCargoService.get_tracking_url(tenant, tracking_reference, 'tracking_number')
                # 20 haneli ise barcode tipi
                elif len(tracking_reference) == 20:
                    tracking_url = ArasCargoService.get_tracking_url(tenant, tracking_reference, 'barcode')
                else:
                    # Diğer durumlarda order_number olarak dene
                    tracking_url = ArasCargoService.get_tracking_url(tenant, tracking_reference, 'order_number')
            
            return {
                'success': True,
                'status': data.get('DURUMU') or data.get('status') or data.get('currentStatus', ''),
                'status_code': data.get('DURUM KODU') or data.get('status_code', ''),
                'tracking_number': data.get('KARGO TAKİP NO') or data.get('TRACKINGNUMBER') or data.get('tracking_number', ''),
                'events': data.get('events') or data.get('trackingEvents', []),
                'tracking_url': tracking_url,
                'data': data,
            }
        else:
            return {
                'success': False,
                'error': response.get('error', 'Takip bilgisi alınamadı.'),
            }
    
    @staticmethod
    def print_label(tenant, tracking_number: str) -> Dict[str, Any]:
        """
        Kargo etiketi yazdır (PrintLabel SOAP metodu).
        
        Args:
            tenant: Tenant instance
            tracking_number: Takip numarası
        
        Returns:
            dict: {
                'success': bool,
                'label_url': str,
                'label_pdf': bytes
            }
        """
        integration = ArasCargoService.get_integration(tenant)
        if not integration:
            return {
                'success': False,
                'error': 'Aras Kargo entegrasyonu bulunamadı veya aktif değil.',
            }
        
        # Service metod adı (config'den al veya default)
        service_method = integration.config.get('print_label_method', 'PrintLabel')
        
        # Label parametreleri
        label_data = {
            'trackingNumber': tracking_number,
        }
        
        # SOAP request gönder
        response = ArasCargoService._make_soap_request(
            integration=integration,
            service_method=service_method,
            data=label_data
        )
        
        if response.get('success'):
            data = response.get('data', {})
            # PDF base64 olarak gelebilir
            label_pdf_base64 = data.get('labelPdf') or data.get('label_pdf') or data.get('pdf', '')
            label_pdf = b''
            if label_pdf_base64:
                import base64
                try:
                    label_pdf = base64.b64decode(label_pdf_base64)
                except:
                    pass
            
            return {
                'success': True,
                'label_url': data.get('labelUrl') or data.get('label_url', ''),
                'label_pdf': label_pdf,
            }
        else:
            return {
                'success': False,
                'error': response.get('error', 'Etiket alınamadı.'),
            }
    
    @staticmethod
    def cancel_shipment(tenant, tracking_number: str) -> Dict[str, Any]:
        """
        Gönderi iptal et (CancelShipment SOAP metodu).
        
        Args:
            tenant: Tenant instance
            tracking_number: Takip numarası
        
        Returns:
            dict: {
                'success': bool,
                'message': str
            }
        """
        integration = ArasCargoService.get_integration(tenant)
        if not integration:
            return {
                'success': False,
                'error': 'Aras Kargo entegrasyonu bulunamadı veya aktif değil.',
            }
        
        # Service metod adı (config'den al veya default)
        service_method = integration.config.get('cancel_shipment_method', 'CancelShipment')
        
        # Cancel parametreleri
        cancel_data = {
            'trackingNumber': tracking_number,
        }
        
        # SOAP request gönder
        response = ArasCargoService._make_soap_request(
            integration=integration,
            service_method=service_method,
            data=cancel_data
        )
        
        if response.get('success'):
            return {
                'success': True,
                'message': 'Gönderi iptal edildi.',
            }
        else:
            return {
                'success': False,
                'error': response.get('error', 'Gönderi iptal edilemedi.'),
            }

