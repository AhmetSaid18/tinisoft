"""
Currency service - TCMB API entegrasyonu ile para birimi dönüşümü.
"""
import requests
import xml.etree.ElementTree as ET
from decimal import Decimal
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class CurrencyService:
    """Para birimi dönüşüm servisi - TCMB API kullanarak."""
    
    # TCMB API URL
    TCMB_API_URL = 'http://www.tcmb.gov.tr/kurlar/today.xml'
    
    # Cache timeout (1 saat - TCMB günlük güncelliyor)
    CACHE_TIMEOUT = 3600
    
    # TCMB Currency Code mapping
    TCMB_CURRENCY_CODES = {
        'USD': 'USD',
        'EUR': 'EUR',
        'TRY': 'TRY',  # TRY için 1.0 döner
    }
    
    @staticmethod
    def get_tcmb_exchange_rates():
        """
        TCMB'den güncel döviz kurlarını çek.
        
        Returns:
            dict: {'USD': Decimal('34.50'), 'EUR': Decimal('37.20'), ...}
        """
        cache_key = 'tcmb_exchange_rates'
        
        # Önce cache'den kontrol et
        cached_rates = cache.get(cache_key)
        if cached_rates:
            logger.debug("TCMB exchange rates loaded from cache")
            return cached_rates
        
        try:
            # TCMB API'den kurları çek
            response = requests.get(CurrencyService.TCMB_API_URL, timeout=5)
            response.raise_for_status()
            
            # XML'i parse et
            root = ET.fromstring(response.content)
            
            rates = {
                'TRY': Decimal('1.0'),  # TRY için 1.0
            }
            
            # USD ve EUR kurlarını al
            for currency in root.findall('Currency'):
                currency_code = currency.get('CurrencyCode')
                if currency_code in ['USD', 'EUR']:
                    # ForexSelling değerini al (satış kuru)
                    forex_selling = currency.find('ForexSelling')
                    if forex_selling is not None and forex_selling.text:
                        try:
                            rate = Decimal(forex_selling.text.replace(',', '.'))
                            rates[currency_code] = rate
                            logger.info(f"TCMB rate for {currency_code}: {rate}")
                        except (ValueError, AttributeError) as e:
                            logger.error(f"Error parsing TCMB rate for {currency_code}: {e}")
            
            # Cache'e kaydet
            cache.set(cache_key, rates, CurrencyService.CACHE_TIMEOUT)
            logger.info(f"TCMB exchange rates fetched and cached: {rates}")
            
            return rates
            
        except requests.RequestException as e:
            logger.error(f"Error fetching TCMB exchange rates: {e}")
            # Hata durumunda cache'deki eski değerleri kullan veya default değerler
            cached_rates = cache.get(cache_key)
            if cached_rates:
                logger.warning("Using cached TCMB rates due to API error")
                return cached_rates
            
            # Fallback: Default değerler (son çare)
            logger.warning("Using fallback exchange rates")
            return {
                'TRY': Decimal('1.0'),
                'USD': Decimal('34.0'),  # Fallback
                'EUR': Decimal('37.0'),  # Fallback
            }
        except ET.ParseError as e:
            logger.error(f"Error parsing TCMB XML: {e}")
            # Fallback
            cached_rates = cache.get(cache_key)
            if cached_rates:
                return cached_rates
            return {
                'TRY': Decimal('1.0'),
                'USD': Decimal('34.0'),
                'EUR': Decimal('37.0'),
            }
    
    @staticmethod
    def convert_amount(amount, from_currency, to_currency):
        """
        Para birimi dönüşümü yap.
        
        Args:
            amount: Dönüştürülecek tutar (Decimal)
            from_currency: Kaynak para birimi kodu (TRY, USD, EUR)
            to_currency: Hedef para birimi kodu (TRY, USD, EUR)
        
        Returns:
            Decimal: Dönüştürülmüş tutar
        """
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        
        # Aynı para birimiyse direkt döndür
        if from_currency == to_currency:
            return amount
        
        # TCMB kurlarını al
        rates = CurrencyService.get_tcmb_exchange_rates()
        
        # TRY'ye dönüştür (base currency)
        if from_currency == 'TRY':
            try_amount = amount
        elif from_currency in rates:
            # Yabancı para biriminden TRY'ye
            try_amount = amount * rates[from_currency]
        else:
            logger.warning(f"Unknown from_currency: {from_currency}, returning original amount")
            return amount
        
        # TRY'den hedef para birimine dönüştür
        if to_currency == 'TRY':
            return try_amount
        elif to_currency in rates:
            # TRY'den yabancı para birimine
            return try_amount / rates[to_currency]
        else:
            logger.warning(f"Unknown to_currency: {to_currency}, returning TRY amount")
            return try_amount
    
    @staticmethod
    def get_exchange_rate(from_currency, to_currency):
        """
        İki para birimi arasındaki dönüşüm oranını döndür.
        
        Args:
            from_currency: Kaynak para birimi kodu
            to_currency: Hedef para birimi kodu
        
        Returns:
            Decimal: Dönüşüm oranı
        """
        if from_currency == to_currency:
            return Decimal('1.0')
        
        rates = CurrencyService.get_tcmb_exchange_rates()
        
        # TRY'ye dönüştür
        if from_currency == 'TRY':
            from_rate = Decimal('1.0')
        elif from_currency in rates:
            from_rate = rates[from_currency]
        else:
            logger.warning(f"Unknown from_currency: {from_currency}")
            return Decimal('1.0')
        
        # TRY'den hedef para birimine
        if to_currency == 'TRY':
            to_rate = Decimal('1.0')
        elif to_currency in rates:
            to_rate = rates[to_currency]
        else:
            logger.warning(f"Unknown to_currency: {to_currency}")
            return Decimal('1.0')
        
        # Oran: (from_currency -> TRY) / (to_currency -> TRY)
        # Örnek: USD -> EUR = (USD/TRY) / (EUR/TRY)
        if to_currency == 'TRY':
            return from_rate
        elif from_currency == 'TRY':
            return Decimal('1.0') / to_rate
        else:
            return from_rate / to_rate
    
    @staticmethod
    def update_currency_exchange_rates(tenant):
        """
        Tenant'ın Currency modellerindeki exchange_rate değerlerini TCMB'den güncelle.
        
        Args:
            tenant: Tenant instance
        """
        from apps.models import Currency
        
        rates = CurrencyService.get_tcmb_exchange_rates()
        
        # Default currency'yi bul (TRY olmalı)
        default_currency = Currency.objects.filter(
            tenant=tenant,
            is_default=True,
            is_active=True,
            is_deleted=False
        ).first()
        
        if not default_currency:
            logger.warning(f"No default currency found for tenant {tenant.name}")
            return
        
        # Default currency TRY olmalı
        if default_currency.code != 'TRY':
            logger.warning(f"Default currency is not TRY for tenant {tenant.name}")
            return
        
        # Diğer para birimlerini güncelle
        for currency in Currency.objects.filter(
            tenant=tenant,
            is_active=True,
            is_deleted=False
        ).exclude(code='TRY'):
            if currency.code in rates:
                currency.exchange_rate = rates[currency.code]
                currency.save(update_fields=['exchange_rate'])
                logger.info(f"Updated exchange rate for {currency.code}: {currency.exchange_rate}")

