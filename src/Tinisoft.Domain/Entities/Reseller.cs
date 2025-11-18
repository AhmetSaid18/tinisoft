using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Bayi/Reseller entity - B2B satış için
/// </summary>
public class Reseller : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    // Basic Info
    public string CompanyName { get; set; } = string.Empty; // Şirket adı
    public string? TaxNumber { get; set; } // Vergi numarası
    public string? TaxOffice { get; set; } // Vergi dairesi
    
    // Contact Info
    public string Email { get; set; } = string.Empty;
    public string? Phone { get; set; }
    public string? Mobile { get; set; }
    
    // Address
    public string? Address { get; set; }
    public string? City { get; set; }
    public string? State { get; set; }
    public string? PostalCode { get; set; }
    public string? Country { get; set; }
    
    // Contact Person
    public string? ContactPersonName { get; set; }
    public string? ContactPersonTitle { get; set; }
    
    // Status
    public bool IsActive { get; set; } = true;
    public DateTime? ApprovedAt { get; set; } // Onay tarihi
    public Guid? ApprovedByUserId { get; set; } // Onaylayan kullanıcı
    
    // Credit & Payment
    public decimal CreditLimit { get; set; } = 0; // Kredi limiti
    public decimal UsedCredit { get; set; } = 0; // Kullanılan kredi
    public int PaymentTermDays { get; set; } = 30; // Ödeme vadesi (gün)
    public string PaymentMethod { get; set; } = "Invoice"; // Invoice, Cash, BankTransfer
    
    // Pricing
    public decimal DefaultDiscountPercent { get; set; } = 0; // Varsayılan indirim yüzdesi
    public bool UseCustomPricing { get; set; } = false; // Özel fiyatlandırma kullanılsın mı?
    
    // Notes
    public string? Notes { get; set; } // Notlar
    
    // Navigation
    public ICollection<ResellerPrice> ResellerPrices { get; set; } = new List<ResellerPrice>();
    public ICollection<Order> Orders { get; set; } = new List<Order>();
}

