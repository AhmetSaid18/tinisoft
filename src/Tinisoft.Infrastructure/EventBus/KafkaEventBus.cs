using System.Text;
using System.Text.Json;
using Confluent.Kafka;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Tinisoft.Shared.Contracts;
using Tinisoft.Shared.Events;

namespace Tinisoft.Infrastructure.EventBus;

/// <summary>
/// Kafka Event Bus - High-volume event'ler için (Product updates, Order events, Inventory changes)
/// </summary>
public class KafkaEventBus : IEventBus, IDisposable
{
    private readonly IProducer<string, string> _producer;
    private readonly ILogger<KafkaEventBus> _logger;
    private readonly string _bootstrapServers;
    private readonly string _defaultTopicPrefix;

    public KafkaEventBus(IConfiguration configuration, ILogger<KafkaEventBus> logger)
    {
        _logger = logger;
        _bootstrapServers = configuration["Kafka:BootstrapServers"] ?? "localhost:9092";
        _defaultTopicPrefix = configuration["Kafka:TopicPrefix"] ?? "tinisoft";

        var producerConfig = new ProducerConfig
        {
            BootstrapServers = _bootstrapServers,
            Acks = Acks.All, // Tüm replica'ların onayını bekle (durability için)
            RetryBackoffMs = 100,
            MessageSendMaxRetries = 3,
            EnableIdempotence = true, // Duplicate mesajları önle
            CompressionType = CompressionType.Snappy, // Yüksek throughput için
            BatchSize = 16384, // Batch size
            LingerMs = 10 // Batch için bekleme süresi
        };

        _producer = new ProducerBuilder<string, string>(producerConfig)
            .SetErrorHandler((_, e) => 
                _logger.LogError("Kafka producer error: {Reason}", e.Reason))
            .Build();

        _logger.LogInformation("Kafka Event Bus initialized: {BootstrapServers}", _bootstrapServers);
    }

    public Task PublishAsync<T>(T @event, CancellationToken cancellationToken = default) where T : IEvent
    {
        return PublishAsync((IEvent)@event, cancellationToken);
    }

    public async Task PublishAsync(IEvent @event, CancellationToken cancellationToken = default)
    {
        try
        {
            var eventType = @event.GetType().Name;
            var topic = GetTopicName(eventType);
            
            // Partition key: TenantId varsa tenant'a göre partition, yoksa round-robin
            var partitionKey = @event is BaseEvent baseEvent && baseEvent.TenantId.HasValue
                ? baseEvent.TenantId.Value.ToString()
                : Guid.NewGuid().ToString();

            var message = JsonSerializer.Serialize(@event, @event.GetType());
            
            var kafkaMessage = new Message<string, string>
            {
                Key = partitionKey,
                Value = message,
                Headers = new Headers
                {
                    { "EventType", Encoding.UTF8.GetBytes(eventType) },
                    { "EventId", Encoding.UTF8.GetBytes(@event.Id.ToString()) },
                    { "Timestamp", Encoding.UTF8.GetBytes(DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString()) }
                }
            };

            var deliveryResult = await _producer.ProduceAsync(topic, kafkaMessage, cancellationToken);

            _logger.LogInformation(
                "Event published to Kafka: {EventType} - {EventId} to topic {Topic} partition {Partition} offset {Offset}",
                eventType, @event.Id, topic, deliveryResult.Partition, deliveryResult.Offset);
        }
        catch (ProduceException<string, string> ex)
        {
            _logger.LogError(ex, "Error publishing event {EventType} to Kafka: {Error}", 
                @event.GetType().Name, ex.Error.Reason);
            throw;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unexpected error publishing event {EventType} to Kafka", 
                @event.GetType().Name);
            throw;
        }
    }

    private string GetTopicName(string eventType)
    {
        // Event type'a göre topic belirle
        // Örnek: ProductCreatedEvent -> tinisoft.products
        //        OrderCreatedEvent -> tinisoft.orders
        //        ProductStockChangedEvent -> tinisoft.inventory
        
        if (eventType.Contains("Product", StringComparison.OrdinalIgnoreCase))
            return $"{_defaultTopicPrefix}.products";
        
        if (eventType.Contains("Order", StringComparison.OrdinalIgnoreCase))
            return $"{_defaultTopicPrefix}.orders";
        
        if (eventType.Contains("Stock", StringComparison.OrdinalIgnoreCase) || 
            eventType.Contains("Inventory", StringComparison.OrdinalIgnoreCase))
            return $"{_defaultTopicPrefix}.inventory";
        
        // Default topic
        return $"{_defaultTopicPrefix}.events";
    }

    public void Dispose()
    {
        _producer?.Flush(TimeSpan.FromSeconds(10));
        _producer?.Dispose();
    }
}

