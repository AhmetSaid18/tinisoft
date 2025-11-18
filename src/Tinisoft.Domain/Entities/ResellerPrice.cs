using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Bayi bazlı özel fiyatlar
/// </summary>
public class ResellerPrice : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public Guid ResellerId { get; set; }
    public Reseller? Reseller { get; set; }
    
    public Guid ProductId { get; set; }
    public Product? Product { get; set; }
    
    // Pricing
    public decimal Price { get; set; } // Bayi fiyatı
    public decimal? CompareAtPrice { get; set; } // Karşılaştırma fiyatı
    public string Currency { get; set; } = "TRY";
    
    // Quantity Break Pricing (Miktar bazlı fiyatlandırma)
    public int? MinQuantity { get; set; } // Minimum miktar (bu fiyat için)
    public int? MaxQuantity { get; set; } // Maksimum miktar (bu fiyat için)
    
    // Status
    public bool IsActive { get; set; } = true;
    public DateTime? ValidFrom { get; set; } // Geçerlilik başlangıç tarihi
    public DateTime? ValidUntil { get; set; } // Geçerlilik bitiş tarihi
    
    // Notes
    public string? Notes { get; set; }
}

