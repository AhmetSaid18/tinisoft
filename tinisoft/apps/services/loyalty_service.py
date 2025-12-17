"""
Loyalty service - Sadakat puanları business logic.
İkas benzeri loyalty points sistemi.
"""
from django.db import transaction
from apps.models import LoyaltyProgram, LoyaltyPoints, LoyaltyTransaction, Order
import logging

logger = logging.getLogger(__name__)


class LoyaltyService:
    """Loyalty business logic."""
    
    @staticmethod
    def get_or_create_loyalty_program(tenant):
        """
        Tenant için sadakat programını al veya oluştur.
        
        Args:
            tenant: Tenant instance
        
        Returns:
            LoyaltyProgram: Sadakat programı
        """
        program, created = LoyaltyProgram.objects.get_or_create(
            tenant=tenant,
            defaults={
                'name': 'Sadakat Programı',
                'points_per_currency': 1.00,  # 1 TL = 1 puan
                'points_per_order': 0,  # Her sipariş için ekstra puan yok
                'currency_per_point': 0.01,  # 1 puan = 0.01 TL (100 puan = 1 TL)
                'minimum_points_to_redeem': 100,  # Minimum 100 puan gerekli
            }
        )
        
        if created:
            logger.info(f"Loyalty program created for tenant {tenant.name}")
        
        return program
    
    @staticmethod
    def get_or_create_loyalty_points(tenant, customer):
        """
        Müşteri için sadakat puanlarını al veya oluştur.
        
        Args:
            tenant: Tenant instance
            customer: User instance (TenantUser)
        
        Returns:
            LoyaltyPoints: Müşteri sadakat puanları
        """
        points, created = LoyaltyPoints.objects.get_or_create(
            tenant=tenant,
            customer=customer,
        )
        
        if created:
            logger.info(f"Loyalty points created for customer {customer.email}")
        
        return points
    
    @staticmethod
    @transaction.atomic
    def award_points_for_order(order):
        """
        Sipariş tamamlandığında puan kazandır.
        
        Args:
            order: Order instance
        
        Returns:
            LoyaltyTransaction: Oluşturulan işlem kaydı
        """
        # Sadece ödenmiş siparişler için puan kazandır
        if order.payment_status != Order.PaymentStatus.PAID:
            return None
        
        # Sadece müşteri siparişleri için (guest checkout değil)
        if not order.customer:
            return None
        
        # Sadakat programı aktif mi?
        try:
            program = LoyaltyProgram.objects.get(tenant=order.tenant, is_active=True)
        except LoyaltyProgram.DoesNotExist:
            logger.warning(f"No active loyalty program for tenant {order.tenant.name}")
            return None
        
        # Müşteri sadakat puanlarını al veya oluştur
        loyalty_points = LoyaltyService.get_or_create_loyalty_points(
            order.tenant,
            order.customer
        )
        
        # Kazanılacak puanı hesapla
        points_earned = program.calculate_points_earned(order.total)
        
        if points_earned > 0:
            # Puan ekle
            loyalty_points.add_points(
                points=points_earned,
                reason=f"Sipariş #{order.order_number}"
            )
            
            logger.info(
                f"Points awarded: {points_earned} points to {order.customer.email} "
                f"for order {order.order_number}"
            )
            
            return LoyaltyTransaction.objects.filter(
                loyalty_points=loyalty_points,
                order=order,
                transaction_type='earned'
            ).first()
        
        return None
    
    @staticmethod
    @transaction.atomic
    def use_points_for_order(order, points_to_use):
        """
        Siparişte puan kullan.
        
        Args:
            order: Order instance
            points_to_use: Kullanılacak puan miktarı
        
        Returns:
            dict: {
                'success': bool,
                'discount_amount': Decimal,
                'transaction': LoyaltyTransaction or None,
                'error': str or None
            }
        """
        # Sadece müşteri siparişleri için
        if not order.customer:
            return {
                'success': False,
                'discount_amount': 0,
                'transaction': None,
                'error': 'Guest checkout için puan kullanılamaz.'
            }
        
        # Sadakat programı aktif mi?
        try:
            program = LoyaltyProgram.objects.get(tenant=order.tenant, is_active=True)
        except LoyaltyProgram.DoesNotExist:
            return {
                'success': False,
                'discount_amount': 0,
                'transaction': None,
                'error': 'Sadakat programı aktif değil.'
            }
        
        # Minimum puan kontrolü
        if points_to_use < program.minimum_points_to_redeem:
            return {
                'success': False,
                'discount_amount': 0,
                'transaction': None,
                'error': f'Minimum {program.minimum_points_to_redeem} puan gerekli.'
            }
        
        # Müşteri sadakat puanlarını al
        try:
            loyalty_points = LoyaltyPoints.objects.get(
                tenant=order.tenant,
                customer=order.customer
            )
        except LoyaltyPoints.DoesNotExist:
            return {
                'success': False,
                'discount_amount': 0,
                'transaction': None,
                'error': 'Sadakat puanı bulunamadı.'
            }
        
        # Yeterli puan var mı?
        if points_to_use > loyalty_points.available_points:
            return {
                'success': False,
                'discount_amount': 0,
                'transaction': None,
                'error': f'Yetersiz puan. Mevcut: {loyalty_points.available_points}'
            }
        
        # Maksimum puan kontrolü
        if program.maximum_points_per_order:
            if points_to_use > program.maximum_points_per_order:
                points_to_use = program.maximum_points_per_order
        
        # İndirim tutarını hesapla
        discount_amount = program.calculate_discount_from_points(points_to_use)
        
        # Sipariş tutarından fazla indirim yapılamaz
        if discount_amount > order.subtotal:
            discount_amount = order.subtotal
            # Gerçek kullanılacak puanı yeniden hesapla
            points_to_use = int(discount_amount / program.currency_per_point)
        
        # Puan kullan
        loyalty_points.use_points(
            points=points_to_use,
            reason=f"Sipariş #{order.order_number}"
        )
        
        # İşlem kaydı oluştur
        transaction = LoyaltyTransaction.objects.create(
            loyalty_points=loyalty_points,
            transaction_type='used',
            points=points_to_use,
            order=order,
            reason=f"Sipariş #{order.order_number} - {discount_amount} TL indirim"
        )
        
        logger.info(
            f"Points used: {points_to_use} points ({discount_amount} TL discount) "
            f"by {order.customer.email} for order {order.order_number}"
        )
        
        return {
            'success': True,
            'discount_amount': discount_amount,
            'points_used': points_to_use,
            'transaction': transaction,
            'error': None
        }
    
    @staticmethod
    @transaction.atomic
    def refund_points_for_order(order):
        """
        Sipariş iade edildiğinde puanları geri al.
        
        Args:
            order: Order instance
        
        Returns:
            bool: Başarılı mı?
        """
        # Bu sipariş için kullanılan puanları bul
        used_transactions = LoyaltyTransaction.objects.filter(
            order=order,
            transaction_type='used'
        )
        
        if not used_transactions.exists():
            return True  # Kullanılan puan yok, zaten başarılı
        
        # Her işlem için puanları geri ver
        for transaction in used_transactions:
            loyalty_points = transaction.loyalty_points
            
            # Puanları geri ekle
            loyalty_points.available_points += transaction.points
            loyalty_points.used_points -= transaction.points
            loyalty_points.save()
            
            # İade işlem kaydı oluştur
            LoyaltyTransaction.objects.create(
                loyalty_points=loyalty_points,
                transaction_type='refunded',
                points=transaction.points,
                order=order,
                reason=f"Sipariş iadesi - {order.order_number}"
            )
            
            logger.info(
                f"Points refunded: {transaction.points} points to {loyalty_points.customer.email} "
                f"for order {order.order_number}"
            )
        
        return True

