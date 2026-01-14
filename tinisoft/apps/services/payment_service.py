"""
Payment service - Business logic for payments.
"""
from django.utils import timezone
from decimal import Decimal
import uuid
import logging
from apps.models import Payment, Order

logger = logging.getLogger(__name__)


class PaymentService:
    """Payment business logic."""
    
    @staticmethod
    def generate_payment_number(tenant):
        """Benzersiz ödeme numarası oluştur."""
        timestamp = int(timezone.now().timestamp())
        random_part = str(uuid.uuid4())[:8].upper()
        return f"PAY-{tenant.slug.upper()}-{timestamp}-{random_part}"
    
    @staticmethod
    def create_payment(order, method, amount, provider=None, metadata=None):
        """
        Ödeme oluştur.
        
        Args:
            order: Order instance
            method: Payment method
            amount: Ödeme tutarı
            provider: Ödeme sağlayıcı (iyzico, paytr, vb.)
            metadata: Ek bilgiler
        
        Returns:
            Payment: Oluşturulan ödeme
        """
        payment_number = PaymentService.generate_payment_number(order.tenant)
        
        payment = Payment.objects.create(
            tenant=order.tenant,
            order=order,
            payment_number=payment_number,
            method=method,
            amount=amount,
            currency=order.currency,
            provider=provider or '',
            metadata=metadata or {},
        )
        
        logger.info(f"Payment created: {payment_number} for order {order.order_number}")
        return payment
    
    @staticmethod
    def process_payment(payment, transaction_id=None, payment_intent_id=None):
        """
        Ödemeyi işle (başarılı).
        Havale/EFT gibi offline ödemeler için PENDING statüsünde kalabilir.
        """
        # Bank Transfer ise Pending kalmalı (manuel onay için)
        if payment.provider == 'bank_transfer' or payment.method == Payment.PaymentMethod.BANK_TRANSFER:
            payment.status = Payment.PaymentStatus.PENDING
            # Transaction ID varsa kaydet
            if transaction_id:
                payment.transaction_id = transaction_id
            payment.save()
            
            # Sipariş durumunu da PENDING (Ödeme Bekliyor) olarak güncelle
            from apps.services.order_service import OrderService
            # Sipariş statusunu da güncellemek gerekebilir (OrderService içinde halledilmeli)
            # Ancak Order.PaymentStatus.PENDING zaten varsayılan, biz yine de emin olalım
            OrderService.update_payment_status(payment.order, Order.PaymentStatus.PENDING)
            
            logger.info(f"Payment pending (Bank Transfer): {payment.payment_number}")
            return payment
            
        payment.status = Payment.PaymentStatus.COMPLETED
        payment.transaction_id = transaction_id or ''
        payment.payment_intent_id = payment_intent_id or ''
        payment.paid_at = timezone.now()
        payment.save()
        
        # Sipariş ödeme durumunu güncelle
        from apps.services.order_service import OrderService
        OrderService.update_payment_status(payment.order, Order.PaymentStatus.PAID)
        
        logger.info(f"Payment completed: {payment.payment_number}")
        return payment

    @staticmethod
    def confirm_payment(payment, user=None):
        """
        Manuel ödeme onayı (Havale/EFT için).
        """
        if payment.status == Payment.PaymentStatus.COMPLETED:
            raise ValueError("Bu ödeme zaten onaylanmış.")
            
        payment.status = Payment.PaymentStatus.COMPLETED
        payment.paid_at = timezone.now()
        
        # Onaylayan kullanıcıyı logla (metadata)
        if user:
            if not payment.metadata:
                payment.metadata = {}
            payment.metadata['confirmed_by'] = str(user.id)
            payment.metadata['confirmed_at'] = str(timezone.now())
            
        payment.save()
        
        # Sipariş ödeme durumunu güncelle
        from apps.services.order_service import OrderService
        OrderService.update_payment_status(payment.order, Order.PaymentStatus.PAID)
        
        logger.info(f"Payment confirmed manually: {payment.payment_number}")
        return payment
    
    @staticmethod
    def fail_payment(payment, error_message='', error_code=''):
        """Ödemeyi başarısız olarak işaretle."""
        payment.status = Payment.PaymentStatus.FAILED
        payment.error_message = error_message
        payment.error_code = error_code
        payment.failed_at = timezone.now()
        payment.save()
        
        logger.warning(f"Payment failed: {payment.payment_number} - {error_message}")
        return payment
    
    @staticmethod
    def refund_payment(payment, amount=None):
        """Ödemeyi iade et."""
        refund_amount = amount or payment.amount
        
        if payment.status != Payment.PaymentStatus.COMPLETED:
            raise ValueError("Sadece tamamlanmış ödemeler iade edilebilir.")
        
        if refund_amount > payment.amount:
            raise ValueError("İade tutarı ödeme tutarından fazla olamaz.")
        
        if refund_amount == payment.amount:
            payment.status = Payment.PaymentStatus.REFUNDED
            from apps.services.order_service import OrderService
            OrderService.update_payment_status(payment.order, Order.PaymentStatus.REFUNDED)
        else:
            payment.status = Payment.PaymentStatus.PARTIALLY_REFUNDED
        
        payment.refunded_at = timezone.now()
        payment.save()
        
        logger.info(f"Payment refunded: {payment.payment_number} - Amount: {refund_amount}")
        return payment

