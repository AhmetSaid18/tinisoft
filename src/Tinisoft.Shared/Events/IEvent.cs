namespace Tinisoft.Shared.Events;

public interface IEvent
{
    Guid Id { get; }
    DateTime OccurredOn { get; }
}

