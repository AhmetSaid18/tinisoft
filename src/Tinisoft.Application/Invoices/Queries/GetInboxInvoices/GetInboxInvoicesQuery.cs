using MediatR;

namespace Tinisoft.Application.Invoices.Queries.GetInboxInvoices;

public class GetInboxInvoicesQuery : IRequest<GetInboxInvoicesResponse>
{
    public DateTime? StartDate { get; set; }
    public DateTime? EndDate { get; set; }
    public string? SenderVKN { get; set; }
}

public class GetInboxInvoicesResponse
{
    public List<InboxInvoiceDto> Invoices { get; set; } = new();
    public int TotalCount { get; set; }
}

public class InboxInvoiceDto
{
    public string InvoiceId { get; set; } = string.Empty;
    public string InvoiceNumber { get; set; } = string.Empty;
    public DateTime InvoiceDate { get; set; }
    public string SenderVKN { get; set; } = string.Empty;
    public string SenderName { get; set; } = string.Empty;
    public decimal Total { get; set; }
    public string Status { get; set; } = string.Empty;
}

