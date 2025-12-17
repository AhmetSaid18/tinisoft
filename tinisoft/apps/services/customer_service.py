"""
Customer service - Business logic for customers.
"""
from apps.models import Customer, User
import logging

logger = logging.getLogger(__name__)


class CustomerService:
    """Customer business logic."""
    
    @staticmethod
    def get_or_create_customer(tenant, user):
        """
        Müşteri profilini al veya oluştur.
        
        Args:
            tenant: Tenant instance
            user: User instance (TenantUser)
        
        Returns:
            Customer: Müşteri profili
        """
        if user.role != User.UserRole.TENANT_USER:
            raise ValueError("Sadece TenantUser rolündeki kullanıcılar için müşteri profili oluşturulabilir.")
        
        customer, created = Customer.objects.get_or_create(
            tenant=tenant,
            user=user,
            defaults={
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'phone': user.phone or '',
            }
        )
        
        if created:
            logger.info(f"Customer profile created for user {user.email}")
        
        return customer
    
    @staticmethod
    def update_customer_statistics(customer):
        """Müşteri istatistiklerini güncelle."""
        customer.update_statistics()
        logger.info(f"Customer statistics updated for {customer.user.email}")

