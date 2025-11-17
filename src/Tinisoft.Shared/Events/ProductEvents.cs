namespace Tinisoft.Shared.Events;

public class ProductCreatedEvent : BaseEvent
{
    public Guid ProductId { get; set; }
    public Guid TenantId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string SKU { get; set; } = string.Empty;
}

public class ProductUpdatedEvent : BaseEvent
{
    public Guid ProductId { get; set; }
    public Guid TenantId { get; set; }
    public string? Changes { get; set; }
}

public class ProductDeletedEvent : BaseEvent
{
    public Guid ProductId { get; set; }
    public Guid TenantId { get; set; }
}

public class ProductStockChangedEvent : BaseEvent
{
    public Guid ProductId { get; set; }
    public Guid? VariantId { get; set; }
    public Guid TenantId { get; set; }
    public int OldQuantity { get; set; }
    public int NewQuantity { get; set; }
    public string Reason { get; set; } = string.Empty; // Sale, Restock, Adjustment, etc.
}

