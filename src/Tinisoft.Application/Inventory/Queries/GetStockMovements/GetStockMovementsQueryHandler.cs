using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Inventory.Queries.GetStockMovements;

public class GetStockMovementsQueryHandler : IRequestHandler<GetStockMovementsQuery, GetStockMovementsResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetStockMovementsQueryHandler> _logger;

    public GetStockMovementsQueryHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetStockMovementsQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetStockMovementsResponse> Handle(GetStockMovementsQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var query = _dbContext.Set<Domain.Entities.StockMovement>()
            .AsNoTracking()
            .Include(sm => sm.Product)
            .Include(sm => sm.Warehouse)
            .Include(sm => sm.WarehouseLocation)
            .Include(sm => sm.User)
            .Where(sm => sm.TenantId == tenantId);

        // Filtreler
        if (request.ProductId.HasValue)
        {
            query = query.Where(sm => sm.ProductId == request.ProductId.Value);
        }

        if (request.WarehouseId.HasValue)
        {
            query = query.Where(sm => sm.WarehouseId == request.WarehouseId.Value);
        }

        if (request.WarehouseLocationId.HasValue)
        {
            query = query.Where(sm => sm.WarehouseLocationId == request.WarehouseLocationId.Value);
        }

        if (!string.IsNullOrEmpty(request.MovementType))
        {
            query = query.Where(sm => sm.MovementType == request.MovementType);
        }

        if (request.FromDate.HasValue)
        {
            query = query.Where(sm => sm.CreatedAt >= request.FromDate.Value);
        }

        if (request.ToDate.HasValue)
        {
            query = query.Where(sm => sm.CreatedAt <= request.ToDate.Value);
        }

        var totalCount = await query.CountAsync(cancellationToken);

        var movements = await query
            .OrderByDescending(sm => sm.CreatedAt)
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
            .Select(sm => new StockMovementDto
            {
                Id = sm.Id,
                ProductId = sm.ProductId,
                ProductTitle = sm.Product != null ? sm.Product.Title : null,
                ProductSKU = sm.Product != null ? sm.Product.SKU : null,
                ProductVariantId = sm.ProductVariantId,
                WarehouseId = sm.WarehouseId,
                WarehouseName = sm.Warehouse != null ? sm.Warehouse.Name : null,
                WarehouseLocationId = sm.WarehouseLocationId,
                LocationCode = sm.WarehouseLocation != null ? sm.WarehouseLocation.LocationCode : null,
                MovementType = sm.MovementType,
                Quantity = sm.Quantity,
                QuantityBefore = sm.QuantityBefore,
                QuantityAfter = sm.QuantityAfter,
                ReferenceId = sm.ReferenceId,
                ReferenceType = sm.ReferenceType,
                ReferenceNumber = sm.ReferenceNumber,
                Reason = sm.Reason,
                Notes = sm.Notes,
                UserId = sm.UserId,
                UserName = sm.User != null ? $"{sm.User.FirstName} {sm.User.LastName}".Trim() : null,
                UnitCost = sm.UnitCost,
                TotalCost = sm.TotalCost,
                CreatedAt = sm.CreatedAt
            })
            .ToListAsync(cancellationToken);

        return new GetStockMovementsResponse
        {
            Movements = movements,
            TotalCount = totalCount,
            Page = request.Page,
            PageSize = request.PageSize
        };
    }
}

