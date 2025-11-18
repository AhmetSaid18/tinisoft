using MediatR;

namespace Tinisoft.Application.Invoices.Queries.GetInvoiceSettings;

public class GetInvoiceSettingsQuery : IRequest<GetInvoiceSettingsResponse>
{
}

public class GetInvoiceSettingsResponse
{
    public Guid TenantId { get; set; }
    
    // E-Fatura User Info
    public bool IsEFaturaUser { get; set; }
    public string? VKN { get; set; }
    public string? TCKN { get; set; }
    public string? TaxOffice { get; set; }
    public string? TaxNumber { get; set; }
    public string? EFaturaAlias { get; set; }
    // Password döndürülmez (güvenlik)
    
    // Company Info
    public string? CompanyName { get; set; }
    public string? CompanyTitle { get; set; }
    public string? CompanyAddressLine1 { get; set; }
    public string? CompanyAddressLine2 { get; set; }
    public string? CompanyCity { get; set; }
    public string? CompanyState { get; set; }
    public string? CompanyPostalCode { get; set; }
    public string? CompanyCountry { get; set; }
    public string? CompanyPhone { get; set; }
    public string? CompanyEmail { get; set; }
    public string? CompanyWebsite { get; set; }
    
    // Bank Account Info
    public string? BankName { get; set; }
    public string? BankBranch { get; set; }
    public string? IBAN { get; set; }
    public string? AccountName { get; set; }
    
    // Mali Mühür Info (sertifika döndürülmez, sadece bilgiler)
    public string? MaliMuhurSerialNumber { get; set; }
    public DateTime? MaliMuhurExpiryDate { get; set; }
    public bool HasMaliMuhur { get; set; }
    
    // Invoice Numbering
    public string InvoicePrefix { get; set; } = "FT";
    public string InvoiceSerial { get; set; } = "A";
    public int InvoiceStartNumber { get; set; } = 1;
    public int LastInvoiceNumber { get; set; } = 0;
    
    // Invoice Settings
    public string DefaultInvoiceType { get; set; } = "eFatura";
    public string DefaultProfileId { get; set; } = "TICARIFATURA";
    public int PaymentDueDays { get; set; } = 30;
    
    // Auto Invoice
    public bool AutoCreateInvoiceOnOrderPaid { get; set; } = true;
    public bool AutoSendToGIB { get; set; } = true;
    
    // GİB Integration Settings
    public bool UseTestEnvironment { get; set; } = false;
    
    public bool IsActive { get; set; }
}

