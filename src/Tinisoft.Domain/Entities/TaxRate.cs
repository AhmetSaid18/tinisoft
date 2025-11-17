using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class TaxRate : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public string Name { get; set; } = string.Empty; // "KDV %20", "ÖTV %25", etc.
    public string Code { get; set; } = string.Empty; // "KDV20", "OTV25", etc.
    public decimal Rate { get; set; } // 20.00 = %20
    public string Type { get; set; } = "VAT"; // VAT, SalesTax, ExciseTax, etc.
    public bool IsActive { get; set; } = true;
    public string? Description { get; set; }
    
    // Türkiye için özel alanlar - E-Fatura entegrasyonu
    public string? TaxCode { get; set; } // KDV kodu (001, 002, etc.) - E-Fatura için
    public string? ExciseTaxCode { get; set; } // ÖTV kodu (varsa)
    public string? ProductServiceCode { get; set; } // Mal/Hizmet kodu (GTIP, vb.)
    public bool IsIncludedInPrice { get; set; } = false; // Fiyata dahil mi? (TR'de genelde dahil değil)
    
    // E-Fatura için ek bilgiler
    public string? EInvoiceTaxType { get; set; } // "001" = KDV, "002" = ÖTV, etc.
    public bool IsExempt { get; set; } = false; // Vergiden muaf mı?
    public string? ExemptionReason { get; set; } // Muafiyet nedeni
}

