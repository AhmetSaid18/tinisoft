using MediatR;

namespace Tinisoft.Application.Inventory.Queries.GetPickingList;

public class GetPickingListQuery : IRequest<GetPickingListResponse>
{
    public Guid OrderId { get; set; }
}

public class GetPickingListResponse
{
    public Guid OrderId { get; set; }
    public string OrderNumber { get; set; } = string.Empty;
    public List<PickingItem> Items { get; set; } = new();
}

public class PickingItem
{
    public Guid OrderItemId { get; set; }
    public Guid ProductId { get; set; }
    public string ProductTitle { get; set; } = string.Empty;
    public string? SKU { get; set; }
    public int Quantity { get; set; }
    
    // Lokasyon bilgileri
    public Guid WarehouseId { get; set; }
    public string WarehouseName { get; set; } = string.Empty;
    public Guid? WarehouseLocationId { get; set; }
    public string? LocationCode { get; set; } // A-1-2-3-4 formatında
    public string? Zone { get; set; }
    public string? Aisle { get; set; }
    public string? Rack { get; set; }
    public string? Shelf { get; set; }
    public string? Level { get; set; }
    
    // Stok bilgisi
    public int AvailableQuantity { get; set; }
    
    // Picking durumu
    public bool IsPicked { get; set; }
    public DateTime? PickedAt { get; set; }
    public string? PickedByUserName { get; set; }
}

