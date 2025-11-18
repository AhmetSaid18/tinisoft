using MediatR;

namespace Tinisoft.Application.Invoices.Commands.CancelInvoice;

public class CancelInvoiceCommand : IRequest<CancelInvoiceResponse>
{
    public Guid InvoiceId { get; set; }
    public string CancellationReason { get; set; } = string.Empty; // İptal nedeni (zorunlu)
    public bool CreateCancellationInvoice { get; set; } = true; // İptal faturası oluştur
}

public class CancelInvoiceResponse
{
    public Guid InvoiceId { get; set; }
    public string InvoiceNumber { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string? CancellationInvoiceNumber { get; set; }
    public string Message { get; set; } = string.Empty;
}

