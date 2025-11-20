using MediatR;

namespace Tinisoft.Application.Inventory.Queries.GetLowStockAlerts;

/// <summary>
/// Düşük stok uyarıları (MinStockLevel'a düşen ürünler)
/// </summary>
public class GetLowStockAlertsQuery : IRequest<GetLowStockAlertsResponse>
{
    public Guid? WarehouseId { get; set; }
    public bool OnlyCritical { get; set; } = false; // Sadece stokta olmayanları göster
}

public class GetLowStockAlertsResponse
{
    public List<LowStockAlertDto> Alerts { get; set; } = new();
    public int TotalCount { get; set; }
}

public class LowStockAlertDto
{
    public Guid ProductId { get; set; }
    public string ProductTitle { get; set; } = string.Empty;
    public string? ProductSKU { get; set; }
    public Guid WarehouseId { get; set; }
    public string WarehouseName { get; set; } = string.Empty;
    public Guid? WarehouseLocationId { get; set; }
    public string? LocationCode { get; set; }
    public int CurrentQuantity { get; set; }
    public int AvailableQuantity { get; set; }
    public int ReservedQuantity { get; set; }
    public int? MinStockLevel { get; set; }
    public int? MaxStockLevel { get; set; }
    public bool IsCritical { get; set; } // Stokta yok (AvailableQuantity = 0)
    public int? DaysUntilOutOfStock { get; set; } // Tahmini tükenme süresi (opsiyonel)
}



