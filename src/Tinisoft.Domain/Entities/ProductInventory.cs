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
    
    // Detaylı lokasyon (yeni)
    public Guid? WarehouseLocationId { get; set; }
    public WarehouseLocation? WarehouseLocation { get; set; }
    
    // Eski Location field'ı (backward compatibility için tutuyoruz)
    public string? Location { get; set; } // Deprecated: WarehouseLocation kullanılmalı
    
    public int Quantity { get; set; } = 0; // Mevcut stok
    public int ReservedQuantity { get; set; } = 0; // Rezerve edilmiş (siparişte ama henüz gönderilmemiş)
    public int AvailableQuantity => Quantity - ReservedQuantity; // Kullanılabilir stok
    
    public int? MinStockLevel { get; set; } // Minimum stok seviyesi (uyarı için)
    public int? MaxStockLevel { get; set; } // Maksimum stok seviyesi
    
    public decimal? Cost { get; set; } // Bu depodaki ürünün maliyeti
    
    // FIFO/LIFO için
    public string? InventoryMethod { get; set; } = "FIFO"; // FIFO, LIFO, FEFO (First Expiry First Out)
    
    // Lot/Batch takibi
    public string? LotNumber { get; set; } // Lot numarası
    public DateTime? ExpiryDate { get; set; } // Son kullanma tarihi (varsa)
    public DateTime? ManufactureDate { get; set; } // Üretim tarihi (varsa)
    
    public bool IsActive { get; set; } = true;
}

