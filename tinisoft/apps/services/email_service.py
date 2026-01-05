import smtplib
import time
import logging
import re
from typing import List, Optional, Dict

from django.conf import settings
from django.core.mail import get_connection, EmailMultiAlternatives
from django.core.mail.message import make_msgid

from apps.models import IntegrationProvider

logger = logging.getLogger(__name__)


class EmailService:
    """Email gönderme servisi."""
    
    @staticmethod
    def get_email_integration(tenant):
        """
        Tenant'ın aktif email entegrasyonunu al.
        """
        try:
            integration = IntegrationProvider.objects.filter(
                tenant=tenant,
                provider_type=IntegrationProvider.ProviderType.EMAIL,
                status=IntegrationProvider.Status.ACTIVE
            ).first()
            return integration
        except Exception as e:
            logger.error(f"Email integration get error: {str(e)}")
            return None
    
    @staticmethod
    def get_smtp_config(tenant):
        """
        Tenant'ın SMTP ayarlarını al.
        """
        integration = EmailService.get_email_integration(tenant)
        if not integration:
            return None
        
        try:
            config = integration.config or {}
            
            # SMTP ayarları
            smtp_config = {
                'host': config.get('smtp_host', ''),
                'port': int(config.get('smtp_port', 587)),
                'username': integration.get_api_key() or config.get('smtp_username') or config.get('from_email', ''),
                'password': integration.get_api_secret() or config.get('smtp_password', ''),
                'use_tls': config.get('smtp_use_tls', True),
                'use_ssl': config.get('smtp_use_ssl', False),
                'from_email': config.get('from_email') or integration.get_api_key() or '',
                'from_name': config.get('from_name', tenant.name),
            }
            
            # Gerekli alanlar kontrolü
            if not smtp_config['host'] or not smtp_config['username'] or not smtp_config['password']:
                logger.warning(f"SMTP config eksik for tenant {tenant.id}")
                return None
            
            return smtp_config
        except Exception as e:
            logger.error(f"SMTP config get error: {str(e)}")
            return None
    
    @staticmethod
    def send_email(
        tenant,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
    ):
        """
        Email gönder - Django'nun native mail araçlarını kullanarak.
        """
        try:
            # SMTP config al
            smtp_config = EmailService.get_smtp_config(tenant)
            if not smtp_config:
                logger.error(f"Email Hata: SMTP config bulunamadı (Host: {tenant.slug})")
                return {
                    'success': False,
                    'message': 'Email entegrasyonu bulunamadı veya aktif değil.',
                    'error': 'SMTP config not found'
                }
            
            # Gönderen bilgileri
            from_email_addr = from_email or smtp_config['from_email']
            from_name_str = from_name or smtp_config['from_name']
            
            # Gönderen adresi formatla
            from_email_formatted = f"{from_name_str} <{from_email_addr}>" if from_name_str else from_email_addr
            
            # Eğer plain text yoksa HTML'den tagları temizleyerek oluştur
            if not text_content:
                text_content = re.sub('<[^<]+?>', '', html_content).strip()

            logger.info(f"Email Gonderiliyor: To={to_email}, From={from_email_formatted}")

            # SSL ve TLS aynı anda True olamaz, SSL önceliklidir
            use_ssl = smtp_config.get('use_ssl', False)
            use_tls = smtp_config.get('use_tls', True) if not use_ssl else False

            # Bağlantı
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=smtp_config['host'],
                port=smtp_config['port'],
                username=smtp_config['username'],
                password=smtp_config['password'],
                use_tls=use_tls,
                use_ssl=use_ssl,
                timeout=25
            )

            # Temel başlıklar
            headers = {
                'Message-ID': make_msgid(domain=from_email_addr.split('@')[-1]),
                'Date': time.strftime("%a, %d %b %Y %H:%M:%S %z"),
                'X-Mailer': 'Tinisoft API',
            }

            # Maili oluştur
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email_formatted,
                to=[to_email],
                connection=connection,
                headers=headers
            )
            
            if reply_to:
                email.extra_headers['Reply-To'] = reply_to

            email.attach_alternative(html_content, "text/html")
            
            if attachments:
                for attachment in attachments:
                    email.attach(
                        attachment.get('filename', 'file'),
                        attachment.get('content', b''),
                        attachment.get('content_type', 'application/octet-stream')
                    )
            
            email.send(fail_silently=False)
            logger.info(f"EMAIL BASARILI: {to_email} (Host: {smtp_config['host']})")
            
            return {
                'success': True,
                'message': 'Email başarıyla gönderildi.',
            }
        
        except Exception as e:
            error_msg = f"Email gönderim hatası: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'message': 'Email gönderilemedi.',
                'error': str(e)
            }

    @staticmethod
    def send_order_confirmation_email(tenant, order):
        """
        Sipariş onay email'i gönder.
        """
        from apps.services.email_templates import EmailTemplateService
        
        # Template'den içerik al
        html_content, text_content = EmailTemplateService.get_order_confirmation_template(
            tenant, order
        )
        
        subject = f"Siparişiniz Onaylandı - {order.order_number}"
        
        return EmailService.send_email(
            tenant=tenant,
            to_email=order.customer_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )
    
    @staticmethod
    def send_order_shipped_email(tenant, order):
        """
        Sipariş kargoya verildi email'i gönder.
        """
        from apps.services.email_templates import EmailTemplateService
        
        # Template'den içerik al
        html_content, text_content = EmailTemplateService.get_order_shipped_template(
            tenant, order
        )
        
        subject = f"Siparişiniz Kargoya Verildi - {order.order_number}"
        
        return EmailService.send_email(
            tenant=tenant,
            to_email=order.customer_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )
    
    @staticmethod
    def send_order_delivered_email(tenant, order):
        """
        Sipariş teslim edildi email'i gönder.
        """
        from apps.services.email_templates import EmailTemplateService
        
        # Template'den içerik al
        html_content, text_content = EmailTemplateService.get_order_delivered_template(
            tenant, order
        )
        
        subject = f"Siparişiniz Teslim Edildi - {order.order_number}"
        
        return EmailService.send_email(
            tenant=tenant,
            to_email=order.customer_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )
    
    @staticmethod
    def send_order_cancelled_email(tenant, order):
        """
        Sipariş iptal email'i gönder.
        """
        from apps.services.email_templates import EmailTemplateService
        
        # Template'den içerik al
        html_content, text_content = EmailTemplateService.get_order_cancelled_template(
            tenant, order
        )
        
        subject = f"Siparişiniz İptal Edildi - {order.order_number}"
        
        return EmailService.send_email(
            tenant=tenant,
            to_email=order.customer_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

    @staticmethod
    def send_verification_email(tenant, to_email: str, code: str):
        """
        Kayıt için doğrulama kodu gönder.
        """
        subject = f"Doğrulama Kodunuz: {code}"
        
        text_content = f"Merhaba, Mağazamıza kayıt olmak için doğrulama kodunuz: {code}. Bu kod 10 dakika geçerlidir. {tenant.name}"
        
        html_content = f"""
        <div style="font-family: sans-serif; padding: 20px; border: 1px solid #eee; border-radius: 10px; max-width: 600px; margin: auto;">
            <h2 style="color: #333; text-align: center;">Doğrulama Kodu</h2>
            <p style="font-size: 16px; color: #555;">Merhaba,</p>
            <p style="font-size: 16px; color: #555;">Mağazamıza kayıt olmak için kullanmanız gereken 6 haneli doğrulama kodunuz aşağıdadır:</p>
            <div style="background-color: #f9f9f9; padding: 20px; text-align: center; border-radius: 10px; margin: 20px 0;">
                <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #007bff;">{code}</span>
            </div>
            <p style="font-size: 14px; color: #999; text-align: center;">Bu kod 10 dakika boyunca geçerlidir.</p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #aaa; text-align: center;">{tenant.name} - Tinisoft Altyapısıyla Güçlendirilmiştir</p>
        </div>
        """
        
        return EmailService.send_email(
            tenant=tenant,
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
