using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class ProductInventory : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public Guid ProductId { get; set; }
    public Product? Product { get; set; }
    
    public Guid WarehouseId { get; set; }
    public Warehouse? Warehouse { get; set; }
    
    public int Quantity { get; set; } = 0; // Mevcut stok
    public int ReservedQuantity { get; set; } = 0; // Rezerve edilmiş (siparişte ama henüz gönderilmemiş)
    public int AvailableQuantity => Quantity - ReservedQuantity; // Kullanılabilir stok
    
    public int? MinStockLevel { get; set; } // Minimum stok seviyesi (uyarı için)
    public int? MaxStockLevel { get; set; } // Maksimum stok seviyesi
    
    public decimal? Cost { get; set; } // Bu depodaki ürünün maliyeti
    public string? Location { get; set; } // Depo içi konum (A-1-2, Raf 5, etc.)
    
    public bool IsActive { get; set; } = true;
}

