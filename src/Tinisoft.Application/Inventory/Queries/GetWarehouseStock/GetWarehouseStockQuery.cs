using MediatR;

namespace Tinisoft.Application.Inventory.Queries.GetWarehouseStock;

/// <summary>
/// Warehouse bazlı stok listesi
/// </summary>
public class GetWarehouseStockQuery : IRequest<GetWarehouseStockResponse>
{
    public Guid? WarehouseId { get; set; }
    public Guid? ProductId { get; set; }
    public bool OnlyLowStock { get; set; } = false; // Sadece düşük stoklu ürünler
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 50;
}

public class GetWarehouseStockResponse
{
    public List<WarehouseStockDto> Items { get; set; } = new();
    public int TotalCount { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
}

public class WarehouseStockDto
{
    public Guid ProductInventoryId { get; set; }
    public Guid ProductId { get; set; }
    public string ProductTitle { get; set; } = string.Empty;
    public string? ProductSKU { get; set; }
    public Guid WarehouseId { get; set; }
    public string WarehouseName { get; set; } = string.Empty;
    public Guid? WarehouseLocationId { get; set; }
    public string? LocationCode { get; set; }
    public string? Zone { get; set; }
    public string? Aisle { get; set; }
    public string? Rack { get; set; }
    public string? Shelf { get; set; }
    public string? Level { get; set; }
    public int Quantity { get; set; }
    public int ReservedQuantity { get; set; }
    public int AvailableQuantity { get; set; }
    public int? MinStockLevel { get; set; }
    public int? MaxStockLevel { get; set; }
    public bool IsLowStock { get; set; }
    public string? InventoryMethod { get; set; }
    public string? LotNumber { get; set; }
    public DateTime? ExpiryDate { get; set; }
    public DateTime? ManufactureDate { get; set; }
    public decimal? Cost { get; set; }
}



