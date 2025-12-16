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
        """
        try:
            import dns.resolver
            
            # TXT record kontrolü
            txt_record = DomainService.get_verification_txt_record(domain_name, verification_code)
            logger.info(f"Checking TXT record for {domain_name}: looking for {txt_record}")
            
            try:
                answers = dns.resolver.resolve(domain_name, 'TXT')
                for answer in answers:
                    answer_str = str(answer).strip('"')
                    logger.debug(f"Found TXT record: {answer_str}")
                    if txt_record in answer_str:
                        logger.info(f"TXT record verification successful for {domain_name}")
                        return True
            except dns.resolver.NXDOMAIN:
                logger.debug(f"No TXT records found for {domain_name}")
            except dns.resolver.NoAnswer:
                logger.debug(f"No TXT answer for {domain_name}")
            except Exception as e:
                logger.warning(f"TXT record check error for {domain_name}: {str(e)}")
            
            # CNAME kontrolü
            from django.conf import settings
            cname_target = getattr(settings, 'DOMAIN_VERIFICATION_CNAME_TARGET', 'verify.tinisoft.com.tr')
            cname_subdomain = f"tinisoft-verify.{domain_name}"
            logger.info(f"Checking CNAME record for {cname_subdomain}: looking for {cname_target}")
            
            try:
                answers = dns.resolver.resolve(cname_subdomain, 'CNAME')
                for answer in answers:
                    answer_str = str(answer).strip('.').lower()
                    target_lower = cname_target.lower()
                    logger.debug(f"Found CNAME record: {answer_str}")
                    if target_lower in answer_str:
                        logger.info(f"CNAME record verification successful for {domain_name}")
                        return True
            except dns.resolver.NXDOMAIN:
                logger.debug(f"No CNAME record found for {cname_subdomain}")
            except dns.resolver.NoAnswer:
                logger.debug(f"No CNAME answer for {cname_subdomain}")
            except Exception as e:
                logger.warning(f"CNAME record check error for {cname_subdomain}: {str(e)}")
            
            logger.warning(f"DNS verification failed for {domain_name}: No matching TXT or CNAME records found")
            return False
        except ImportError:
            logger.error("dnspython library not installed. Install it with: pip install dnspython")
            raise Exception("DNS verification library not available. Please install dnspython.")
        except Exception as e:
            logger.error(f"DNS verification failed for {domain_name}: {str(e)}")
            raise
    
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

