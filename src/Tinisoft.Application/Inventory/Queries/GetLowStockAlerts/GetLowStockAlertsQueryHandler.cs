using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Inventory.Queries.GetLowStockAlerts;

public class GetLowStockAlertsQueryHandler : IRequestHandler<GetLowStockAlertsQuery, GetLowStockAlertsResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetLowStockAlertsQueryHandler> _logger;

    public GetLowStockAlertsQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetLowStockAlertsQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetLowStockAlertsResponse> Handle(GetLowStockAlertsQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var query = _dbContext.Set<Domain.Entities.ProductInventory>()
            .AsNoTracking()
            .Include(pi => pi.Product)
            .Include(pi => pi.Warehouse)
            .Include(pi => pi.WarehouseLocation)
            .Where(pi => 
                pi.TenantId == tenantId &&
                pi.IsActive &&
                pi.Product != null &&
                pi.Product.TrackInventory);

        if (request.WarehouseId.HasValue)
        {
            query = query.Where(pi => pi.WarehouseId == request.WarehouseId.Value);
        }

        // MinStockLevel kontrolü - ya min level'a düşmüş ya da stokta yok
        query = query.Where(pi => 
            (pi.MinStockLevel.HasValue && pi.AvailableQuantity <= pi.MinStockLevel.Value) ||
            (!pi.MinStockLevel.HasValue && pi.AvailableQuantity <= 0) ||
            (request.OnlyCritical && pi.AvailableQuantity == 0));

        var inventories = await query
            .OrderBy(pi => pi.AvailableQuantity)
            .ThenBy(pi => pi.Product != null ? pi.Product.Title : "")
            .ToListAsync(cancellationToken);

        var alerts = inventories.Select(pi => new LowStockAlertDto
        {
            ProductId = pi.ProductId,
            ProductTitle = pi.Product?.Title ?? "Bilinmeyen Ürün",
            ProductSKU = pi.Product?.SKU,
            WarehouseId = pi.WarehouseId,
            WarehouseName = pi.Warehouse?.Name ?? "Bilinmeyen Depo",
            WarehouseLocationId = pi.WarehouseLocationId,
            LocationCode = pi.WarehouseLocation?.LocationCode,
            CurrentQuantity = pi.Quantity,
            AvailableQuantity = pi.AvailableQuantity,
            ReservedQuantity = pi.ReservedQuantity,
            MinStockLevel = pi.MinStockLevel,
            MaxStockLevel = pi.MaxStockLevel,
            IsCritical = pi.AvailableQuantity == 0
        }).ToList();

        return new GetLowStockAlertsResponse
        {
            Alerts = alerts,
            TotalCount = alerts.Count
        };
    }
}



