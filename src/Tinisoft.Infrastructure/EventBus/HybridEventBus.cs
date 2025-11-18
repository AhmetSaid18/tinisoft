using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Tinisoft.Shared.Contracts;
using Tinisoft.Shared.Events;

namespace Tinisoft.Infrastructure.EventBus;

/// <summary>
/// Hybrid Event Bus - High-volume event'leri Kafka'ya, basit event'leri RabbitMQ'ya yönlendirir
/// </summary>
public class HybridEventBus : IEventBus
{
    private readonly IEventBus _kafkaEventBus;
    private readonly IEventBus _rabbitMQEventBus;
    private readonly ILogger<HybridEventBus> _logger;
    private readonly HashSet<string> _kafkaEventTypes;

    public HybridEventBus(
        KafkaEventBus kafkaEventBus,
        RabbitMQEventBus rabbitMQEventBus,
        ILogger<HybridEventBus> logger)
    {
        _kafkaEventBus = kafkaEventBus;
        _rabbitMQEventBus = rabbitMQEventBus;
        _logger = logger;

        // Kafka'ya gidecek high-volume event'ler
        _kafkaEventTypes = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            nameof(ProductCreatedEvent),
            nameof(ProductUpdatedEvent),
            nameof(ProductDeletedEvent),
            nameof(ProductStockChangedEvent),
            nameof(OrderCreatedEvent),
            nameof(OrderPaidEvent),
            nameof(OrderStatusChangedEvent)
        };
    }

    public Task PublishAsync<T>(T @event, CancellationToken cancellationToken = default) where T : IEvent
    {
        return PublishAsync((IEvent)@event, cancellationToken);
    }

    public async Task PublishAsync(IEvent @event, CancellationToken cancellationToken = default)
    {
        var eventType = @event.GetType().Name;

        // High-volume event'ler Kafka'ya, diğerleri RabbitMQ'ya
        if (_kafkaEventTypes.Contains(eventType))
        {
            _logger.LogDebug("Routing {EventType} to Kafka", eventType);
            await _kafkaEventBus.PublishAsync(@event, cancellationToken);
        }
        else
        {
            _logger.LogDebug("Routing {EventType} to RabbitMQ", eventType);
            await _rabbitMQEventBus.PublishAsync(@event, cancellationToken);
        }
    }
}

