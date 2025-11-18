using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Stok hareketleri kaydı (giriş/çıkış/transfer)
/// </summary>
public class StockMovement : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public Guid ProductId { get; set; }
    public Product? Product { get; set; }
    
    public Guid? ProductVariantId { get; set; }
    public ProductVariant? ProductVariant { get; set; }
    
    public Guid WarehouseId { get; set; }
    public Warehouse? Warehouse { get; set; }
    
    public Guid? WarehouseLocationId { get; set; }
    public WarehouseLocation? WarehouseLocation { get; set; }
    
    // Hareket tipi
    public string MovementType { get; set; } = string.Empty; 
    // IN: Giriş (Alım, İade, Transfer Gelen)
    // OUT: Çıkış (Satış, Transfer Giden, Fire, Hasar)
    // ADJUSTMENT: Düzeltme
    // TRANSFER: Transfer (hem kaynak hem hedef için kayıt tutulur)
    // RESERVED: Rezervasyon (Sipariş için stok rezerve edildi)
    
    public int Quantity { get; set; } // Hareket miktarı (pozitif/negatif)
    public int QuantityBefore { get; set; } // Hareket öncesi stok
    public int QuantityAfter { get; set; } // Hareket sonrası stok
    
    // Referans bilgileri
    public Guid? ReferenceId { get; set; } // OrderId, TransferId, vb.
    public string? ReferenceType { get; set; } // "Order", "Transfer", "Adjustment", vb.
    public string? ReferenceNumber { get; set; } // Sipariş numarası, transfer numarası, vb.
    
    // Açıklama
    public string? Reason { get; set; } // Hareket nedeni
    public string? Notes { get; set; } // Ek notlar
    
    // Kullanıcı bilgisi
    public Guid? UserId { get; set; } // İşlemi yapan kullanıcı
    public User? User { get; set; }
    
    // Maliyet bilgisi
    public decimal? UnitCost { get; set; } // Birim maliyet
    public decimal? TotalCost { get; set; } // Toplam maliyet
}

