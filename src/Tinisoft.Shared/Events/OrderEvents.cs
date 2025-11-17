namespace Tinisoft.Shared.Events;

public class OrderCreatedEvent : BaseEvent
{
    public Guid OrderId { get; set; }
    public Guid TenantId { get; set; }
    public string OrderNumber { get; set; } = string.Empty;
    public decimal TotalAmount { get; set; }
}

public class OrderPaidEvent : BaseEvent
{
    public Guid OrderId { get; set; }
    public Guid TenantId { get; set; }
    public string PaymentProvider { get; set; } = string.Empty;
    public string PaymentReference { get; set; } = string.Empty;
}

public class OrderStatusChangedEvent : BaseEvent
{
    public Guid OrderId { get; set; }
    public Guid TenantId { get; set; }
    public string OldStatus { get; set; } = string.Empty;
    public string NewStatus { get; set; } = string.Empty;
}

