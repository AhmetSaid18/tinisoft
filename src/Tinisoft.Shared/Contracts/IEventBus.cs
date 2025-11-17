using Tinisoft.Shared.Events;

namespace Tinisoft.Shared.Contracts;

public interface IEventBus
{
    Task PublishAsync<T>(T @event, CancellationToken cancellationToken = default) where T : IEvent;
    Task PublishAsync(IEvent @event, CancellationToken cancellationToken = default);
}

