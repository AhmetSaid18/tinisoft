"""
Payment Provider Services - Kuveyt API ve diğer ödeme sağlayıcıları için.
"""
import requests
import logging
from decimal import Decimal
from django.conf import settings

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
    Kuveyt API ödeme sağlayıcısı.
    
    Tenant'ın settings'inde şu bilgiler olmalı:
    - kuwait_api_key: API anahtarı
    - kuwait_api_secret: API secret
    - kuwait_api_endpoint: API endpoint URL (örn: https://api.kuveyt.com/payment)
    """
    
    def __init__(self, tenant, config=None):
        super().__init__(tenant, config)
        self.api_key = self.config.get('api_key') or getattr(settings, 'KUWAIT_API_KEY', '')
        self.api_secret = self.config.get('api_secret') or getattr(settings, 'KUWAIT_API_SECRET', '')
        self.api_endpoint = self.config.get('endpoint') or getattr(settings, 'KUWAIT_API_ENDPOINT', 'https://api.kuveyt.com/payment')
    
    def create_payment(self, order, amount, customer_info):
        """
        Kuveyt API ile ödeme oluştur.
        
        Args:
            order: Order instance
            amount: Ödeme tutarı
            customer_info: {
                'email': str,
                'name': str,
                'phone': str,
                'address': dict
            }
        
        Returns:
            dict: Payment response
        """
        try:
            # Kuveyt API'ye ödeme isteği gönder
            payload = {
                'amount': float(amount),
                'currency': order.currency,
                'order_id': order.order_number,
                'customer_email': customer_info.get('email'),
                'customer_name': customer_info.get('name'),
                'customer_phone': customer_info.get('phone'),
                'return_url': self.config.get('return_url', f'{getattr(settings, "FRONTEND_URL", "https://api.tinisoft.com.tr")}/payment/return'),
                'cancel_url': self.config.get('cancel_url', f'{getattr(settings, "FRONTEND_URL", "https://api.tinisoft.com.tr")}/payment/cancel'),
                'metadata': {
                    'tenant_id': str(self.tenant.id),
                    'order_number': order.order_number,
                }
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
            
            # API çağrısı
            response = requests.post(
                f'{self.api_endpoint}/create',
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'payment_url': data.get('payment_url'),
                    'transaction_id': data.get('transaction_id'),
                    'error': None,
                }
            else:
                error_msg = response.json().get('error', 'Ödeme oluşturulamadı.')
                logger.error(f"Kuveyt API error: {error_msg}")
                return {
                    'success': False,
                    'payment_url': None,
                    'transaction_id': None,
                    'error': error_msg,
                }
        
        except Exception as e:
            logger.error(f"Kuveyt payment creation error: {str(e)}")
            return {
                'success': False,
                'payment_url': None,
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

