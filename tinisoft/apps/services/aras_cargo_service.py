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
    # SetOrder servisi için ASMX endpoint'leri
    DEFAULT_SETORDER_API_ENDPOINT = "https://customerws.araskargo.com.tr/arascargoservice.asmx"
    DEFAULT_SETORDER_TEST_ENDPOINT = "https://customerservicestest.araskargo.com.tr/arascargoservice/arascargoservice.asmx"
    
    # Eski endpoint'ler (SetDataXML için - şimdilik kullanılmıyor)
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
            # SetOrder için ayrı credentials
            # Öncelik sırası: setorder config > api_key/api_secret > boş
            setorder_config = config.get('setorder', {})
            
            # SetOrder username: setorder.username > api_key
            username = setorder_config.get('username') or integration.get_api_key() or ''
            
            # SetOrder password: setorder.password > api_secret
            password = setorder_config.get('password') or integration.get_api_secret() or ''
            
            logger.info(f"SetOrder credentials - username: {username}, password: {'*' * len(password) if password else 'EMPTY'}")
            logger.info(f"SetOrder config - setorder_config: {setorder_config}")
            logger.info(f"SetOrder config - api_key from integration: {integration.get_api_key()[:20] if integration.get_api_key() else 'EMPTY'}...")
            
            return {
                'user_name': username,  # SetOrder için user_name (Order içinde UserName)
                'password': password,  # SetOrder için password (Order içinde Password)
                'username': username,  # SetOrder için userName (orderInfo dışında)
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
    def _build_setorder_soap_envelope(shipment_data: Dict, credentials: Dict, order=None) -> str:
        """
        SetOrder servisi için SOAP envelope oluştur (ASMX servisi).
        
        Format:
        <SetOrder xmlns="http://tempuri.org/">
          <orderInfo>
            <Order>
              <UserName>...</UserName>
              <Password>...</Password>
              <ReceiverName>...</ReceiverName>
              ...
            </Order>
          </orderInfo>
          <userName>...</userName>
          <password>...</password>
        </SetOrder>
        
        Args:
            shipment_data: Gönderi bilgileri
            credentials: API credentials (user_name, password, customer_code)
        
        Returns:
            str: SOAP XML envelope
        """
        # SOAP Envelope
        envelope = ET.Element('soap:Envelope')
        envelope.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        envelope.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
        envelope.set('xmlns:soap', 'http://schemas.xmlsoap.org/soap/envelope/')
        
        # Body
        body = ET.SubElement(envelope, 'soap:Body')
        
        # SetOrder
        set_order = ET.SubElement(body, 'SetOrder')
        set_order.set('xmlns', 'http://tempuri.org/')
        
        # orderInfo
        order_info = ET.SubElement(set_order, 'orderInfo')
        
        # Order (XML element)
        order_xml = ET.SubElement(order_info, 'Order')
        
        # Field mapping: shipment_data -> SetOrder XML fields
        field_mapping = {
            'orderNumber': 'IntegrationCode',  # Sipariş numarası (M.Ö.K) - MAX 32 karakter
            'invoiceNumber': 'InvoiceNumber',  # Fatura numarası - MAX 20 karakter
            'receiverName': 'ReceiverName',
            'receiverAddress': 'ReceiverAddress',
            'receiverPhone': 'ReceiverPhone1',
            'receiverPhone2': 'ReceiverPhone2',
            'receiverPhone3': 'ReceiverPhone3',
            'receiverCity': 'ReceiverCityName',
            'receiverState': 'ReceiverTownName',
            'weight': 'Weight',
            'desi': 'VolumetricWeight',
            'pieceCount': 'PieceCount',
            'content': 'Description',
        }
        
        # Order içine UserName ve Password ekle (SetOrder dokümantasyonuna göre gerekli olabilir)
        if credentials:
            # SetOrder için user_name ve password kullan
            user_name = credentials.get('user_name') or credentials.get('username', '')
            password = credentials.get('password', '')
            
            logger.info(f"SetOrder Order içinde UserName: {user_name}, Password: {'*' * len(password) if password else 'EMPTY'}")
            
            user_name_elem = ET.SubElement(order_xml, 'UserName')
            user_name_elem.text = str(user_name)
            
            password_elem = ET.SubElement(order_xml, 'Password')
            password_elem.text = str(password)
        
        # Gönderi bilgilerini ekle
        for key, value in shipment_data.items():
            xml_field = field_mapping.get(key, key)
            if value is not None and value != '':
                # PieceCount ve PieceDetails özel işlem gerektirir
                if xml_field == 'PieceCount':
                    continue  # PieceCount'u sonra ekleyeceğiz (PieceDetails ile birlikte)
                element = ET.SubElement(order_xml, xml_field)
                element.text = str(value).strip()
        
        # PieceCount ekle (PieceDetails olmadan)
        # NOT: PieceDetails gönderdiğimizde "barcode bilgisi eksik" hatası alıyoruz
        # Şimdilik sadece PieceCount gönderelim, PieceDetails'i kaldıralım
        piece_count = shipment_data.get('pieceCount', '1')
        try:
            piece_count_int = int(piece_count)
        except (ValueError, TypeError):
            piece_count_int = 1
        
        # PieceCount ekle
        piece_count_elem = ET.SubElement(order_xml, 'PieceCount')
        piece_count_elem.text = str(piece_count_int)
        
        # PieceDetails ekle - Her order item için gerçek ürün barcode'u gönder
        piece_details = ET.SubElement(order_xml, 'PieceDetails')
        
        # Order items'dan ürün barcode'larını al
        order_items = order.items.all()
        total_items_count = sum(item.quantity for item in order_items)
        
        # Her order item için quantity kadar PieceDetail oluştur
        piece_index = 0
        # Toplam ağırlık ve desi'yi parça sayısına böl (her parça için eşit dağıt)
        total_weight_float = float(shipment_data.get('weight', '1.0'))
        total_desi_float = float(shipment_data.get('desi', '3.0'))
        weight_per_piece = total_weight_float / piece_count_int if piece_count_int > 0 else total_weight_float
        desi_per_piece = total_desi_float / piece_count_int if piece_count_int > 0 else total_desi_float
        
        for order_item in order_items:
            # Ürün barcode'unu al (product.barcode veya product.sku veya product_sku)
            barcode = ''
            if order_item.product:
                barcode = order_item.product.barcode or order_item.product.sku or ''
            if not barcode:
                barcode = order_item.product_sku or ''
            if not barcode:
                # Barcode yoksa, IntegrationCode + parça numarası kullan
                barcode = f"{integration_code}-{piece_index+1}"
            
            # Her quantity için bir PieceDetail oluştur
            for qty_index in range(order_item.quantity):
                piece_detail = ET.SubElement(piece_details, 'PieceDetail')
                
                # Barcode ekle (gerçek ürün barcode'u) - Farklı field isimlerini dene
                # Belki BarcodeCode veya PieceBarcode olabilir, ama önce Barcode deneyelim
                barcode_elem = ET.SubElement(piece_detail, 'Barcode')
                barcode_elem.text = barcode[:50] if barcode else f"{integration_code}-{piece_index+1}"
                
                # Weight ve Desi ekle (her parça için)
                weight_elem = ET.SubElement(piece_detail, 'Weight')
                weight_elem.text = str(round(weight_per_piece, 2))
                
                desi_elem = ET.SubElement(piece_detail, 'Desi')
                desi_elem.text = str(round(desi_per_piece, 2))
                
                piece_index += 1
        
        # SetOrder parametreleri (orderInfo dışında)
        if credentials:
            # SetOrder için userName ve password (orderInfo dışında)
            user_name = credentials.get('user_name') or credentials.get('username', '')
            password = credentials.get('password', '')
            
            logger.debug(f"SetOrder orderInfo dışında userName: {user_name[:10] if user_name else 'EMPTY'}..., password: {'*' * len(password) if password else 'EMPTY'}")
            
            user_name_param = ET.SubElement(set_order, 'userName')
            user_name_param.text = str(user_name)
            
            password_param = ET.SubElement(set_order, 'password')
            password_param.text = str(password)
        
        # XML string'e çevir
        xml_str = ET.tostring(envelope, encoding='utf-8', method='xml')
        # Pretty print için minidom kullan
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
    
    @staticmethod
    def _make_setorder_request(
        integration: IntegrationProvider,
        endpoint: str,
        shipment_data: Dict,
        credentials: Dict,
        order
    ) -> Dict[str, Any]:
        """
        SetOrder ASMX servisine istek gönder.
        
        Args:
            integration: IntegrationProvider instance
            endpoint: SetOrder endpoint URL
            shipment_data: Gönderi bilgileri
            credentials: API credentials
        
        Returns:
            dict: API response
        """
        # SOAP XML oluştur
        soap_xml = ArasCargoService._build_setorder_soap_envelope(shipment_data, credentials, order)
        
        # SOAP Action header (SetOrder için)
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'http://tempuri.org/SetOrder',
        }
        
        try:
            logger.info(f"Aras Kargo SetOrder request to {endpoint}")
            logger.info(f"SetOrder credentials being used - username: {credentials.get('username', '')[:30] if credentials.get('username') else 'EMPTY'}, password: {'*' * len(credentials.get('password', '')) if credentials.get('password') else 'EMPTY'}")
            logger.info(f"SOAP XML (full):\n{soap_xml}")
            
            response = requests.post(
                url=endpoint,
                data=soap_xml.encode('utf-8'),
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            # SOAP response'u parse et
            parsed_data = ArasCargoService._parse_setorder_response(response.text)
            
            # Debug için response'u logla
            logger.info(f"Aras Kargo SetOrder response: {response.status_code}")
            logger.debug(f"SetOrder parsed data: {parsed_data}")
            logger.debug(f"SetOrder raw response: {response.text[:500]}")
            
            result = {
                'success': True,
                'data': parsed_data,
                'status_code': response.status_code,
                'raw_response': response.text,
            }
            
            # Son kullanım zamanını güncelle
            integration.last_used_at = timezone.now()
            integration.last_error = ''
            integration.save(update_fields=['last_used_at', 'last_error'])
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Aras Kargo SetOrder error: {str(e)}"
            
            if hasattr(e, 'response') and e.response is not None:
                response_text = e.response.text[:1000] if e.response.text else 'No response body'
                logger.error(f"{error_msg}\nResponse body: {response_text}")
                logger.error(f"Request SOAP XML: {soap_xml}")
            else:
                logger.error(error_msg)
            
            integration.last_error = error_msg
            integration.save(update_fields=['last_error'])
            
            return {
                'success': False,
                'error': error_msg,
            }
        except Exception as e:
            error_msg = f"Unexpected error in Aras Kargo SetOrder: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            integration.last_error = error_msg
            integration.save(update_fields=['last_error'])
            
            return {
                'success': False,
                'error': error_msg,
            }
    
    @staticmethod
    def _parse_setorder_response(xml_response: str) -> Dict[str, Any]:
        """
        SetOrder SOAP response'u parse et.
        
        Format:
        <SetOrderResponse>
          <SetOrderResult>
            <OrderResultInfo>
              <ResultCode>string</ResultCode>
              <ResultMessage>string</ResultMessage>
              <InvoiceKey>string</InvoiceKey>
              <OrgReceiverCustId>string</OrgReceiverCustId>
            </OrderResultInfo>
          </SetOrderResult>
        </SetOrderResponse>
        
        Args:
            xml_response: SOAP XML response string
        
        Returns:
            dict: Parsed data
        """
        try:
            root = ET.fromstring(xml_response)
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'tem': 'http://tempuri.org/'
            }
            
            # Body içindeki SetOrderResponse'u bul
            body = root.find('.//soap:Body', namespaces)
            if body is not None:
                set_order_response = body.find('.//tem:SetOrderResponse', namespaces)
                if set_order_response is not None:
                    result = {}
                    # SetOrderResult içindeki OrderResultInfo'yu bul
                    set_order_result = set_order_response.find('.//tem:SetOrderResult', namespaces)
                    if set_order_result is not None:
                        order_result_info = set_order_result.find('.//tem:OrderResultInfo', namespaces)
                        if order_result_info is not None:
                            for child in order_result_info:
                                tag = child.tag.split('}')[-1]
                                result[tag] = child.text if child.text else ''
                    return result
            return {}
        except Exception as e:
            logger.error(f"Error parsing SetOrder SOAP response: {str(e)}")
            return {}
    
    @staticmethod
    def _build_shipment_query_info_xml(data: Dict) -> str:
        """
        SetDataXML için queryInfo XML parametresini oluştur.
        
        WSDL'e göre SetDataXML, GetQueryDS ile aynı formatı kullanır:
        - loginInfo: Kullanıcı bilgileri
        - queryInfo: Gönderi bilgileri (XML string)
        
        ÖNEMLI: SetDataXML için queryInfo formatı Aras Kargo dokümantasyonunda belirtilmiş olmalı.
        Bu method tahmini field isimlerini kullanıyor. Gerçek field isimleri ve format için
        Aras Kargo teknik desteğiyle iletişime geçilmesi gerekiyor.
        
        Args:
            data: Gönderi bilgileri (orderNumber, receiverName, vb.)
        
        Returns:
            str: QueryInfo XML string
        """
        # QueryInfo XML oluştur (SetDataXML için gönderi bilgileri)
        # Not: Bu format tahminidir, Aras Kargo dokümantasyonuna göre güncellenmelidir
        query_info = ET.Element('QueryInfo')
        
        # Field mapping: Python field -> Aras Kargo field
        # Kaynak: "Müşteri Servis Entegrasyon Dökümanı.docx" - GetDispatch servis field isimleri
        field_mapping = {
            'orderNumber': 'orgReceiverCustId',  # Müşteri Özel kodu (Sipariş kodu) - M.Ö.K
            'receiverName': 'receiverCustName',  # Alıcı Adı
            'receiverPhone': 'receiverPhone1',  # Telefon-1
            'receiverAddress': 'receiverAddress',  # Alıcı Adresi
            'receiverCity': 'cityName',  # İl – Şehir Adı
            'receiverState': 'townName',  # İlçe Adı
            'weight': 'kg',  # Ürün Kg (Double 6,2)
            'pieceCount': 'cargoCount',  # Sevkedilen Kargo Sayısı (Integer 2)
            'content': 'description',  # Açıklama (String 255)
            'desi': 'desi',  # Ürün Desi (Double 6,2)
            # Opsiyonel alanlar:
            'receiverPhone2': 'receiverPhone2',  # Telefon-2 (String 15)
            'receiverPhone3': 'receiverPhone3',  # Telefon-3 (String 15)
            'specialField1': 'specialField1',  # Özel Alan - 1 (String 500)
            'specialField2': 'specialField2',  # Özel Alan – 2 (String 500)
            'specialField3': 'specialField3',  # Özel Alan – 3 (String 500)
        }
        
        # Zorunlu field'lar (tahmini)
        required_fields = ['IntegrationCode', 'GondericiAdi', 'AliciAdi', 'AliciTelefon', 'AliciAdres', 'AliciSehir']
        
        for key, value in data.items():
            if value is not None and value != '':
                # Field mapping varsa kullan, yoksa orijinal key'i kullan
                xml_field_name = field_mapping.get(key, key)
                element = ET.SubElement(query_info, xml_field_name)
                # String değeri temizle (XML güvenliği için)
                clean_value = str(value).strip()
                element.text = clean_value
        
        xml_str = ET.tostring(query_info, encoding='utf-8', method='xml')
        result = xml_str.decode('utf-8')
        
        # Debug için log
        logger.debug(f"SetDataXML queryInfo XML: {result}")
        
        return result
    
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
                
                # Request SOAP XML'ini de logla (500 hatası için)
                logger.error(f"Request SOAP XML: {soap_xml}")
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
        Gönderi oluştur (SetDataXML API kullanarak).
        
        NOT: SetDataXML için queryInfo formatı Aras Kargo dokümantasyonunda belirtilmiş olmalı.
        Şu an kullandığımız format tahminidir ve Aras Kargo teknik desteğinden doğrulanmalıdır.
        
        SetDataXML API ile gönderi oluşturur ve takip linki döndürür.
        Müşteri bu link ile kargo durumunu takip edebilir.
        
        ÖNEMLİ: SetDataXML queryInfo formatı için Aras Kargo'dan dokümantasyon alınması gerekiyor.
        
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
        
        # SetOrder endpoint'i (ASMX servisi)
        # Öncelik sırası:
        # 1. integration.api_endpoint (eğer .asmx ile bitiyorsa)
        # 2. config.setorder.endpoint
        # 3. Test/Production moduna göre default endpoint
        
        setorder_endpoint = None
        
        # Önce api_endpoint'i kontrol et (canlı/production için)
        if integration.api_endpoint and integration.api_endpoint.endswith('.asmx'):
            setorder_endpoint = integration.api_endpoint
            logger.info(f"SetOrder endpoint from api_endpoint: {setorder_endpoint}")
        # Test modundaysa test_endpoint'i kontrol et
        elif integration.status == IntegrationProvider.Status.TEST_MODE and integration.test_endpoint and integration.test_endpoint.endswith('.asmx'):
            setorder_endpoint = integration.test_endpoint
            logger.info(f"SetOrder endpoint from test_endpoint: {setorder_endpoint}")
        # Config'de tanımlı endpoint
        elif integration.config.get('setorder', {}).get('endpoint'):
            setorder_endpoint = integration.config.get('setorder', {}).get('endpoint')
            # Eğer config'de eksik endpoint varsa (sadece host girilmişse), ignore et
            if setorder_endpoint.count('/') < 3 or not setorder_endpoint.endswith('.asmx'):
                logger.warning(f"Config'de eksik endpoint bulundu (sadece host?), SetOrder için default endpoint kullanılacak: {setorder_endpoint}")
                setorder_endpoint = None
        
        # Default endpoint (eğer hala endpoint yoksa)
        if not setorder_endpoint:
            if integration.status == IntegrationProvider.Status.TEST_MODE:
                # Test endpoint - SetOrder için ASMX servisi
                setorder_endpoint = ArasCargoService.DEFAULT_SETORDER_TEST_ENDPOINT
            else:
                # Production endpoint - SetOrder için ASMX servisi
                setorder_endpoint = ArasCargoService.DEFAULT_SETORDER_API_ENDPOINT
        
        logger.info(f"SetOrder endpoint: {setorder_endpoint}")
        
        # Gönderi bilgilerini hazırla (SetDataXML API formatına göre)
        # ÖNEMLI: SetDataXML için queryInfo içindeki field isimleri ve format Aras Kargo dokümantasyonunda belirtilmiş olmalı
        # Şu an kullandığımız field mapping tahminidir ve test edilmelidir
        
        # Gönderen adresi bilgileri (integration config'den veya tenant'tan)
        sender_address_config = integration.config.get('sender_address', {})
        
        # Ağırlık ve desi hesaplama
        total_weight = float(order.items.aggregate(total_weight=models.Sum('product__weight'))['total_weight'] or 1.0)
        total_weight = max(0.1, total_weight)
        
        # Desi hesaplama (basit formül: kg * 3, gerçekte hacim bazlı olmalı)
        desi = total_weight * 3.0  # Basit hesaplama, gerçekte hacim gerekli
        
        # SetOrder servisi için field isimleri (ASMX servisi formatı)
        # IntegrationCode: En az 2, en fazla 32 karakter olmalı (Aras Kargo kısıtlaması)
        integration_code = order.order_number[:32] if len(order.order_number) > 32 else order.order_number
        if len(integration_code) < 2:
            # Eğer order_number çok kısaysa, order ID'nin son kısmını kullan
            integration_code = str(order.id)[:32] if len(str(order.id)) <= 32 else str(order.id)[-32:]
        
        # InvoiceNumber: En fazla 20 karakter olmalı (Aras Kargo kısıtlaması)
        # Eğer invoice number yoksa, IntegrationCode'un ilk 20 karakterini kullan
        invoice_number = integration_code[:20] if integration_code else str(order.id)[:20]
        
        shipment_data = {
            'orderNumber': integration_code,  # IntegrationCode olarak map edilecek - Müşteri özel kodu (M.Ö.K) - MAX 32 karakter
            'invoiceNumber': invoice_number,  # InvoiceNumber - Müşteri Fatura Numarası - MAX 20 karakter
            'receiverName': f"{shipping_address.get('first_name', '').strip()} {shipping_address.get('last_name', '').strip()}".strip()[:100],  # ReceiverName
            'receiverPhone': shipping_address.get('phone', '').strip()[:32],  # ReceiverPhone1
            'receiverAddress': shipping_address.get('address_line_1', '').strip()[:250],  # ReceiverAddress - ZORUNLU
            'receiverCity': shipping_address.get('city', '').strip()[:32],  # ReceiverCityName - ZORUNLU
            'weight': str(total_weight),  # Weight (string format) - ZORUNLU
            'desi': str(round(desi, 2)),  # VolumetricWeight (string format, desi)
            # PieceCount: Order items'ın toplam quantity'si (her item için quantity kadar parça)
            'pieceCount': str(min(99, max(1, sum(item.quantity for item in order.items.all())))),  # Toplam parça sayısı
            'content': ', '.join([item.product.name for item in order.items.all()[:3]])[:255],  # Description
        }
        
        # İlçe (townName) - opsiyonel ama ekleyelim
        if shipping_address.get('state'):
            shipment_data['receiverState'] = shipping_address.get('state', '').strip()[:32]  # townName (max 32)
        
        # Opsiyonel alanlar (eğer varsa)
        if shipping_address.get('phone2'):
            shipment_data['receiverPhone2'] = shipping_address.get('phone2', '').strip()[:15]
        
        if shipping_address.get('phone3'):
            shipment_data['receiverPhone3'] = shipping_address.get('phone3', '').strip()[:15]
        
        # Zorunlu alanların boş olmadığını kontrol et
        required_fields = {
            'receiverAddress': 'Alıcı adresi',
            'receiverCity': 'Alıcı şehir',
            'weight': 'Ağırlık',
            'pieceCount': 'Kargo sayısı'
        }
        
        missing_fields = []
        for field, field_name in required_fields.items():
            if field not in shipment_data or not shipment_data[field] or (isinstance(shipment_data[field], str) and not shipment_data[field].strip()):
                missing_fields.append(field_name)
                logger.warning(f"SetDataXML için zorunlu alan eksik: {field} ({field_name})")
        
        if missing_fields:
            return {
                'success': False,
                'error': f'Gönderi bilgileri eksik: {", ".join(missing_fields)}. Lütfen sipariş adres bilgilerini kontrol edin.',
            }
        
        # Boş değerleri temizle (sadece string field'lar için)
        # Ama zorunlu numeric field'ları (weight, pieceCount) koru
        cleaned_data = {}
        for key, value in shipment_data.items():
            if isinstance(value, (int, float)):
                cleaned_data[key] = value
            elif value and str(value).strip():
                cleaned_data[key] = value
            # Boş string'leri atla (opsiyonel alanlar için)
        
        shipment_data = cleaned_data
        
        # Boş değerleri temizle
        shipment_data = {k: v for k, v in shipment_data.items() if v and str(v).strip()}
        
        # SetOrder için SOAP request gönder (ASMX servisi)
        response = ArasCargoService._make_setorder_request(
            integration=integration,
            endpoint=setorder_endpoint,
            shipment_data=shipment_data,
            credentials=setorder_credentials,
            order=order
        )
        
        if response.get('success'):
            data = response.get('data', {})
            logger.info(f"SetOrder response data: {data}")
            
            # SetOrder response'dan tracking number ve label URL'i al
            # ResultCode ve ResultMessage kontrolü yap
            result_code = data.get('ResultCode', '')
            result_message = data.get('ResultMessage', '')
            
            # ResultCode boşsa veya 0 ise başarılı, diğerleri hata
            if result_code and result_code != '0' and result_code != '' and result_code.lower() not in ['0', 'success', 'ok']:
                # Hata varsa
                logger.warning(f"SetOrder hatası: {result_message} (Code: {result_code})")
                return {
                    'success': False,
                    'error': f"Aras Kargo hatası: {result_message} (Code: {result_code})",
                }
            
            # InvoiceKey muhtemelen takip numarası veya invoice key
            # Eğer InvoiceKey yoksa, OrgReceiverCustId bizim gönderdiğimiz order_number (M.Ö.K)
            tracking_number = data.get('InvoiceKey') or data.get('trackingNumber') or data.get('tracking_number') or ''
            org_receiver_cust_id = data.get('OrgReceiverCustId', '')
            barcode = ''  # SetOrder response'da barkod olmayabilir
            
            logger.info(f"SetOrder tracking_number: {tracking_number}, OrgReceiverCustId: {org_receiver_cust_id}")
            
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

