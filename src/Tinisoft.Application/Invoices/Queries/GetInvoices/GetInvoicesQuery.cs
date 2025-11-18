using MediatR;

namespace Tinisoft.Application.Invoices.Queries.GetInvoices;

public class GetInvoicesQuery : IRequest<GetInvoicesResponse>
{
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 20;
    
    // Filters
    public string? Status { get; set; } // Draft, Sent, Approved, Rejected, Cancelled
    public string? InvoiceType { get; set; } // eFatura, EArsiv
    public Guid? OrderId { get; set; }
    public DateTime? StartDate { get; set; }
    public DateTime? EndDate { get; set; }
    public string? CustomerName { get; set; }
    public string? InvoiceNumber { get; set; }
    
    // Sorting
    public string? SortBy { get; set; } // InvoiceDate, InvoiceNumber, Total, Status
    public string? SortOrder { get; set; } // ASC, DESC (default: DESC)
}

public class GetInvoicesResponse
{
    public List<InvoiceListItemDto> Invoices { get; set; } = new();
    public int TotalCount { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => (int)Math.Ceiling((double)TotalCount / PageSize);
}

public class InvoiceListItemDto
{
    public Guid InvoiceId { get; set; }
    public string InvoiceNumber { get; set; } = string.Empty;
    public string InvoiceSerial { get; set; } = string.Empty;
    public DateTime InvoiceDate { get; set; }
    public string InvoiceType { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string? StatusMessage { get; set; }
    
    public Guid OrderId { get; set; }
    public string? OrderNumber { get; set; }
    
    public string CustomerName { get; set; } = string.Empty;
    public string? CustomerEmail { get; set; }
    
    public decimal Total { get; set; }
    public string Currency { get; set; } = "TRY";
    
    public string? GIBInvoiceId { get; set; }
    public string? GIBInvoiceNumber { get; set; }
    public DateTime? GIBSentAt { get; set; }
    public string? GIBApprovalStatus { get; set; }
    
    public bool IsCancelled { get; set; }
    public DateTime? CancelledAt { get; set; }
    
    public DateTime CreatedAt { get; set; }
}

