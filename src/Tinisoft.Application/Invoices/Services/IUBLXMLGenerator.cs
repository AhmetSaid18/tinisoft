using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Invoices.Services;

/// <summary>
/// UBL-TR XML oluşturma ve imzalama servisi
/// </summary>
public interface IUBLXMLGenerator
{
    /// <summary>
    /// Invoice'dan UBL-TR XML oluştur
    /// </summary>
    Task<string> GenerateInvoiceXMLAsync(
        Invoice invoice,
        TenantInvoiceSettings settings,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// UBL XML'i mali mühür ile imzala
    /// </summary>
    Task<string> SignUBLXMLAsync(
        string ublXml,
        TenantInvoiceSettings settings,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// UBL XML validasyonu
    /// </summary>
    Task<bool> ValidateUBLXMLAsync(
        string ublXml,
        CancellationToken cancellationToken = default);
}



