using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Fatura kalemi (ürün/hizmet)
/// </summary>
public class InvoiceItem : BaseEntity
{
    public Guid InvoiceId { get; set; }
    public Invoice? Invoice { get; set; }
    
    // Product Reference
    public Guid ProductId { get; set; }
    public Product? Product { get; set; }
    public Guid? ProductVariantId { get; set; }
    public ProductVariant? ProductVariant { get; set; }
    
    // Item Info
    public string ItemName { get; set; } = string.Empty; // Ürün adı
    public string? ItemDescription { get; set; } // Açıklama
    public string? ItemCode { get; set; } // Ürün kodu (SKU, GTIN, vb.)
    public string? ProductServiceCode { get; set; } // Mal/Hizmet kodu (GTIP - e-Fatura için)
    
    // Quantity & Price
    public int Quantity { get; set; } = 1;
    public string Unit { get; set; } = "C62"; // C62 = Adet (e-Fatura birim kodu)
    public decimal UnitPrice { get; set; } // Birim fiyat (vergi hariç)
    public decimal LineTotal { get; set; } // Satır toplamı (vergi hariç)
    
    // Tax
    public Guid? TaxRateId { get; set; }
    public TaxRate? TaxRate { get; set; }
    public decimal TaxRatePercent { get; set; } // %20 = 20.00
    public decimal TaxAmount { get; set; } // Vergi tutarı (KDV)
    public decimal LineTotalWithTax { get; set; } // Satır toplamı (vergi dahil)
    
    // Discount
    public decimal DiscountAmount { get; set; } = 0; // İndirim tutarı
    public decimal DiscountPercent { get; set; } = 0; // İndirim yüzdesi
    
    // Position
    public int Position { get; set; } // Sıra numarası
}

