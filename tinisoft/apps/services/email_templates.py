"""
Email template servisi - Email içeriklerini oluşturur.
"""
from typing import Tuple
from decimal import Decimal


class EmailTemplateService:
    """Email template servisi."""
    
    @staticmethod
    def get_order_confirmation_template(tenant, order) -> Tuple[str, str]:
        """
        Sipariş onay email template'i.
        
        Returns:
            Tuple[str, str]: (html_content, text_content)
        """
        # HTML içerik
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .order-info {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .order-item {{ padding: 10px; border-bottom: 1px solid #eee; }}
                .total {{ font-weight: bold; font-size: 18px; color: #4CAF50; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Siparişiniz Onaylandı!</h1>
                </div>
                <div class="content">
                    <p>Merhaba {order.customer_first_name} {order.customer_last_name},</p>
                    <p>Siparişiniz başarıyla alındı ve onaylandı. Sipariş detaylarınız aşağıdadır:</p>
                    
                    <div class="order-info">
                        <h2>Sipariş Bilgileri</h2>
                        <p><strong>Sipariş No:</strong> {order.order_number}</p>
                        <p><strong>Tarih:</strong> {order.created_at.strftime('%d.%m.%Y %H:%M')}</p>
                        <p><strong>Durum:</strong> {order.get_status_display()}</p>
                    </div>
                    
                    <div class="order-info">
                        <h2>Sipariş Detayları</h2>
                        {"".join([f'<div class="order-item"><strong>{item.product_name}</strong> x {item.quantity} = {item.total_price} {order.currency}</div>' for item in order.items.all()])}
                        <div class="order-item">Kargo: {order.shipping_cost} {order.currency}</div>
                        {f'<div class="order-item">İndirim: -{order.discount_amount} {order.currency}</div>' if order.discount_amount > 0 else ''}
                        <div class="order-item total">Toplam: {order.total} {order.currency}</div>
                    </div>
                    
                    <div class="order-info">
                        <h2>Teslimat Adresi</h2>
                        <p>{order.shipping_address.full_address if order.shipping_address else f"{order.customer_first_name} {order.customer_last_name}, {order.customer_phone}"}</p>
                    </div>
                    
                    <p>Siparişinizin durumunu takip etmek için: <a href="{tenant.get_frontend_url()}/orders/{order.order_number}">Sipariş Takip</a></p>
                    
                    <p>Teşekkür ederiz!</p>
                    <p><strong>{tenant.name}</strong></p>
                </div>
                <div class="footer">
                    <p>Bu email {tenant.name} tarafından gönderilmiştir.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text içerik
        text_content = f"""
Siparişiniz Onaylandı!

Merhaba {order.customer_first_name} {order.customer_last_name},

Siparişiniz başarıyla alındı ve onaylandı.

Sipariş Bilgileri:
- Sipariş No: {order.order_number}
- Tarih: {order.created_at.strftime('%d.%m.%Y %H:%M')}
- Durum: {order.get_status_display()}

Sipariş Detayları:
{chr(10).join([f'- {item.product_name} x {item.quantity} = {item.total_price} {order.currency}' for item in order.items.all()])}
- Kargo: {order.shipping_cost} {order.currency}
{f'- İndirim: -{order.discount_amount} {order.currency}' if order.discount_amount > 0 else ''}
- Toplam: {order.total} {order.currency}

Teslimat Adresi:
{order.shipping_address.full_address if order.shipping_address else f"{order.customer_first_name} {order.customer_last_name}, {order.customer_phone}"}

Siparişinizin durumunu takip etmek için: {tenant.get_frontend_url()}/orders/{order.order_number}

Teşekkür ederiz!
{tenant.name}
        """
        
        return html_content, text_content
    
    @staticmethod
    def get_order_shipped_template(tenant, order) -> Tuple[str, str]:
        """
        Sipariş kargoya verildi email template'i.
        
        Returns:
            Tuple[str, str]: (html_content, text_content)
        """
        tracking_info = ""
        if order.tracking_number:
            tracking_info = f'<p><strong>Takip Numarası:</strong> {order.tracking_number}</p>'
        
        # HTML içerik
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .info-box {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .tracking {{ font-size: 24px; font-weight: bold; color: #2196F3; text-align: center; padding: 20px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Siparişiniz Kargoya Verildi!</h1>
                </div>
                <div class="content">
                    <p>Merhaba {order.customer_first_name} {order.customer_last_name},</p>
                    <p>Siparişiniz kargoya verildi. Yakında size ulaşacaktır.</p>
                    
                    <div class="info-box">
                        <h2>Sipariş Bilgileri</h2>
                        <p><strong>Sipariş No:</strong> {order.order_number}</p>
                        <p><strong>Kargoya Verilme Tarihi:</strong> {order.shipped_at.strftime('%d.%m.%Y %H:%M') if order.shipped_at else 'Belirtilmemiş'}</p>
                        {tracking_info}
                    </div>
                    
                    {f'<div class="tracking">Takip No: {order.tracking_number}</div>' if order.tracking_number else ''}
                    
                    <p>Siparişinizin durumunu takip etmek için: <a href="{tenant.get_frontend_url()}/orders/{order.order_number}">Sipariş Takip</a></p>
                    
                    <p>Teşekkür ederiz!</p>
                    <p><strong>{tenant.name}</strong></p>
                </div>
                <div class="footer">
                    <p>Bu email {tenant.name} tarafından gönderilmiştir.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text içerik
        text_content = f"""
Siparişiniz Kargoya Verildi!

Merhaba {order.customer_first_name} {order.customer_last_name},

Siparişiniz kargoya verildi. Yakında size ulaşacaktır.

Sipariş Bilgileri:
- Sipariş No: {order.order_number}
- Kargoya Verilme Tarihi: {order.shipped_at.strftime('%d.%m.%Y %H:%M') if order.shipped_at else 'Belirtilmemiş'}
{f'- Takip Numarası: {order.tracking_number}' if order.tracking_number else ''}

Siparişinizin durumunu takip etmek için: {tenant.get_frontend_url()}/orders/{order.order_number}

Teşekkür ederiz!
{tenant.name}
        """
        
        return html_content, text_content
    
    @staticmethod
    def get_order_delivered_template(tenant, order) -> Tuple[str, str]:
        """
        Sipariş teslim edildi email template'i.
        
        Returns:
            Tuple[str, str]: (html_content, text_content)
        """
        # HTML içerik
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .info-box {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Siparişiniz Teslim Edildi!</h1>
                </div>
                <div class="content">
                    <p>Merhaba {order.customer_first_name} {order.customer_last_name},</p>
                    <p>Siparişiniz başarıyla teslim edildi. Memnun kaldıysanız değerlendirme yapabilirsiniz.</p>
                    
                    <div class="info-box">
                        <h2>Sipariş Bilgileri</h2>
                        <p><strong>Sipariş No:</strong> {order.order_number}</p>
                        <p><strong>Teslim Tarihi:</strong> {order.delivered_at.strftime('%d.%m.%Y %H:%M') if order.delivered_at else 'Belirtilmemiş'}</p>
                    </div>
                    
                    <p>Ürünleri değerlendirmek için: <a href="{tenant.get_frontend_url()}/orders/{order.order_number}/review">Değerlendirme Yap</a></p>
                    
                    <p>Teşekkür ederiz!</p>
                    <p><strong>{tenant.name}</strong></p>
                </div>
                <div class="footer">
                    <p>Bu email {tenant.name} tarafından gönderilmiştir.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text içerik
        text_content = f"""
Siparişiniz Teslim Edildi!

Merhaba {order.customer_first_name} {order.customer_last_name},

Siparişiniz başarıyla teslim edildi. Memnun kaldıysanız değerlendirme yapabilirsiniz.

Sipariş Bilgileri:
- Sipariş No: {order.order_number}
- Teslim Tarihi: {order.delivered_at.strftime('%d.%m.%Y %H:%M') if order.delivered_at else 'Belirtilmemiş'}

Ürünleri değerlendirmek için: {tenant.get_frontend_url()}/orders/{order.order_number}/review

Teşekkür ederiz!
{tenant.name}
        """
        
        return html_content, text_content
    
    @staticmethod
    def get_order_cancelled_template(tenant, order) -> Tuple[str, str]:
        """
        Sipariş iptal email template'i.
        
        Returns:
            Tuple[str, str]: (html_content, text_content)
        """
        # HTML içerik
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .info-box {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Siparişiniz İptal Edildi</h1>
                </div>
                <div class="content">
                    <p>Merhaba {order.customer_first_name} {order.customer_last_name},</p>
                    <p>Maalesef siparişiniz iptal edildi.</p>
                    
                    <div class="info-box">
                        <h2>Sipariş Bilgileri</h2>
                        <p><strong>Sipariş No:</strong> {order.order_number}</p>
                        <p><strong>İptal Tarihi:</strong> {order.updated_at.strftime('%d.%m.%Y %H:%M')}</p>
                        {f'<p><strong>İptal Nedeni:</strong> {order.admin_note}</p>' if order.admin_note else ''}
                    </div>
                    
                    <p>Ödeme yapıldıysa, iade işlemi en kısa sürede gerçekleştirilecektir.</p>
                    
                    <p>Sorularınız için bizimle iletişime geçebilirsiniz.</p>
                    
                    <p>Teşekkür ederiz!</p>
                    <p><strong>{tenant.name}</strong></p>
                </div>
                <div class="footer">
                    <p>Bu email {tenant.name} tarafından gönderilmiştir.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text içerik
        text_content = f"""
Siparişiniz İptal Edildi

Merhaba {order.customer_first_name} {order.customer_last_name},

Maalesef siparişiniz iptal edildi.

Sipariş Bilgileri:
- Sipariş No: {order.order_number}
- İptal Tarihi: {order.updated_at.strftime('%d.%m.%Y %H:%M')}
{f'- İptal Nedeni: {order.admin_note}' if order.admin_note else ''}

Ödeme yapıldıysa, iade işlemi en kısa sürede gerçekleştirilecektir.

Sorularınız için bizimle iletişime geçebilirsiniz.

Teşekkür ederiz!
{tenant.name}
        """
        
        return html_content, text_content

