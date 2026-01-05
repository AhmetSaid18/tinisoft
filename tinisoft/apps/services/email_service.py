"""
Email gönderme servisi - SMTP ile email gönderimi.
Tenant'ların kendi SMTP ayarlarını kullanarak email gönderme.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from django.conf import settings
from apps.models import IntegrationProvider
import logging
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)


class EmailService:
    """Email gönderme servisi."""
    
    @staticmethod
    def get_email_integration(tenant):
        """
        Tenant'ın aktif email entegrasyonunu al.
        
        Args:
            tenant: Tenant instance
        
        Returns:
            IntegrationProvider instance veya None
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
        
        Args:
            tenant: Tenant instance
        
        Returns:
            dict: SMTP config veya None
        """
        integration = EmailService.get_email_integration(tenant)
        if not integration:
            return None
        
        try:
            config = integration.config or {}
            
            # SMTP ayarları
            smtp_config = {
                'host': config.get('smtp_host', ''),
                'port': config.get('smtp_port', 587),
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
        Email gönder.
        
        Args:
            tenant: Tenant instance
            to_email: Alıcı email adresi
            subject: Email konusu
            html_content: HTML içerik
            text_content: Plain text içerik (opsiyonel)
            from_email: Gönderen email (opsiyonel, config'den alınır)
            from_name: Gönderen adı (opsiyonel, config'den alınır)
            reply_to: Reply-to adresi (opsiyonel)
            attachments: Ek dosyalar (opsiyonel) [{'filename': 'file.pdf', 'content': bytes, 'content_type': 'application/pdf'}]
        
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'error': str (optional)
            }
        """
        try:
            # SMTP config al
            smtp_config = EmailService.get_smtp_config(tenant)
            if not smtp_config:
                return {
                    'success': False,
                    'message': 'Email entegrasyonu bulunamadı veya aktif değil.',
                    'error': 'SMTP config not found'
                }
            
            # Gönderen bilgileri
            from_email = from_email or smtp_config['from_email']
            from_name = from_name or smtp_config['from_name']
            
            # Email oluştur
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # İçerik ekle
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            # Ek dosyalar ekle
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.get('content', b''))
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment.get("filename", "file")}'
                    )
                    msg.attach(part)
            
            # SMTP bağlantısı
            if smtp_config['use_ssl']:
                server = smtplib.SMTP_SSL(smtp_config['host'], smtp_config['port'])
            else:
                server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
                if smtp_config['use_tls']:
                    server.starttls()
            
            # Giriş yap
            server.login(smtp_config['username'], smtp_config['password'])
            
            # Email gönder
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email} from tenant {tenant.id}")
            
            return {
                'success': True,
                'message': 'Email başarıyla gönderildi.',
            }
        
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication error: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': 'Email gönderim hatası: Kimlik doğrulama başarısız.',
                'error': error_msg
            }
        
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': f'Email gönderim hatası: {str(e)}',
                'error': error_msg
            }
        
        except Exception as e:
            error_msg = f"Email send error: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': f'Email gönderim hatası: {str(e)}',
                'error': error_msg
            }
    
    @staticmethod
    def send_order_confirmation_email(tenant, order):
        """
        Sipariş onay email'i gönder.
        
        Args:
            tenant: Tenant instance
            order: Order instance
        
        Returns:
            dict: Email gönderme sonucu
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
        
        Args:
            tenant: Tenant instance
            order: Order instance
        
        Returns:
            dict: Email gönderme sonucu
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
        
        Args:
            tenant: Tenant instance
            order: Order instance
        
        Returns:
            dict: Email gönderme sonucu
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
        
        Args:
            tenant: Tenant instance
            order: Order instance
        
        Returns:
            dict: Email gönderme sonucu
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
        subject = f"Giriş Doğrulama Kodu: {code}"
        
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
            html_content=html_content
        )

