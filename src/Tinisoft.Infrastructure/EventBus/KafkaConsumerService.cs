using System.Text;
using System.Text.Json;
using Confluent.Kafka;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Tinisoft.Application.Products.Services;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Events;

namespace Tinisoft.Infrastructure.EventBus;

/// <summary>
/// Kafka Consumer Service - Background service olarak çalışır, event'leri consume eder
/// </summary>
public class KafkaConsumerService : BackgroundService
{
    private readonly IConsumer<string, string> _consumer;
    private readonly ILogger<KafkaConsumerService> _logger;
    private readonly IServiceProvider _serviceProvider;
    private readonly string[] _topics;

    public KafkaConsumerService(
        IConfiguration configuration,
        ILogger<KafkaConsumerService> logger,
        IServiceProvider serviceProvider)
    {
        _logger = logger;
        _serviceProvider = serviceProvider;

        var bootstrapServers = configuration["Kafka:BootstrapServers"] ?? "localhost:9092";
        var topicPrefix = configuration["Kafka:TopicPrefix"] ?? "tinisoft";
        var consumerGroup = configuration["Kafka:ConsumerGroup"] ?? "tinisoft-consumers";

        _topics = new[]
        {
            $"{topicPrefix}.products",
            $"{topicPrefix}.orders",
            $"{topicPrefix}.inventory"
        };

        var consumerConfig = new ConsumerConfig
        {
            BootstrapServers = bootstrapServers,
            GroupId = consumerGroup,
            AutoOffsetReset = AutoOffsetReset.Earliest, // İlk mesajdan başla
            EnableAutoCommit = false, // Manuel commit (işlem başarılı olursa commit)
            EnablePartitionEof = true,
            MaxPollIntervalMs = 300000 // 5 dakika
        };

        _consumer = new ConsumerBuilder<string, string>(consumerConfig)
            .SetErrorHandler((_, e) => 
                _logger.LogError("Kafka consumer error: {Reason}", e.Reason))
            .Build();

        _consumer.Subscribe(_topics);
        _logger.LogInformation("Kafka Consumer Service started. Topics: {Topics}, Group: {Group}", 
            string.Join(", ", _topics), consumerGroup);
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        try
        {
            while (!stoppingToken.IsCancellationRequested)
            {
                try
                {
                    var result = _consumer.Consume(stoppingToken);

                    if (result.IsPartitionEOF)
                    {
                        _logger.LogDebug("Reached end of partition {Partition}", result.Partition);
                        continue;
                    }

                    await ProcessMessageAsync(result, stoppingToken);
                    
                    // İşlem başarılı oldu, commit et
                    _consumer.Commit(result);
                }
                catch (ConsumeException ex)
                {
                    // Topic henüz oluşturulmamışsa (normal durum), sadece debug log
                    if (ex.Error.Code == ErrorCode.UnknownTopicOrPart)
                    {
                        _logger.LogDebug("Kafka topic not yet available: {Reason}. Will retry...", ex.Error.Reason);
                        // Topic oluşana kadar bekle
                        await Task.Delay(5000, stoppingToken);
                    }
                    else
                    {
                        _logger.LogError(ex, "Error consuming message from Kafka: {Reason}", ex.Error.Reason);
                    }
                    // Hata durumunda continue et, bir sonraki mesaja geç
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Unexpected error in Kafka consumer");
                }
            }
        }
        catch (OperationCanceledException)
        {
            _logger.LogInformation("Kafka Consumer Service is stopping");
        }
        finally
        {
            _consumer.Close();
        }
    }

