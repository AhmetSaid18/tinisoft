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
        """Ödemeyi işle (başarılı)."""
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

