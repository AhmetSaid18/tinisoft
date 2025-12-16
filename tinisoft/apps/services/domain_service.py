"""
Domain service.
Domain kayıt, doğrulama ve yönetim işlemleri.
"""
import secrets
import string
import logging

logger = logging.getLogger(__name__)


class DomainService:
    """Domain yönetim servisi."""
    
    @staticmethod
    def generate_verification_code(length: int = 32) -> str:
        """
        DNS doğrulama kodu oluştur.
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def get_verification_txt_record(domain_name: str, verification_code: str) -> str:
        """
        DNS TXT record değerini döndür.
        """
        from django.conf import settings
        prefix = getattr(settings, 'DOMAIN_VERIFICATION_TXT_PREFIX', 'tinisoft-verify')
        return f"{prefix}={verification_code}"
    
    @staticmethod
    def verify_domain_dns(domain_name: str, verification_code: str) -> bool:
        """
        DNS kayıtlarını kontrol et ve domain'i doğrula.
        TODO: DNS lookup implementasyonu
        """
        try:
            import dns.resolver
            
            # TXT record kontrolü
            txt_record = DomainService.get_verification_txt_record(domain_name, verification_code)
            
            try:
                answers = dns.resolver.resolve(domain_name, 'TXT')
                for answer in answers:
                    if txt_record in str(answer):
                        return True
            except dns.resolver.NXDOMAIN:
                pass
            
            # CNAME kontrolü
            from django.conf import settings
            cname_target = getattr(settings, 'DOMAIN_VERIFICATION_CNAME_TARGET', 'verify.tinisoft.com.tr')
            try:
                answers = dns.resolver.resolve(f"tinisoft-verify.{domain_name}", 'CNAME')
                for answer in answers:
                    if cname_target in str(answer):
                        return True
            except dns.resolver.NXDOMAIN:
                pass
            
            return False
        except Exception as e:
            logger.error(f"DNS verification failed for {domain_name}: {str(e)}")
            return False
    
    @staticmethod
    def get_verification_instructions(domain):
        """
        Domain doğrulama talimatlarını döndür.
        """
        if not domain.is_custom:
            return "Subdomain otomatik olarak doğrulanmıştır."
        
        txt_record = DomainService.get_verification_txt_record(
            domain.domain_name,
            domain.verification_code
        )
        
        from django.conf import settings
        cname_target = getattr(settings, 'DOMAIN_VERIFICATION_CNAME_TARGET', 'verify.tinisoft.com.tr')
        
        instructions = f"""
Domain doğrulaması için aşağıdaki DNS kayıtlarından birini ekleyin:

1. TXT Record:
   Name: @ (veya {domain.domain_name})
   Value: {txt_record}

2. VEYA CNAME Record:
   Name: tinisoft-verify.{domain.domain_name}
   Value: {cname_target}

DNS kaydını ekledikten sonra, doğrulama işlemi otomatik olarak başlatılacaktır.
        """
        
        return instructions.strip()

