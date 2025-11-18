using MediatR;

namespace Tinisoft.Application.Invoices.Commands.SendInvoiceToGIB;

public class SendInvoiceToGIBCommand : IRequest<SendInvoiceToGIBResponse>
{
    public Guid InvoiceId { get; set; }
}

public class SendInvoiceToGIBResponse
{
    public Guid InvoiceId { get; set; }
    public string InvoiceNumber { get; set; } = string.Empty;
    public bool Success { get; set; }
    public string? GIBInvoiceId { get; set; }
    public string? GIBInvoiceNumber { get; set; }
    public string? ErrorMessage { get; set; }
    public string Message { get; set; } = string.Empty;
}

