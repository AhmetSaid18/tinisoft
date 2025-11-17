using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Inventory.Commands.PickOrderItem;

public class PickOrderItemCommandHandler : IRequestHandler<PickOrderItemCommand, PickOrderItemResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<PickOrderItemCommandHandler> _logger;

    public PickOrderItemCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<PickOrderItemCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<PickOrderItemResponse> Handle(PickOrderItemCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // OrderItem'ı bul
        var orderItem = await _dbContext.Set<OrderItem>()
            .Include(oi => oi.Order)
            .Include(oi => oi.Product)
            .FirstOrDefaultAsync(oi => oi.Id == request.OrderItemId, cancellationToken);

        if (orderItem == null)
        {
            throw new NotFoundException("OrderItem", request.OrderItemId);
        }

        if (orderItem.Order == null || orderItem.Order.TenantId != tenantId)
        {
            throw new UnauthorizedException("Bu siparişe erişim yetkiniz yok.");
        }

        // Inventory'yi bul
        var inventory = await _dbContext.Set<ProductInventory>()
            .Include(pi => pi.WarehouseLocation)
            .FirstOrDefaultAsync(pi => 
                pi.ProductId == orderItem.ProductId &&
                pi.WarehouseLocationId == request.WarehouseLocationId &&
                pi.TenantId == tenantId &&
                pi.IsActive, cancellationToken);

        if (inventory == null)
        {
            return new PickOrderItemResponse
            {
                OrderItemId = request.OrderItemId,
                Success = false,
                Message = "Belirtilen lokasyonda ürün bulunamadı."
            };
        }

        if (inventory.AvailableQuantity < request.Quantity)
        {
            return new PickOrderItemResponse
            {
                OrderItemId = request.OrderItemId,
                Success = false,
                Message = $"Yetersiz stok. Mevcut: {inventory.AvailableQuantity}, İstenen: {request.Quantity}"
            };
        }

        // Stok düşür
        inventory.Quantity -= request.Quantity;
        inventory.ReservedQuantity -= request.Quantity; // Rezerve edilmiş stoktan düş

        // OrderItem'ı güncelle
        orderItem.WarehouseId = inventory.WarehouseId;
        orderItem.WarehouseLocationId = request.WarehouseLocationId;
        orderItem.IsPicked = true;
        orderItem.PickedAt = DateTime.UtcNow;
        orderItem.PickedByUserId = request.PickedByUserId;

        // StockMovement kaydı oluştur
        var stockMovement = new StockMovement
        {
            TenantId = tenantId,
            ProductId = orderItem.ProductId,
            ProductVariantId = orderItem.ProductVariantId,
            WarehouseId = inventory.WarehouseId,
            WarehouseLocationId = request.WarehouseLocationId,
            MovementType = "OUT",
            Quantity = -request.Quantity,
            QuantityBefore = inventory.Quantity + request.Quantity,
            QuantityAfter = inventory.Quantity,
            ReferenceId = orderItem.OrderId,
            ReferenceType = "Order",
            ReferenceNumber = orderItem.Order?.OrderNumber,
            Reason = "Sipariş Toplama",
            UserId = request.PickedByUserId
        };

        _dbContext.Set<StockMovement>().Add(stockMovement);

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Order item picked: {OrderItemId} - Quantity: {Quantity} - Location: {Location}",
            request.OrderItemId, request.Quantity, inventory.WarehouseLocation?.LocationCode);

        return new PickOrderItemResponse
        {
            OrderItemId = request.OrderItemId,
            Success = true,
            Message = "Ürün başarıyla toplandı."
        };
    }
}

