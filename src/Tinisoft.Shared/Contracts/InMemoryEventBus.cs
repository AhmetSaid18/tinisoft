using Tinisoft.Shared.Events;
using Microsoft.Extensions.Logging;

namespace Tinisoft.Shared.Contracts;

public class InMemoryEventBus : IEventBus
{
    private readonly ILogger<InMemoryEventBus> _logger;
    private readonly List<Func<IEvent, CancellationToken, Task>> _handlers = new();

    public InMemoryEventBus(ILogger<InMemoryEventBus> logger)
    {
        _logger = logger;
    }

    public Task PublishAsync<T>(T @event, CancellationToken cancellationToken = default) where T : IEvent
    {
        return PublishAsync((IEvent)@event, cancellationToken);
    }

    public async Task PublishAsync(IEvent @event, CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Publishing event: {EventType} - {EventId}", @event.GetType().Name, @event.Id);

        // In-memory implementation - ileride RabbitMQ/Kafka ile değiştirilebilir
        foreach (var handler in _handlers)
        {
            try
            {
                await handler(@event, cancellationToken);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error handling event {EventType}", @event.GetType().Name);
            }
        }
    }

    public void Subscribe<T>(Func<T, CancellationToken, Task> handler) where T : IEvent
    {
        _handlers.Add((evt, ct) =>
        {
            if (evt is T typedEvent)
            {
                return handler(typedEvent, ct);
            }
            return Task.CompletedTask;
        });
    }
}

