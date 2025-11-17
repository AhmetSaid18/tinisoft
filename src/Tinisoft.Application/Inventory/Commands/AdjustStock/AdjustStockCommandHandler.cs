using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Inventory.Commands.AdjustStock;

public class AdjustStockCommandHandler : IRequestHandler<AdjustStockCommand, AdjustStockResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IEventBus _eventBus;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<AdjustStockCommandHandler> _logger;

    public AdjustStockCommandHandler(
        ApplicationDbContext dbContext,
        IEventBus eventBus,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<AdjustStockCommandHandler> logger)
    {
        _dbContext = dbContext;
        _eventBus = eventBus;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<AdjustStockResponse> Handle(AdjustStockCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        if (request.VariantId.HasValue)
        {
            // Variant stock adjustment
            var variant = await _dbContext.ProductVariants
                .FirstOrDefaultAsync(v => 
                    v.Id == request.VariantId.Value && 
                    v.TenantId == tenantId, cancellationToken);

            if (variant == null)
            {
                throw new KeyNotFoundException($"Varyant bulunamadı: {request.VariantId}");
            }

            if (!variant.TrackInventory)
            {
                throw new InvalidOperationException("Bu varyant için stok takibi yapılmıyor");
            }

            var oldQuantity = variant.InventoryQuantity ?? 0;
            var newQuantity = oldQuantity + request.QuantityChange;

            if (newQuantity < 0)
            {
                throw new InvalidOperationException("Stok miktarı negatif olamaz");
            }

            variant.InventoryQuantity = newQuantity;
            variant.UpdatedAt = DateTime.UtcNow;

            await _dbContext.SaveChangesAsync(cancellationToken);

            // Event publish
            await _eventBus.PublishAsync(new ProductStockChangedEvent
            {
                ProductId = variant.ProductId,
                VariantId = variant.Id,
                TenantId = tenantId,
                OldQuantity = oldQuantity,
                NewQuantity = newQuantity,
                Reason = request.Reason
            }, cancellationToken);

            return new AdjustStockResponse
            {
                ProductId = variant.ProductId,
                VariantId = variant.Id,
                OldQuantity = oldQuantity,
                NewQuantity = newQuantity
            };
        }
        else
        {
            // Product stock adjustment
            var product = await _dbContext.Products
                .FirstOrDefaultAsync(p => 
                    p.Id == request.ProductId && 
                    p.TenantId == tenantId, cancellationToken);

            if (product == null)
            {
                throw new KeyNotFoundException($"Ürün bulunamadı: {request.ProductId}");
            }

            if (!product.TrackInventory)
            {
                throw new InvalidOperationException("Bu ürün için stok takibi yapılmıyor");
            }

            var oldQuantity = product.InventoryQuantity ?? 0;
            var newQuantity = oldQuantity + request.QuantityChange;

            if (newQuantity < 0)
            {
                throw new InvalidOperationException("Stok miktarı negatif olamaz");
            }

            product.InventoryQuantity = newQuantity;
            product.UpdatedAt = DateTime.UtcNow;

            await _dbContext.SaveChangesAsync(cancellationToken);

            // Event publish
            await _eventBus.PublishAsync(new ProductStockChangedEvent
            {
                ProductId = product.Id,
                TenantId = tenantId,
                OldQuantity = oldQuantity,
                NewQuantity = newQuantity,
                Reason = request.Reason
            }, cancellationToken);

            return new AdjustStockResponse
            {
                ProductId = product.Id,
                OldQuantity = oldQuantity,
                NewQuantity = newQuantity
            };
        }
    }
}

