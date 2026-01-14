
from apps.services.payment_providers import PaymentProviderBase

class BankTransferPaymentProvider(PaymentProviderBase):
    """
    Banka Havalesi / EFT ödeme sağlayıcısı.
    
    API bağlantısı yapmaz, sadece siparişi onaylar ve 
    müşteriye gösterilecek IBAN bilgilerini döner.
    
    Config'de şu bilgiler olabilir (opsiyonel):
    - iban: IBAN Adresi (açıklamadan da alınabilir)
    - bank_name: Banka adı
    - account_name: Hesap Sahibi
    """
    
    def __init__(self, tenant, config=None):
        super().__init__(tenant, config)
        
    def create_payment(self, order, amount, customer_info):
        """
        Havale ödemesi oluştur.
        Direkt başarılı döner, mesaj içinde IBAN bilgisini iletir.
        """
        # Config'den IBAN vb. bilgileri toparla
        # Genelde kullanıcılar "Açıklama" kısmına yazar ama biz config alanlarını da kontrol edelim
        iban = self.config.get('iban') or self.config.get('IBAN')
        bank_name = self.config.get('bank_name') or self.config.get('bankName')
        account_name = self.config.get('account_name') or self.config.get('accountName')
        description = self.config.get('description', '')
        
        # Müşteriye gösterilecek mesaj
        message_parts = [
            "Siparişiniz ödeme yaptıktan kısa bir süre sonra onaylanacaktır.",
            "Lütfen aşağıdaki hesaba ödemenizi yapınız:",
            ""
        ]
        
        if bank_name:
            message_parts.append(f"Banka: {bank_name}")
        if account_name:
            message_parts.append(f"Alıcı: {account_name}")
        if iban:
            message_parts.append(f"IBAN: {iban}")
            
        # Sipariş numarasını açıklama olarak eklemesi gerektiğini hatırlat
        message_parts.append("")
        message_parts.append(f"Lütfen açıklama kısmına sipariş numaranızı ({order.order_number}) yazınız.")
        
        # Eğer config'de özel açıklama varsa onu da ekle (IBANlar orada olabilir)
        if description:
            message_parts.append("")
            message_parts.append("Hesap Bilgileri:")
            message_parts.append(description)
            
        final_message = "\n".join(message_parts)
        
        # Havale için HTML yerine bu mesajı dönebilecek bir yapı kullanıyoruz.
        # Frontend, payment_html içinde bu metni parse edip gösterebilir veya direkt basar.
        # Basit bir HTML template içinde döndürelim ki popup içinde düzgün görünsün.
        payment_html = f"""
        <div class="bank-transfer-info" style="padding: 20px; text-align: center; font-family: sans-serif;">
            <div style="font-size: 48px; color: #4CAF50; margin-bottom: 20px;">✓</div>
            <h2 style="color: #333; margin-bottom: 10px;">Siparişiniz Alındı</h2>
            <p style="font-size: 16px; color: #666; margin-bottom: 20px;">
                {final_message.replace(chr(10), '<br>')}
            </p>
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px; margin-top: 20px; text-align: left;">
                <p><strong>Banka:</strong> {bank_name or '-'}</p>
                <p><strong>Alıcı:</strong> {account_name or '-'}</p>
                <p><strong>IBAN:</strong> {iban or '-'}</p>
                <p><strong>Tutar:</strong> {amount} {getattr(order, 'currency', 'TRY')}</p>
                <p><strong>Açıklama:</strong> {order.order_number}</p>
            </div>
            <p style="margin-top: 20px; font-size: 14px; color: #999;">
                Ödemeniz onaylandıktan sonra siparişiniz işleme alınacaktır.
            </p>
            <button onclick="window.location.href='/order/success/{order.order_number}'" 
                    style="background-color: #4CAF50; color: white; border: none; padding: 10px 20px; 
                           border-radius: 5px; cursor: pointer; margin-top: 20px; font-size: 16px;">
                Siparişi Tamamla
            </button>
        </div>
        """
        
        return {
            'success': True,
            'payment_html': payment_html,
            'transaction_id': f"TRF-{order.order_number}",  # Transfer + Order Number
            'error': None,
            'is_offline': True,  # Frontend'e bunun offline bir yöntem olduğunu belirtmek için
            'offline_message': final_message
        }
        
    def verify_payment(self, transaction_id):
        # Havale ödemesi API ile doğrulanamaz, manuel kontrol gerekir.
        # Ancak sistem akışını bozmamak için 'pending' dönebiliriz.
        return {
            'success': True,
            'status': 'pending', 
            'transaction_id': transaction_id,
            'error': None,
            'message': 'Havale ödemesi manuel onay bekliyor.'
        }
