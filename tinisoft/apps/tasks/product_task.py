"""
Celery tasks for product operations.
"""
from celery import shared_task
from decimal import Decimal
from django.db import models
from apps.models import Product, Tax, Tenant
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_all_products_price_with_vat(tenant_id: str):
    """
    Tenant'a ait tüm ürünlerin KDV dahil fiyatlarını güncelle.
    Background task olarak çalışır.
    
    Args:
        tenant_id: Tenant ID (string veya UUID)
    """
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        logger.error(f"Tenant not found: {tenant_id}")
        return {
            'success': False,
            'error': f'Tenant not found: {tenant_id}',
        }
    
    # Tenant'ın aktif ve varsayılan Tax'ını bul
    active_tax = Tax.objects.filter(
        tenant=tenant,
        is_active=True,
        is_deleted=False
    ).order_by('-is_default', '-created_at').first()
    
    if not active_tax:
        logger.warning(f"No active tax found for tenant: {tenant.name} ({tenant_id})")
        # Aktif Tax yoksa, tüm ürünlerin price_with_vat = price yap
        products = Product.objects.filter(
            tenant=tenant,
            is_deleted=False
        )
        updated_count = 0
        for product in products:
            product.price_with_vat = product.price
            Product.objects.filter(id=product.id).update(price_with_vat=product.price)
            updated_count += 1
        
        return {
            'success': True,
            'tenant_id': str(tenant_id),
            'tenant_name': tenant.name,
            'updated_count': updated_count,
            'message': f'No active tax found. Updated {updated_count} products with price_with_vat = price',
        }
    
    # Tüm ürünleri al ve güncelle
    products = Product.objects.filter(
        tenant=tenant,
        is_deleted=False
    )
    
    updated_count = 0
    for product in products:
        try:
            # KDV dahil fiyat hesapla
            if active_tax.rate and active_tax.rate > 0:
                # KDV dahil fiyat = Fiyat * (1 + KDV oranı / 100)
                # Örnek: 100 TL * (1 + 20/100) = 100 * 1.20 = 120 TL
                product.price_with_vat = product.price * (Decimal('1') + (active_tax.rate / Decimal('100')))
            else:
                # Oran 0 ise, KDV dahil fiyat = normal fiyat
                product.price_with_vat = product.price
            
            # Sadece price_with_vat field'ını güncelle (save() metodunu çağırmadan)
            Product.objects.filter(id=product.id).update(price_with_vat=product.price_with_vat)
            updated_count += 1
            
        except Exception as e:
            logger.error(f"Error updating product {product.id}: {str(e)}")
            continue
    
    logger.info(
        f"Updated {updated_count} products' price_with_vat for tenant: {tenant.name} ({tenant_id}) "
        f"with tax rate: {active_tax.rate}%"
    )
    
    return {
        'success': True,
        'tenant_id': str(tenant_id),
        'tenant_name': tenant.name,
        'tax_rate': float(active_tax.rate),
        'tax_name': active_tax.name,
        'updated_count': updated_count,
        'total_products': products.count(),
    }

