using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class TaxRule : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public string Name { get; set; } = string.Empty;
    public Guid? ProductId { get; set; } // Belirli ürün için
    public Product? Product { get; set; }
    public Guid? CategoryId { get; set; } // Belirli kategori için
    public Category? Category { get; set; }
    public Guid? ProductTypeId { get; set; } // Belirli ürün tipi için
    
    public Guid TaxRateId { get; set; }
    public TaxRate? TaxRate { get; set; }
    
    public int Priority { get; set; } // Öncelik (daha yüksek öncelik önce uygulanır)
    public bool IsActive { get; set; } = true;
    
    // Koşullar
    public decimal? MinPrice { get; set; } // Minimum fiyat
    public decimal? MaxPrice { get; set; } // Maksimum fiyat
    public string? CountryCode { get; set; } // Ülke kodu (TR, US, etc.)
    public string? Region { get; set; } // Bölge (İstanbul, Ankara, etc.)
}

