namespace Tinisoft.Application.Invoices.Services;

public interface IInvoiceNumberGenerator
{
    Task<InvoiceNumberResult> GenerateNextInvoiceNumberAsync(
        Guid tenantId,
        string prefix,
        string serial,
        CancellationToken cancellationToken = default);
}

public class InvoiceNumberResult
{
    public string Number { get; set; } = string.Empty; // Örn: "0001", "0002"
    public string Serial { get; set; } = string.Empty; // Örn: "A", "B"
    public string FullNumber { get; set; } = string.Empty; // Örn: "FT2024001A" veya sadece "FT0001"
}



