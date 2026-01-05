import os
import django
import sys

# Django ortamını kur
sys.path.append(r'c:\projects\tinisoft\tinisoft')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tinisoft.settings')
django.setup()

from apps.models import Tenant, IntegrationProvider
from apps.services.email_service import EmailService
import smtplib

def test_mail_debug():
    tenant_slug = 'avrupamutfak'
    to_email = 'backstagecrm@gmail.com' # User'ın maili
    
    try:
        tenant = Tenant.objects.get(slug=tenant_slug)
        print(f"Tenant bulundu: {tenant.name}")
        
        integration = IntegrationProvider.objects.filter(
            tenant=tenant,
            provider_type=IntegrationProvider.ProviderType.EMAIL,
            status=IntegrationProvider.Status.ACTIVE
        ).first()
        
        if not integration:
            print("Aktif email entegrasyonu bulunamadı!")
            return

        config = integration.config or {}
        print(f"Config: {config}")
        
        # Sifreyi ve digerlerini al
        host = config.get('smtp_host')
        port = config.get('smtp_port', 587)
        user = integration.get_api_key() or config.get('smtp_username') or config.get('from_email')
        password = integration.get_api_secret() or config.get('smtp_password')
        use_ssl = config.get('smtp_use_ssl', False)
        
        print(f"Baglaniliyor: {host}:{port} (SSL: {use_ssl})")
        print(f"Kullanici: {user}")
        print(f"Sifre Mevcut mu?: {'Evet' if password else 'Hayir'}")

        if not password:
            print("HATA: Sifre bulunamadi! Integration ayarlarindan sifreyi (api_secret veya config.smtp_password) girmeniz lazim.")
            return

        # Manuel SMTP Testi (Debug Level ile)
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
            
        server.set_debuglevel(1)
        server.login(user, password)
        
        # Test maili gonder
        res = EmailService.send_verification_email(tenant, to_email, "999888")
        print(f"Gonderim Sonucu: {res}")
        
        server.quit()
        
    except Exception as e:
        print(f"HATA OLUSTU: {str(e)}")

if __name__ == "__main__":
    test_mail_debug()
