namespace Tinisoft.Shared.Events;

public class ReviewCreatedEvent : BaseEvent
{
    public Guid ReviewId { get; set; }
    public Guid ProductId { get; set; }
    public Guid TenantId { get; set; }
    public int Rating { get; set; }
    public Guid? CustomerId { get; set; }
}

public class ReviewApprovedEvent : BaseEvent
{
    public Guid ReviewId { get; set; }
    public Guid ProductId { get; set; }
    public Guid TenantId { get; set; }
    public int Rating { get; set; }
}

public class ReviewRejectedEvent : BaseEvent
{
    public Guid ReviewId { get; set; }
    public Guid ProductId { get; set; }
    public Guid TenantId { get; set; }
    public string? ModerationNote { get; set; }
}

public class ReviewRepliedEvent : BaseEvent
{
    public Guid ReviewId { get; set; }
    public Guid ProductId { get; set; }
    public Guid TenantId { get; set; }
    public Guid RepliedBy { get; set; }
}

public class ReviewDeletedEvent : BaseEvent
{
    public Guid ReviewId { get; set; }
    public Guid ProductId { get; set; }
    public Guid TenantId { get; set; }
    public int Rating { get; set; }
}
