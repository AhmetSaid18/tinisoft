using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Invoices.Services;

/// <summary>
/// GİB SOAP servis entegrasyonu
/// </summary>
public interface IGIBService
{
    /// <summary>
    /// Faturayı GİB'e gönder
    /// </summary>
    Task<GIBSendInvoiceResponse> SendInvoiceAsync(
        string signedUBLXml,
        TenantInvoiceSettings settings,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Fatura durumunu sorgula
    /// </summary>
    Task<GIBInvoiceStatusResponse> GetInvoiceStatusAsync(
        string gibInvoiceId,
        TenantInvoiceSettings settings,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Gelen faturaları al (inbox)
    /// </summary>
    Task<List<GIBInboxInvoiceResponse>> GetInboxInvoicesAsync(
        TenantInvoiceSettings settings,
        CancellationToken cancellationToken = default);
}

public class GIBSendInvoiceResponse
{
    public bool Success { get; set; }
    public string? InvoiceId { get; set; } // GİB'den dönen UUID
    public string? InvoiceNumber { get; set; } // GİB'den dönen fatura numarası
    public string? ErrorMessage { get; set; }
    public string? ErrorCode { get; set; }
}

public class GIBInvoiceStatusResponse
{
    public bool Success { get; set; }
    public string Status { get; set; } = string.Empty; // "Onaylandı", "Reddedildi", "İşleniyor"
    public string? StatusMessage { get; set; }
    public DateTime? ProcessedAt { get; set; }
}

public class GIBInboxInvoiceResponse
{
    public string InvoiceId { get; set; } = string.Empty;
    public string InvoiceNumber { get; set; } = string.Empty;
    public DateTime InvoiceDate { get; set; }
    public string SenderVKN { get; set; } = string.Empty;
    public string SenderName { get; set; } = string.Empty;
    public decimal Total { get; set; }
    public string Status { get; set; } = string.Empty;
}



