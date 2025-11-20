using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Inventory.Queries.GetStockLevel;

public class GetStockLevelQueryHandler : IRequestHandler<GetStockLevelQuery, GetStockLevelResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;

    public GetStockLevelQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
    }

    public async Task<GetStockLevelResponse> Handle(GetStockLevelQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        if (request.VariantId.HasValue)
        {
            var variant = await _dbContext.ProductVariants
                .FirstOrDefaultAsync(v => 
                    v.Id == request.VariantId.Value && 
                    v.TenantId == tenantId, cancellationToken);

            if (variant == null)
            {
                throw new KeyNotFoundException($"Varyant bulunamadı: {request.VariantId}");
            }

            return new GetStockLevelResponse
            {
                ProductId = variant.ProductId,
                VariantId = variant.Id,
                Quantity = variant.InventoryQuantity,
                TrackInventory = variant.TrackInventory,
                IsLowStock = variant.TrackInventory && variant.InventoryQuantity.HasValue && variant.InventoryQuantity < 10 // Örnek eşik
            };
        }
        else
        {
            var product = await _dbContext.Products
                .FirstOrDefaultAsync(p => 
                    p.Id == request.ProductId && 
                    p.TenantId == tenantId, cancellationToken);

            if (product == null)
            {
                throw new KeyNotFoundException($"Ürün bulunamadı: {request.ProductId}");
            }

            return new GetStockLevelResponse
            {
                ProductId = product.Id,
                Quantity = product.InventoryQuantity,
                TrackInventory = product.TrackInventory,
                IsLowStock = product.TrackInventory && product.InventoryQuantity.HasValue && product.InventoryQuantity < 10 // Örnek eşik
            };
        }
    }
}



