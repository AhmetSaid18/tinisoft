using MediatR;

namespace Tinisoft.Application.Invoices.Commands.UpdateInvoiceSettings;

public class UpdateInvoiceSettingsCommand : IRequest<UpdateInvoiceSettingsResponse>
{
    // E-Fatura User Info
    public bool? IsEFaturaUser { get; set; }
    public string? VKN { get; set; }
    public string? TCKN { get; set; }
    public string? TaxOffice { get; set; }
    public string? TaxNumber { get; set; }
    public string? EFaturaAlias { get; set; }
    public string? EFaturaPassword { get; set; }
    
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
    
    // Mali Mühür (Base64 encoded PKCS#12 certificate)
    public string? MaliMuhurCertificateBase64 { get; set; }
    public string? MaliMuhurPassword { get; set; }
    
    // Invoice Numbering
    public string? InvoicePrefix { get; set; }
    public string? InvoiceSerial { get; set; }
    public int? InvoiceStartNumber { get; set; }
    
    // Invoice Settings
    public string? DefaultInvoiceType { get; set; }
    public string? DefaultProfileId { get; set; }
    public int? PaymentDueDays { get; set; }
    
    // Auto Invoice
    public bool? AutoCreateInvoiceOnOrderPaid { get; set; }
    public bool? AutoSendToGIB { get; set; }
    
    // GİB Integration Settings
    public bool? UseTestEnvironment { get; set; }
}

public class UpdateInvoiceSettingsResponse
{
    public Guid TenantId { get; set; }
    public bool IsEFaturaUser { get; set; }
    public string? VKN { get; set; }
    public string Message { get; set; } = string.Empty;
}



