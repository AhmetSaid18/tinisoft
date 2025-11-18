using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Inventory.Queries.GetWarehouseStock;

public class GetWarehouseStockQueryHandler : IRequestHandler<GetWarehouseStockQuery, GetWarehouseStockResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetWarehouseStockQueryHandler> _logger;

    public GetWarehouseStockQueryHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetWarehouseStockQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetWarehouseStockResponse> Handle(GetWarehouseStockQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var query = _dbContext.Set<Domain.Entities.ProductInventory>()
            .AsNoTracking()
            .Include(pi => pi.Product)
            .Include(pi => pi.Warehouse)
            .Include(pi => pi.WarehouseLocation)
            .Where(pi => pi.TenantId == tenantId && pi.IsActive);

        if (request.WarehouseId.HasValue)
        {
            query = query.Where(pi => pi.WarehouseId == request.WarehouseId.Value);
        }

        if (request.ProductId.HasValue)
        {
            query = query.Where(pi => pi.ProductId == request.ProductId.Value);
        }

        if (request.OnlyLowStock)
        {
            query = query.Where(pi => 
                (pi.MinStockLevel.HasValue && pi.AvailableQuantity <= pi.MinStockLevel.Value) ||
                (!pi.MinStockLevel.HasValue && pi.AvailableQuantity <= 0));
        }

        var totalCount = await query.CountAsync(cancellationToken);

        var inventories = await query
            .OrderBy(pi => pi.Warehouse != null ? pi.Warehouse.Name : "")
            .ThenBy(pi => pi.Product != null ? pi.Product.Title : "")
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
            .Select(pi => new WarehouseStockDto
            {
                ProductInventoryId = pi.Id,
                ProductId = pi.ProductId,
                ProductTitle = pi.Product != null ? pi.Product.Title : "Bilinmeyen Ürün",
                ProductSKU = pi.Product != null ? pi.Product.SKU : null,
                WarehouseId = pi.WarehouseId,
                WarehouseName = pi.Warehouse != null ? pi.Warehouse.Name : "Bilinmeyen Depo",
                WarehouseLocationId = pi.WarehouseLocationId,
                LocationCode = pi.WarehouseLocation != null ? pi.WarehouseLocation.LocationCode : null,
                Zone = pi.WarehouseLocation != null ? pi.WarehouseLocation.Zone : null,
                Aisle = pi.WarehouseLocation != null ? pi.WarehouseLocation.Aisle : null,
                Rack = pi.WarehouseLocation != null ? pi.WarehouseLocation.Rack : null,
                Shelf = pi.WarehouseLocation != null ? pi.WarehouseLocation.Shelf : null,
                Level = pi.WarehouseLocation != null ? pi.WarehouseLocation.Level : null,
                Quantity = pi.Quantity,
                ReservedQuantity = pi.ReservedQuantity,
                AvailableQuantity = pi.AvailableQuantity,
                MinStockLevel = pi.MinStockLevel,
                MaxStockLevel = pi.MaxStockLevel,
                IsLowStock = (pi.MinStockLevel.HasValue && pi.AvailableQuantity <= pi.MinStockLevel.Value) ||
                            (!pi.MinStockLevel.HasValue && pi.AvailableQuantity <= 0),
                InventoryMethod = pi.InventoryMethod,
                LotNumber = pi.LotNumber,
                ExpiryDate = pi.ExpiryDate,
                ManufactureDate = pi.ManufactureDate,
                Cost = pi.Cost
            })
            .ToListAsync(cancellationToken);

        return new GetWarehouseStockResponse
        {
            Items = inventories,
            TotalCount = totalCount,
            Page = request.Page,
            PageSize = request.PageSize
        };
    }
}

