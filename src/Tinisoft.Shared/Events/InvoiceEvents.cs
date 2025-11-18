namespace Tinisoft.Shared.Events;

public class InvoiceCreatedEvent : BaseEvent
{
    public Guid InvoiceId { get; set; }
    public Guid OrderId { get; set; }
    public Guid TenantId { get; set; }
    public string InvoiceNumber { get; set; } = string.Empty;
}

public class InvoiceSentToGIBEvent : BaseEvent
{
    public Guid InvoiceId { get; set; }
    public Guid TenantId { get; set; }
    public string InvoiceNumber { get; set; } = string.Empty;
    public string GIBInvoiceId { get; set; } = string.Empty;
}

public class InvoiceApprovedByGIBEvent : BaseEvent
{
    public Guid InvoiceId { get; set; }
    public Guid TenantId { get; set; }
    public string InvoiceNumber { get; set; } = string.Empty;
    public string GIBInvoiceId { get; set; } = string.Empty;
}

public class InvoiceCancelledEvent : BaseEvent
{
    public Guid InvoiceId { get; set; }
    public Guid TenantId { get; set; }
    public string InvoiceNumber { get; set; } = string.Empty;
    public string CancellationReason { get; set; } = string.Empty;
}

