using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Tenant (şirket) e-fatura ayarları
/// </summary>
public class TenantInvoiceSettings : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    // E-Fatura User Info
    public bool IsEFaturaUser { get; set; } = false; // e-Fatura kullanıcısı mı?
    public string? VKN { get; set; } // Vergi Kimlik No (şirket VKN'si)
    public string? TCKN { get; set; } // TC Kimlik No (şahıs şirketi ise)
    public string? TaxOffice { get; set; } // Vergi Dairesi
    public string? TaxNumber { get; set; } // Vergi No
    public string? EFaturaAlias { get; set; } // GİB'den aldığı alias (e-fatura kullanıcı adı)
    public string? EFaturaPassword { get; set; } // GİB şifresi (encrypted)
    
    // Company Info (fatura kesen şirket bilgileri)
    public string? CompanyName { get; set; } // Şirket adı
    public string? CompanyTitle { get; set; } // Ünvan
    public string? CompanyAddressLine1 { get; set; }
    public string? CompanyAddressLine2 { get; set; }
    public string? CompanyCity { get; set; }
    public string? CompanyState { get; set; }
    public string? CompanyPostalCode { get; set; }
    public string? CompanyCountry { get; set; } = "TR";
    public string? CompanyPhone { get; set; }
    public string? CompanyEmail { get; set; }
    public string? CompanyWebsite { get; set; }
    
    // Bank Account Info (IBAN)
    public string? BankName { get; set; }
    public string? BankBranch { get; set; }
    public string? IBAN { get; set; }
    public string? AccountName { get; set; }
    
    // Mali Mühür/E-İmza
    public string? MaliMuhurCertificateBase64 { get; set; } // PKCS#12 sertifika (encrypted base64)
    public string? MaliMuhurPassword { get; set; } // Sertifika şifresi (encrypted)
    public string? MaliMuhurSerialNumber { get; set; } // Sertifika seri numarası
    public DateTime? MaliMuhurExpiryDate { get; set; } // Sertifika son geçerlilik tarihi
    
    // Invoice Numbering
    public string InvoicePrefix { get; set; } = "FT"; // Fatura öneki (FT, FAT, vb.)
    public string InvoiceSerial { get; set; } = "A"; // Seri (A, B, C, vb.)
    public int InvoiceStartNumber { get; set; } = 1; // Başlangıç numarası
    public int LastInvoiceNumber { get; set; } = 0; // Son kullanılan numara
    
    // Invoice Settings
    public string DefaultInvoiceType { get; set; } = "eFatura"; // eFatura, EArsiv
    public string DefaultProfileId { get; set; } = "TICARIFATURA"; // TICARIFATURA, EARSIVFATURA
    public int PaymentDueDays { get; set; } = 30; // Ödeme vadesi (gün)
    
    // Auto Invoice
    public bool AutoCreateInvoiceOnOrderPaid { get; set; } = true; // Sipariş ödenince otomatik fatura kes
    public bool AutoSendToGIB { get; set; } = true; // Otomatik GİB'e gönder
    
    // GİB Integration Settings
    public bool UseTestEnvironment { get; set; } = false; // Test ortamı kullan
    public string? GIBTestVKN { get; set; } // Test ortamı VKN
    public string? GIBTestAlias { get; set; } // Test ortamı alias
    
    // Status
    public bool IsActive { get; set; } = true;
    public DateTime? LastInvoiceSyncAt { get; set; } // Son fatura senkronizasyonu
}

