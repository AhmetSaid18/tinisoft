using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Inventory.Commands.TransferStock;

public class TransferStockCommandHandler : IRequestHandler<TransferStockCommand, TransferStockResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<TransferStockCommandHandler> _logger;

    public TransferStockCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<TransferStockCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<TransferStockResponse> Handle(TransferStockCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Kaynak inventory'yi bul
        var fromInventory = await _dbContext.Set<ProductInventory>()
            .Include(pi => pi.Warehouse)
            .Include(pi => pi.WarehouseLocation)
            .FirstOrDefaultAsync(pi => 
                pi.ProductId == request.ProductId &&
                pi.WarehouseId == request.FromWarehouseId &&
                (request.FromWarehouseLocationId == null || pi.WarehouseLocationId == request.FromWarehouseLocationId) &&
                pi.TenantId == tenantId &&
                pi.IsActive, cancellationToken);

        if (fromInventory == null)
        {
            return new TransferStockResponse
            {
                Success = false,
                Message = "Kaynak lokasyonda ürün bulunamadı."
            };
        }

        if (fromInventory.AvailableQuantity < request.Quantity)
        {
            return new TransferStockResponse
            {
                Success = false,
                Message = $"Yetersiz stok. Mevcut: {fromInventory.AvailableQuantity}, İstenen: {request.Quantity}"
            };
        }

        // Hedef inventory'yi bul veya oluştur
        var toInventory = await _dbContext.Set<ProductInventory>()
            .FirstOrDefaultAsync(pi => 
                pi.ProductId == request.ProductId &&
                pi.WarehouseId == request.ToWarehouseId &&
                (request.ToWarehouseLocationId == null || pi.WarehouseLocationId == request.ToWarehouseLocationId) &&
                pi.TenantId == tenantId &&
                pi.IsActive, cancellationToken);

        if (toInventory == null)
        {
            // Yeni inventory kaydı oluştur
            var product = await _dbContext.Set<Product>()
                .FirstOrDefaultAsync(p => p.Id == request.ProductId && p.TenantId == tenantId, cancellationToken);

            if (product == null)
            {
                throw new NotFoundException("Product", request.ProductId);
            }

            toInventory = new ProductInventory
            {
                TenantId = tenantId,
                ProductId = request.ProductId,
                WarehouseId = request.ToWarehouseId,
                WarehouseLocationId = request.ToWarehouseLocationId,
                Quantity = 0,
                ReservedQuantity = 0,
                Cost = fromInventory.Cost, // Maliyeti kaynaktan kopyala
                InventoryMethod = fromInventory.InventoryMethod,
                LotNumber = fromInventory.LotNumber,
                ExpiryDate = fromInventory.ExpiryDate,
                ManufactureDate = fromInventory.ManufactureDate,
                IsActive = true
            };

            _dbContext.Set<ProductInventory>().Add(toInventory);
        }

        // Stok transferi
        fromInventory.Quantity -= request.Quantity;
        toInventory.Quantity += request.Quantity;

        // StockMovement kayıtları oluştur (hem kaynak hem hedef için)
        
        // Kaynak için OUT kaydı
        var fromMovement = new StockMovement
        {
            TenantId = tenantId,
            ProductId = request.ProductId,
            ProductVariantId = request.ProductVariantId,
            WarehouseId = request.FromWarehouseId,
            WarehouseLocationId = request.FromWarehouseLocationId,
            MovementType = "TRANSFER",
            Quantity = -request.Quantity,
            QuantityBefore = fromInventory.Quantity + request.Quantity,
            QuantityAfter = fromInventory.Quantity,
            ReferenceType = "Transfer",
            Reason = request.Reason ?? "Depo Arası Transfer",
            Notes = $"Transfer to Warehouse: {request.ToWarehouseId}",
            UserId = request.UserId
        };

        // Hedef için IN kaydı
        var toMovement = new StockMovement
        {
            TenantId = tenantId,
            ProductId = request.ProductId,
            ProductVariantId = request.ProductVariantId,
            WarehouseId = request.ToWarehouseId,
            WarehouseLocationId = request.ToWarehouseLocationId,
            MovementType = "TRANSFER",
            Quantity = request.Quantity,
            QuantityBefore = toInventory.Quantity - request.Quantity,
            QuantityAfter = toInventory.Quantity,
            ReferenceType = "Transfer",
            Reason = request.Reason ?? "Depo Arası Transfer",
            Notes = $"Transfer from Warehouse: {request.FromWarehouseId}",
            UserId = request.UserId
        };

        _dbContext.Set<StockMovement>().Add(fromMovement);
        _dbContext.Set<StockMovement>().Add(toMovement);

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Stock transferred: Product {ProductId} - From: {FromWarehouse} To: {ToWarehouse} - Quantity: {Quantity}",
            request.ProductId, request.FromWarehouseId, request.ToWarehouseId, request.Quantity);

        return new TransferStockResponse
        {
            Success = true,
            Message = "Stok transferi başarıyla tamamlandı.",
            FromInventoryId = fromInventory.Id,
            ToInventoryId = toInventory.Id
        };
    }
}



