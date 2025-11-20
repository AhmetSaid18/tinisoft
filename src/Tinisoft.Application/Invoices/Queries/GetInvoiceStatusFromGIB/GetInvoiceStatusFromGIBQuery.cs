using MediatR;

namespace Tinisoft.Application.Invoices.Queries.GetInvoiceStatusFromGIB;

public class GetInvoiceStatusFromGIBQuery : IRequest<GetInvoiceStatusFromGIBResponse>
{
    public Guid InvoiceId { get; set; }
}

public class GetInvoiceStatusFromGIBResponse
{
    public Guid InvoiceId { get; set; }
    public string InvoiceNumber { get; set; } = string.Empty;
    public bool Success { get; set; }
    public string Status { get; set; } = string.Empty; // "Onaylandı", "Reddedildi", "İşleniyor", "Gönderildi"
    public string? StatusMessage { get; set; }
    public DateTime? ProcessedAt { get; set; }
    public string? GIBInvoiceId { get; set; }
}