    private async Task ProcessMessageAsync(ConsumeResult<string, string> result, CancellationToken cancellationToken)
    {
        try
        {
            var eventTypeHeader = result.Message.Headers?.FirstOrDefault(h => h.Key == "EventType");
            if (eventTypeHeader == null)
            {
                _logger.LogWarning("Message missing EventType header. Topic: {Topic}, Partition: {Partition}, Offset: {Offset}",
                    result.Topic, result.Partition, result.Offset);
                return;
            }

            var eventTypeName = Encoding.UTF8.GetString(eventTypeHeader.GetValueBytes());
            _logger.LogDebug("Processing event: {EventType} from topic {Topic}", eventTypeName, result.Topic);

            // Event type'a göre işle
            switch (eventTypeName)
            {
                case nameof(ProductCreatedEvent):
                case nameof(ProductUpdatedEvent):
                case nameof(ProductDeletedEvent):
                    await HandleProductEventAsync(eventTypeName, result.Message.Value, cancellationToken);
                    break;

                case nameof(ProductStockChangedEvent):
                    await HandleStockEventAsync(result.Message.Value, cancellationToken);
                    break;

                case nameof(OrderCreatedEvent):
                case nameof(OrderPaidEvent):
                case nameof(OrderStatusChangedEvent):
                    await HandleOrderEventAsync(eventTypeName, result.Message.Value, cancellationToken);
                    break;

                default:
                    _logger.LogWarning("Unknown event type: {EventType}", eventTypeName);
                    break;
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing message from topic {Topic}, partition {Partition}, offset {Offset}",
                result.Topic, result.Partition, result.Offset);
            throw; // Re-throw to prevent commit
        }
    }

    private async Task HandleProductEventAsync(string eventType, string messageJson, CancellationToken cancellationToken)
    {
        using var scope = _serviceProvider.CreateScope();
        var meilisearchService = scope.ServiceProvider.GetRequiredService<IMeilisearchService>();

        try
        {
            if (eventType == nameof(ProductCreatedEvent))
            {
                var @event = JsonSerializer.Deserialize<ProductCreatedEvent>(messageJson);
                if (@event != null)
                {
                    _logger.LogInformation("Product created event received: ProductId: {ProductId}, TenantId: {TenantId}", 
                        @event.ProductId, @event.TenantId);
                    // MeilisearchService zaten product'ı index ediyor (CreateProductCommandHandler'da)
                    // Burada sadece log, ileride başka işlemler eklenebilir (analytics, notifications, etc.)
                }
            }
            else if (eventType == nameof(ProductUpdatedEvent))
            {
                var @event = JsonSerializer.Deserialize<ProductUpdatedEvent>(messageJson);
                if (@event != null)
                {
                    _logger.LogInformation("Product updated event received: ProductId: {ProductId}, TenantId: {TenantId}", 
                        @event.ProductId, @event.TenantId);
                    // MeilisearchService zaten product'ı index ediyor (UpdateProductCommandHandler'da)
                    // Burada sadece log, ileride cache invalidation vs. eklenebilir
                }
            }
            else if (eventType == nameof(ProductDeletedEvent))
            {
                var @event = JsonSerializer.Deserialize<ProductDeletedEvent>(messageJson);
                if (@event != null)
                {
                    await meilisearchService.DeleteProductAsync(@event.ProductId, @event.TenantId, cancellationToken);
                    _logger.LogInformation("Product deleted from Meilisearch: {ProductId}", @event.ProductId);
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error handling product event: {EventType}", eventType);
            throw;
        }
    }

    private async Task HandleStockEventAsync(string messageJson, CancellationToken cancellationToken)
    {
        try
        {
            var @event = JsonSerializer.Deserialize<ProductStockChangedEvent>(messageJson);
            if (@event != null)
            {
                // Cache invalidation için
                using var scope = _serviceProvider.CreateScope();
                var cacheService = scope.ServiceProvider.GetRequiredService<ICacheService>();
                
                // Product cache'ini invalidate et
                await cacheService.RemoveAsync($"product:{@event.ProductId}", cancellationToken);
                await cacheService.RemoveAsync($"product:stock:{@event.ProductId}", cancellationToken);
                
                _logger.LogInformation("Stock changed event processed. ProductId: {ProductId}, Cache invalidated", 
                    @event.ProductId);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error handling stock event");
            throw;
        }
    }

    private async Task HandleOrderEventAsync(string eventType, string messageJson, CancellationToken cancellationToken)
    {
        try
        {
            _logger.LogInformation("Order event received: {EventType}", eventType);
            // İleride analytics, notification, vs. için kullanılabilir
            await Task.CompletedTask;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error handling order event: {EventType}", eventType);
            throw;
        }
    }

    public override void Dispose()
    {
        _consumer?.Dispose();
        base.Dispose();
    }
}

