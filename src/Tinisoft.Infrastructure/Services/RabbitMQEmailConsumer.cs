using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;
using System.Text;
using System.Text.Json;
using Tinisoft.Shared.Events;
using Tinisoft.Application.Notifications.Commands.SendEmail;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;

namespace Tinisoft.Infrastructure.Services;

/// <summary>
/// RabbitMQ'dan event'leri dinleyip email gönderen background service
/// </summary>
public class RabbitMQEmailConsumer : BackgroundService
{
    private readonly IServiceProvider _serviceProvider;
    private readonly ILogger<RabbitMQEmailConsumer> _logger;
    private readonly IConfiguration _configuration;
    private IConnection? _connection;
    private IModel? _channel;

    public RabbitMQEmailConsumer(
        IServiceProvider serviceProvider,
        ILogger<RabbitMQEmailConsumer> logger,
        IConfiguration configuration)
    {
        _serviceProvider = serviceProvider;
        _logger = logger;
        _configuration = configuration;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        try
        {
            var hostName = _configuration["RabbitMQ:HostName"] ?? "localhost";
            var port = int.Parse(_configuration["RabbitMQ:Port"] ?? "5672");
            var userName = _configuration["RabbitMQ:UserName"] ?? "guest";
            var password = _configuration["RabbitMQ:Password"] ?? "guest";
            var exchangeName = _configuration["RabbitMQ:ExchangeName"] ?? "tinisoft_events";

            var factory = new ConnectionFactory
            {
                HostName = hostName,
                Port = port,
                UserName = userName,
                Password = password
            };

            _connection = factory.CreateConnection();
            _channel = _connection.CreateModel();

            // Exchange'i declare et
            _channel.ExchangeDeclare(exchangeName, ExchangeType.Topic, durable: true);

            // Queue oluştur
            var queueName = "notifications_email_queue";
            _channel.QueueDeclare(queueName, durable: true, exclusive: false, autoDelete: false);

            // Queue'yu exchange'e bind et
            _channel.QueueBind(queueName, exchangeName, "order.created");
            _channel.QueueBind(queueName, exchangeName, "order.shipped");
            _channel.QueueBind(queueName, exchangeName, "order.delivered");
            // İleride daha fazla event eklenebilir

            var consumer = new EventingBasicConsumer(_channel);
            consumer.Received += async (model, ea) =>
            {
                try
                {
                    var body = ea.Body.ToArray();
                    var message = Encoding.UTF8.GetString(body);
                    var routingKey = ea.RoutingKey;
                    var eventType = ea.BasicProperties.Type;

                    _logger.LogInformation("Email event received: {EventType} - {RoutingKey}", eventType, routingKey);

                    using var scope = _serviceProvider.CreateScope();
                    var mediator = scope.ServiceProvider.GetRequiredService<IMediator>();

                    if (eventType == nameof(OrderCreatedEvent))
                    {
                        var orderEvent = JsonSerializer.Deserialize<OrderCreatedEvent>(message);
                        if (orderEvent != null)
                        {
                            await HandleOrderCreatedEventAsync(mediator, orderEvent, stoppingToken);
                        }
                    }
                    // İleride OrderShippedEvent, OrderDeliveredEvent, LowStockAlertEvent eklenebilir

                    _channel.BasicAck(ea.DeliveryTag, false);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error processing email event");
                    _channel.BasicNack(ea.DeliveryTag, false, true); // Requeue
                }
            };

            _channel.BasicConsume(queueName, autoAck: false, consumer);

            _logger.LogInformation("RabbitMQ Email Consumer started, listening on queue: {QueueName}", queueName);

            await Task.Delay(Timeout.Infinite, stoppingToken);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error starting RabbitMQ Email Consumer");
        }
    }

    private async Task HandleOrderCreatedEventAsync(IMediator mediator, OrderCreatedEvent orderEvent, CancellationToken cancellationToken)
    {
        using var scope = _serviceProvider.CreateScope();
        var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();

        var order = await dbContext.Orders
            .AsNoTracking()
            .FirstOrDefaultAsync(o => o.Id == orderEvent.OrderId, cancellationToken);

        if (order == null || string.IsNullOrEmpty(order.CustomerEmail))
        {
            _logger.LogWarning("Order not found or customer email missing for order {OrderId}", orderEvent.OrderId);
            return;
        }

        // Order confirmation email gönder
        var sendEmailCommand = new SendEmailCommand
        {
            ToEmail = order.CustomerEmail,
            ToName = $"{order.CustomerFirstName} {order.CustomerLastName}".Trim(),
            Subject = $"Sipariş Onayı - {orderEvent.OrderNumber}",
            BodyHtml = $@"
                <h2>Siparişiniz Alındı</h2>
                <p>Sayın {order.CustomerFirstName},</p>
                <p>Siparişiniz başarıyla alındı.</p>
                <p><strong>Sipariş No:</strong> {orderEvent.OrderNumber}</p>
                <p><strong>Tutar:</strong> {orderEvent.TotalAmount:C}</p>
                <p>Teşekkür ederiz.</p>
            ",
            ReferenceId = orderEvent.OrderId,
            ReferenceType = "Order"
        };

        await mediator.Send(sendEmailCommand, cancellationToken);
        _logger.LogInformation("Order confirmation email sent for order {OrderNumber}", orderEvent.OrderNumber);
    }

    public override void Dispose()
    {
        _channel?.Close();
        _connection?.Close();
        _channel?.Dispose();
        _connection?.Dispose();
        base.Dispose();
    }
}

