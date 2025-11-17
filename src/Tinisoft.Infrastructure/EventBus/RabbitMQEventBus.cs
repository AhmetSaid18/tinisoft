using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using RabbitMQ.Client;
using Tinisoft.Shared.Contracts;
using Tinisoft.Shared.Events;

namespace Tinisoft.Infrastructure.EventBus;

public class RabbitMQEventBus : IEventBus, IDisposable
{
    private readonly IConnection _connection;
    private readonly IModel _channel;
    private readonly ILogger<RabbitMQEventBus> _logger;
    private readonly string _exchangeName;

    public RabbitMQEventBus(IConfiguration configuration, ILogger<RabbitMQEventBus> logger)
    {
        _logger = logger;
        var hostName = configuration["RabbitMQ:HostName"] ?? "localhost";
        var port = int.Parse(configuration["RabbitMQ:Port"] ?? "5672");
        var userName = configuration["RabbitMQ:UserName"] ?? "guest";
        var password = configuration["RabbitMQ:Password"] ?? "guest";
        _exchangeName = configuration["RabbitMQ:ExchangeName"] ?? "tinisoft_events";

        var factory = new ConnectionFactory
        {
            HostName = hostName,
            Port = port,
            UserName = userName,
            Password = password
        };

        _connection = factory.CreateConnection();
        _channel = _connection.CreateModel();
        
        // Exchange oluştur
        _channel.ExchangeDeclare(_exchangeName, ExchangeType.Topic, durable: true);
        
        _logger.LogInformation("RabbitMQ Event Bus connected to {HostName}:{Port}", hostName, port);
    }

    public Task PublishAsync<T>(T @event, CancellationToken cancellationToken = default) where T : IEvent
    {
        return PublishAsync((IEvent)@event, cancellationToken);
    }

    public Task PublishAsync(IEvent @event, CancellationToken cancellationToken = default)
    {
        try
        {
            var eventName = @event.GetType().Name;
            var routingKey = eventName.ToLower().Replace("event", "");
            
            var message = JsonSerializer.Serialize(@event, @event.GetType());
            var body = Encoding.UTF8.GetBytes(message);

            var properties = _channel.CreateBasicProperties();
            properties.Persistent = true;
            properties.MessageId = @event.Id.ToString();
            properties.Timestamp = new AmqpTimestamp(DateTimeOffset.UtcNow.ToUnixTimeSeconds());
            properties.Type = eventName;

            _channel.BasicPublish(
                exchange: _exchangeName,
                routingKey: routingKey,
                basicProperties: properties,
                body: body);

            _logger.LogInformation("Event published: {EventType} - {EventId} to {RoutingKey}", 
                eventName, @event.Id, routingKey);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error publishing event {EventType}", @event.GetType().Name);
            throw;
        }

        return Task.CompletedTask;
    }

    public void Dispose()
    {
        _channel?.Close();
        _connection?.Close();
        _channel?.Dispose();
        _connection?.Dispose();
    }
}

