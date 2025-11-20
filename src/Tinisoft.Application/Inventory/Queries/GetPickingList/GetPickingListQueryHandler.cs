using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Inventory.Queries.GetPickingList;

public class GetPickingListQueryHandler : IRequestHandler<GetPickingListQuery, GetPickingListResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetPickingListQueryHandler> _logger;

    public GetPickingListQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetPickingListQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetPickingListResponse> Handle(GetPickingListQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Order'ı bul
        var order = await _dbContext.Set<Order>()
            .Include(o => o.OrderItems)
                .ThenInclude(oi => oi.PickedByUser)
            .FirstOrDefaultAsync(o => o.Id == request.OrderId && o.TenantId == tenantId, cancellationToken);

        if (order == null)
        {
            throw new NotFoundException("Order", request.OrderId);
        }

        var pickingItems = new List<PickingItem>();

        foreach (var orderItem in order.OrderItems)
        {
            // Ürün için en uygun lokasyonu bul (FIFO/LIFO mantığı ile)
            var inventory = await _dbContext.Set<ProductInventory>()
                .Include(pi => pi.Warehouse)
                .Include(pi => pi.WarehouseLocation)
                .Where(pi => 
                    pi.ProductId == orderItem.ProductId &&
                    pi.TenantId == tenantId &&
                    pi.IsActive &&
                    pi.AvailableQuantity >= orderItem.Quantity)
                .OrderBy(pi => pi.InventoryMethod == "FIFO" ? pi.CreatedAt : DateTime.MaxValue) // FIFO için en eski
                .ThenByDescending(pi => pi.InventoryMethod == "LIFO" ? pi.CreatedAt : DateTime.MinValue) // LIFO için en yeni
                .ThenBy(pi => pi.ExpiryDate ?? DateTime.MaxValue) // FEFO için son kullanma tarihi
                .FirstOrDefaultAsync(cancellationToken);

            if (inventory == null)
            {
                // Stok yoksa yine de listeye ekle (uyarı için)
                pickingItems.Add(new PickingItem
                {
                    OrderItemId = orderItem.Id,
                    ProductId = orderItem.ProductId,
                    ProductTitle = orderItem.Title,
                    SKU = orderItem.SKU,
                    Quantity = orderItem.Quantity,
                    AvailableQuantity = 0,
                    IsPicked = orderItem.IsPicked,
                    PickedAt = orderItem.PickedAt
                });
                continue;
            }

            // Lokasyon bilgilerini al
            var locationCode = inventory.WarehouseLocation != null
                ? BuildLocationCode(inventory.WarehouseLocation)
                : inventory.Location;

            pickingItems.Add(new PickingItem
            {
                OrderItemId = orderItem.Id,
                ProductId = orderItem.ProductId,
                ProductTitle = orderItem.Title,
                SKU = orderItem.SKU,
                Quantity = orderItem.Quantity,
                WarehouseId = inventory.WarehouseId,
                WarehouseName = inventory.Warehouse?.Name ?? "Bilinmeyen Depo",
                WarehouseLocationId = inventory.WarehouseLocationId,
                LocationCode = locationCode,
                Zone = inventory.WarehouseLocation?.Zone,
                Aisle = inventory.WarehouseLocation?.Aisle,
                Rack = inventory.WarehouseLocation?.Rack,
                Shelf = inventory.WarehouseLocation?.Shelf,
                Level = inventory.WarehouseLocation?.Level,
                AvailableQuantity = inventory.AvailableQuantity,
                IsPicked = orderItem.IsPicked,
                PickedAt = orderItem.PickedAt,
                PickedByUserName = orderItem.PickedByUser != null 
                    ? $"{orderItem.PickedByUser.FirstName} {orderItem.PickedByUser.LastName}".Trim()
                    : null
            });
        }

        return new GetPickingListResponse
        {
            OrderId = order.Id,
            OrderNumber = order.OrderNumber,
            Items = pickingItems
        };
    }

    private static string BuildLocationCode(WarehouseLocation location)
    {
        var parts = new List<string>();
        
        if (!string.IsNullOrEmpty(location.Zone))
            parts.Add(location.Zone);
        if (!string.IsNullOrEmpty(location.Aisle))
            parts.Add(location.Aisle);
        if (!string.IsNullOrEmpty(location.Rack))
            parts.Add(location.Rack);
        if (!string.IsNullOrEmpty(location.Shelf))
            parts.Add(location.Shelf);
        if (!string.IsNullOrEmpty(location.Level))
            parts.Add(location.Level);

        return parts.Count > 0 ? string.Join("-", parts) : location.LocationCode;
    }
}



