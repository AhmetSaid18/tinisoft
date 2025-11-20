using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Inventory.Commands.CountInventory;

public class CountInventoryCommandHandler : IRequestHandler<CountInventoryCommand, CountInventoryResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CountInventoryCommandHandler> _logger;

    public CountInventoryCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CountInventoryCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CountInventoryResponse> Handle(CountInventoryCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var inventory = await _dbContext.Set<Domain.Entities.ProductInventory>()
            .Include(pi => pi.Product)
            .Include(pi => pi.Warehouse)
            .Include(pi => pi.WarehouseLocation)
            .FirstOrDefaultAsync(pi => 
                pi.Id == request.ProductInventoryId && 
                pi.TenantId == tenantId, cancellationToken);

        if (inventory == null)
        {
            throw new NotFoundException("ProductInventory", request.ProductInventoryId);
        }

        var previousQuantity = inventory.Quantity;
        var difference = request.CountedQuantity - previousQuantity;

        // Stok güncelle
        inventory.Quantity = request.CountedQuantity;
        // ReservedQuantity'yi de güncelle (eğer sayım sonucu rezerve edilmiş stoktan azsa)
        if (inventory.Quantity < inventory.ReservedQuantity)
        {
            inventory.ReservedQuantity = inventory.Quantity; // Rezerve edilmiş stok fazla olamaz
        }

        // StockMovement kaydı oluştur (ADJUSTMENT)
        var stockMovement = new Domain.Entities.StockMovement
        {
            TenantId = tenantId,
            ProductId = inventory.ProductId,
            WarehouseId = inventory.WarehouseId,
            WarehouseLocationId = inventory.WarehouseLocationId,
            MovementType = "ADJUSTMENT",
            Quantity = difference,
            QuantityBefore = previousQuantity,
            QuantityAfter = request.CountedQuantity,
            ReferenceType = "InventoryCount",
            Reason = "Stok Sayımı",
            Notes = request.Notes ?? $"Fiziksel sayım: {request.CountedQuantity}, Sistem: {previousQuantity}, Fark: {difference}",
            UserId = request.CountedByUserId
        };

        _dbContext.Set<Domain.Entities.StockMovement>().Add(stockMovement);

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Inventory counted: ProductInventory {ProductInventoryId} - Previous: {PreviousQuantity}, Counted: {CountedQuantity}, Difference: {Difference}",
            request.ProductInventoryId, previousQuantity, request.CountedQuantity, difference);

        return new CountInventoryResponse
        {
            ProductInventoryId = inventory.Id,
            PreviousQuantity = previousQuantity,
            CountedQuantity = request.CountedQuantity,
            Difference = difference,
            Success = true,
            Message = difference != 0 
                ? $"Stok güncellendi. Fark: {difference} adet"
                : "Stok sayımı tamamlandı. Fark yok."
        };
    }
}



