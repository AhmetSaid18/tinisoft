@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def order_delete(request, order_id):
    """
    Siparişi kalıcı olarak sil (Hard Delete).
    DİKKAT: Bu işlem geri alınamaz.
    Sadece Tenant Owner veya Owner yapabilir.
    
    DELETE: /api/orders/{order_id}/delete/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Sadece tenant'a ait siparişi bul
        order = Order.objects.get(id=order_id, tenant=tenant)
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Sipariş bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Permission kontrolü
    # SADECE TenantOwner veya Owner silebilir
    # TenantUser veya Customer silemez
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok. Sadece mağaza sahibi sipariş silebilir.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Siparişi Hard Delete ile sil
        # Not: OrderItem ve Payment modelleri cascade ile silinir.
        # InventoryMovement kayıtları SET_NULL olur, silinmez.
        order_number = order.order_number
        order.delete()
        
        logger.info(
            f"[ORDERS] DELETE /api/orders/{order_id}/delete/ | 200 | "
            f"Order deleted permanently: {order_number} | "
            f"User: {request.user.email} | "
            f"Tenant: {tenant.name}"
        )
        
        return Response({
            'success': True,
            'message': f'Sipariş ({order_number}) kalıcı olarak silindi.',
        })
        
    except Exception as e:
        logger.error(
            f"[ORDERS] DELETE /api/orders/{order_id}/delete/ | 500 | "
            f"Error deleting order: {str(e)} | "
            f"User: {request.user.email} | "
            f"Tenant: {tenant.name}",
            exc_info=True
        )
        return Response({
            'success': False,
            'message': 'Sipariş silinirken bir hata oluştu.',
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
