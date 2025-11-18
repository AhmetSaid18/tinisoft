using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Fatura (e-Fatura veya E-Arşiv)
/// </summary>
public class Invoice : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    // Invoice Info
    public string InvoiceNumber { get; set; } = string.Empty; // Fatura numarası (örn: FT2024001)
    public string InvoiceSerial { get; set; } = string.Empty; // Seri (A, B, vb.)
    public DateTime InvoiceDate { get; set; } = DateTime.UtcNow;
    public DateTime? DeliveryDate { get; set; } // Teslimat tarihi (e-fatura için)
    
    // Invoice Type
    public string InvoiceType { get; set; } = "eFatura"; // eFatura, EArsiv
    public string ProfileId { get; set; } = "TICARIFATURA"; // TICARIFATURA, EARSIVFATURA, TEMELFATURA
    
    // Status
    public string Status { get; set; } = "Draft"; // Draft, Sent, Approved, Rejected, Cancelled
    public string? StatusMessage { get; set; } // GİB'den gelen durum mesajı
    
    // Order Reference
    public Guid OrderId { get; set; }
    public Order? Order { get; set; }
    
    // Customer Info (fatura alan müşteri)
    public string CustomerName { get; set; } = string.Empty;
    public string? CustomerVKN { get; set; } // Vergi Kimlik No (TCKN veya VKN)
    public string? CustomerTCKN { get; set; } // TC Kimlik No (şahıs ise)
    public string? CustomerTaxOffice { get; set; } // Vergi Dairesi
    public string? CustomerTaxNumber { get; set; } // Vergi No
    public string? CustomerEmail { get; set; }
    public string? CustomerPhone { get; set; }
    
    // Customer Address
    public string? CustomerAddressLine1 { get; set; }
    public string? CustomerAddressLine2 { get; set; }
    public string? CustomerCity { get; set; }
    public string? CustomerState { get; set; }
    public string? CustomerPostalCode { get; set; }
    public string? CustomerCountry { get; set; } = "TR";
    
    // Totals
    public decimal Subtotal { get; set; } // Vergi öncesi toplam
    public decimal TaxAmount { get; set; } // Vergi tutarı (KDV)
    public decimal DiscountAmount { get; set; } // İndirim tutarı
    public decimal ShippingAmount { get; set; } // Kargo tutarı
    public decimal Total { get; set; } // Toplam tutar (vergi dahil)
    
    // Tax Details (JSON)
    public string TaxDetailsJson { get; set; } = "[]"; // [{taxRate: 20, taxAmount: 100, taxableAmount: 500}]
    
    // Currency
    public string Currency { get; set; } = "TRY";
    
    // Payment Info
    public string? PaymentMethod { get; set; } // "KrediKartı", "Havale", "KapıdaÖdeme"
    public DateTime? PaymentDueDate { get; set; } // Ödeme vadesi
    
    // GİB Integration
    public string? GIBInvoiceId { get; set; } // GİB'den dönen Invoice ID (UUID)
    public string? GIBInvoiceNumber { get; set; } // GİB'den dönen fatura numarası
    public DateTime? GIBSentAt { get; set; } // GİB'e gönderilme tarihi
    public DateTime? GIBApprovedAt { get; set; } // GİB onay tarihi
    public string? GIBApprovalStatus { get; set; } // "Onaylandı", "Reddedildi", vb.
    
    // XML & PDF
    public string? UBLXML { get; set; } // Orijinal UBL-TR XML (gönderilen)
    public string? UBLXMLSigned { get; set; } // İmzalanmış UBL-TR XML
    public string? PDFUrl { get; set; } // Oluşturulan PDF URL
    public DateTime? PDFGeneratedAt { get; set; }
    
    // Notes
    public string? Notes { get; set; } // Notlar
    public string? InternalNotes { get; set; } // İç notlar (sadece admin)
    
    // Cancellation
    public bool IsCancelled { get; set; } = false;
    public DateTime? CancelledAt { get; set; }
    public string? CancellationReason { get; set; }
    public string? CancellationInvoiceNumber { get; set; } // İptal faturası numarası
    
    // Navigation
    public ICollection<InvoiceItem> Items { get; set; } = new List<InvoiceItem>();
}

