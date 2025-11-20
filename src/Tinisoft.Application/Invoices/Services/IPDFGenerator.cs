using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Invoices.Services;

/// <summary>
/// Fatura PDF oluşturma servisi
/// </summary>
public interface IPDFGenerator
{
    /// <summary>
    /// Invoice'dan PDF oluştur
    /// </summary>
    Task<string> GenerateInvoicePDFAsync(
        Invoice invoice,
        TenantInvoiceSettings settings,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// PDF template'ı al
    /// </summary>
    Task<string> GetTemplateAsync(
        Guid tenantId,
        string templateName = "default",
        CancellationToken cancellationToken = default);
}



