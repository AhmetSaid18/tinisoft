namespace Tinisoft.Shared.Events;

public abstract class BaseEvent : IEvent
{
    public Guid Id { get; } = Guid.NewGuid();
    public DateTime OccurredOn { get; } = DateTime.UtcNow;
}

