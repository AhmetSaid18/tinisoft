"""
Django management command to set up Aras Kargo integration.
Usage: python manage.py setup_aras_cargo --tenant-slug <slug> --username <username> --password <password> --customer-code <code> --account-id <account_id>
"""
from django.core.management.base import BaseCommand, CommandError
from apps.models import IntegrationProvider, Tenant
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Set up Aras Kargo integration for a tenant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-slug',
            type=str,
            required=True,
            help='Tenant slug (subdomain)',
        )
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Aras Kargo kullanıcı adı (API key)',
        )
        parser.add_argument(
            '--password',
            type=str,
            required=True,
            help='Aras Kargo şifre (API secret)',
        )
        parser.add_argument(
            '--customer-code',
            type=str,
            required=True,
            help='Müşteri kodu (customer_code)',
        )
        parser.add_argument(
            '--account-id',
            type=str,
            required=True,
            help='Account ID (takip linki için)',
        )
        parser.add_argument(
            '--tracking-password',
            type=str,
            required=False,
            help='Takip linki için güvenlik şifresi (sifre parametresi). Eğer verilmezse password kullanılır.',
        )
        parser.add_argument(
            '--setorder-username',
            type=str,
            required=False,
            help='SetOrder API kullanıcı adı (gönderi oluşturma için)',
        )
        parser.add_argument(
            '--setorder-password',
            type=str,
            required=False,
            help='SetOrder API şifresi (gönderi oluşturma için)',
        )
        parser.add_argument(
            '--setorder-endpoint',
            type=str,
            required=False,
            help='SetOrder API endpoint URL (opsiyonel)',
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['active', 'inactive', 'test_mode'],
            default='active',
            help='Integration status (default: active)',
        )
        parser.add_argument(
            '--api-endpoint',
            type=str,
            required=False,
            help='API endpoint URL (opsiyonel, default kullanılır)',
        )
        parser.add_argument(
            '--test-endpoint',
            type=str,
            required=False,
            help='Test API endpoint URL (opsiyonel)',
        )

    def handle(self, *args, **options):
        tenant_slug = options['tenant_slug']
        username = options['username']
        password = options['password']
        customer_code = options['customer_code']
        account_id = options['account_id']
        tracking_password = options.get('tracking_password') or password
        status = options['status']
        api_endpoint = options.get('api_endpoint')
        test_endpoint = options.get('test_endpoint')

        # Tenant'ı bul
        try:
            tenant = Tenant.objects.get(slug=tenant_slug, is_deleted=False)
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant bulunamadı: {tenant_slug}')

        self.stdout.write(f'Tenant bulundu: {tenant.name} ({tenant.slug})')

        # Mevcut entegrasyonu kontrol et
        existing_integration = IntegrationProvider.objects.filter(
            tenant=tenant,
            provider_type=IntegrationProvider.ProviderType.ARAS,
            is_deleted=False
        ).first()

        if existing_integration:
            self.stdout.write(self.style.WARNING(f'Mevcut Aras Kargo entegrasyonu bulundu. Güncelleniyor...'))
            integration = existing_integration
        else:
            self.stdout.write('Yeni Aras Kargo entegrasyonu oluşturuluyor...')
            integration = IntegrationProvider(
                tenant=tenant,
                provider_type=IntegrationProvider.ProviderType.ARAS,
                name='Aras Kargo Entegrasyonu',
                description=f'Aras Kargo API entegrasyonu - {tenant.name}',
            )

        # Bilgileri güncelle
        integration.status = status
        integration.set_api_key(username)
        integration.set_api_secret(password)

        if api_endpoint:
            integration.api_endpoint = api_endpoint

        if test_endpoint:
            integration.test_endpoint = test_endpoint

        # Config bilgilerini güncelle
        config = integration.config.copy() if integration.config else {}
        config['customer_code'] = customer_code
        config['account_id'] = account_id
        config['tracking_password'] = tracking_password
        
        # SetOrder bilgileri (email'den gelen bilgiler)
        setorder_username = options.get('setorder_username')
        setorder_password = options.get('setorder_password')
        setorder_endpoint = options.get('setorder_endpoint')
        
        if setorder_username or setorder_password:
            if 'setorder' not in config:
                config['setorder'] = {}
            if setorder_username:
                config['setorder']['username'] = setorder_username
            if setorder_password:
                config['setorder']['password'] = setorder_password
            if setorder_endpoint:
                config['setorder']['endpoint'] = setorder_endpoint
            config['setorder']['customer_code'] = customer_code
        
        integration.config = config

        # Kaydet
        integration.save()

        self.stdout.write(self.style.SUCCESS(f'Aras Kargo entegrasyonu başarıyla kaydedildi!'))
        self.stdout.write(f'  - ID: {integration.id}')
        self.stdout.write(f'  - Durum: {integration.get_status_display()}')
        self.stdout.write(f'  - Müşteri Kodu: {customer_code}')
        self.stdout.write(f'  - Account ID: {account_id}')
        self.stdout.write(f'  - API Endpoint: {integration.api_endpoint or "Default"}')
        
        if setorder_username:
            self.stdout.write(f'  - SetOrder Username: {setorder_username}')
            self.stdout.write(f'  - SetOrder Endpoint: {setorder_endpoint or "Default"}')
        
        # Örnek takip linki göster
        from apps.services.aras_cargo_service import ArasCargoService
        example_tracking_url = ArasCargoService.get_tracking_url(
            tenant=tenant,
            tracking_reference='EXAMPLE123',
            tracking_type='order_number'
        )
        self.stdout.write(f'  - Örnek Takip Linki: {example_tracking_url}')
        self.stdout.write(self.style.SUCCESS('\n✅ Artık gönderi oluşturup müşteriye takip linki verebilirsiniz!'))

