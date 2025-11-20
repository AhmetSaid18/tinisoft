using MediatR;

namespace Tinisoft.Application.Invoices.Commands.CreateInvoice;

public class CreateInvoiceCommand : IRequest<CreateInvoiceResponse>
{
    public Guid OrderId { get; set; }
    public string? InvoiceType { get; set; } // eFatura, EArsiv (default: TenantInvoiceSettings'den)
    public string? ProfileId { get; set; } // TICARIFATURA, EARSIVFATURA (default: TenantInvoiceSettings'den)
    public DateTime? InvoiceDate { get; set; } // null ise bugün
    public bool AutoSendToGIB { get; set; } = true; // Otomatik GİB'e gönder
}

public class CreateInvoiceResponse
{
    public Guid InvoiceId { get; set; }
    public string InvoiceNumber { get; set; } = string.Empty;
    public string InvoiceSerial { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string? GIBInvoiceId { get; set; }
    public string? PDFUrl { get; set; }
    public string Message { get; set; } = string.Empty;
}



