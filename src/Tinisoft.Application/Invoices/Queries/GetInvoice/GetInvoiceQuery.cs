using MediatR;

namespace Tinisoft.Application.Invoices.Queries.GetInvoice;

public class GetInvoiceQuery : IRequest<GetInvoiceResponse>
{
    public Guid InvoiceId { get; set; }
    public bool IncludePDF { get; set; } = false; // PDF URL'i de dahil et
}

public class GetInvoiceResponse
{
    public Guid InvoiceId { get; set; }
    public string InvoiceNumber { get; set; } = string.Empty;
    public string InvoiceSerial { get; set; } = string.Empty;
    public DateTime InvoiceDate { get; set; }
    public string InvoiceType { get; set; } = string.Empty;
    public string ProfileId { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string? StatusMessage { get; set; }
    
    public Guid OrderId { get; set; }
    public string OrderNumber { get; set; } = string.Empty;
    
    public string CustomerName { get; set; } = string.Empty;
    public string? CustomerEmail { get; set; }
    public string? CustomerVKN { get; set; }
    
    public decimal Subtotal { get; set; }
    public decimal TaxAmount { get; set; }
    public decimal DiscountAmount { get; set; }
    public decimal ShippingAmount { get; set; }
    public decimal Total { get; set; }
    public string Currency { get; set; } = "TRY";
    
    public string? GIBInvoiceId { get; set; }
    public string? GIBInvoiceNumber { get; set; }
    public DateTime? GIBSentAt { get; set; }
    public DateTime? GIBApprovedAt { get; set; }
    public string? GIBApprovalStatus { get; set; }
    
    public string? PDFUrl { get; set; }
    public DateTime? PDFGeneratedAt { get; set; }
    
    public List<InvoiceItemResponse> Items { get; set; } = new();
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

public class InvoiceItemResponse
{
    public Guid InvoiceItemId { get; set; }
    public Guid ProductId { get; set; }
    public Guid? ProductVariantId { get; set; }
    public string ItemName { get; set; } = string.Empty;
    public string? ItemCode { get; set; }
    public int Quantity { get; set; }
    public string Unit { get; set; } = string.Empty;
    public decimal UnitPrice { get; set; }
    public decimal LineTotal { get; set; }
    public decimal TaxRatePercent { get; set; }
    public decimal TaxAmount { get; set; }
    public decimal LineTotalWithTax { get; set; }
    public int Position { get; set; }
}



