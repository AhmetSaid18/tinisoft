"""
SSL service.
Let's Encrypt ile SSL sertifikası yönetimi.
"""
import logging

logger = logging.getLogger(__name__)


class SSLService:
    """SSL sertifika yönetim servisi."""
    
    @staticmethod
    def obtain_certificate(domain):
        """
        Let's Encrypt ile SSL sertifikası al.
        Traefik otomatik olarak Let's Encrypt ile sertifika alır.
        Bu fonksiyon sadece log için.
        """
        logger.info(f"SSL certificate will be obtained by Traefik for: {domain.domain_name}")
        # Traefik Let's Encrypt resolver ile otomatik sertifika alır
        # Burada sadece log tutuyoruz
        return True
    
    @staticmethod
    def renew_certificate(domain):
        """
        SSL sertifikasını yenile.
        """
        logger.info(f"SSL certificate renewal for: {domain.domain_name}")
        # Traefik otomatik olarak yeniler
        return True

