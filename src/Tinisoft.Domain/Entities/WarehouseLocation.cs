using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Depo içi detaylı lokasyon yapısı
/// Örnek: Bölüm A, Koridor 1, Raf 2, Sıra 3, Katman 4
/// </summary>
public class WarehouseLocation : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public Guid WarehouseId { get; set; }
    public Warehouse? Warehouse { get; set; }
    
    // Lokasyon hiyerarşisi
    public string? Zone { get; set; } // Bölüm (A, B, C, vb.)
    public string? Aisle { get; set; } // Koridor (1, 2, 3, vb.)
    public string? Rack { get; set; } // Raf (1, 2, 3, vb.)
    public string? Shelf { get; set; } // Sıra (1, 2, 3, vb.)
    public string? Level { get; set; } // Katman (1, 2, 3, vb.)
    
    // Lokasyon kodu (otomatik oluşturulabilir: A-1-2-3-4)
    public string LocationCode { get; set; } = string.Empty;
    
    // Lokasyon bilgileri
    public string? Name { get; set; } // Opsiyonel isim (örn: "Hızlı Erişim Rafı")
    public string? Description { get; set; }
    public decimal? Width { get; set; } // Genişlik (cm)
    public decimal? Height { get; set; } // Yükseklik (cm)
    public decimal? Depth { get; set; } // Derinlik (cm)
    public decimal? MaxWeight { get; set; } // Maksimum ağırlık (kg)
    
    // Durum
    public bool IsActive { get; set; } = true;
    public bool IsReserved { get; set; } = false; // Rezerve edilmiş mi?
    public string? ReservedFor { get; set; } // Rezerve nedeni
    
    // Navigation
    public ICollection<ProductInventory> ProductInventories { get; set; } = new List<ProductInventory>();
}

