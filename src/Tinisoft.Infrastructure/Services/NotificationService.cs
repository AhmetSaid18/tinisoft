using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.Notifications.Models;
using Tinisoft.Application.Notifications.Services;
using Tinisoft.Domain.Entities;
using Tinisoft.Domain.Enums;
using Finbuckle.MultiTenant;

namespace Tinisoft.Infrastructure.Services;

public class NotificationService : INotificationService
{
    private readonly IApplicationDbContext _context;
    private readonly IEmailService _emailService;
    private readonly ISmsService _smsService;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<NotificationService> _logger;

    public NotificationService(
        IApplicationDbContext context,
        IEmailService emailService,
        ISmsService smsService,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<NotificationService> logger)
    {
        _context = context;
        _emailService = emailService;
        _smsService = smsService;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<NotificationResult> SendNotificationAsync(NotificationRequest request, CancellationToken cancellationToken = default)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);
        
        // Get template
        var template = await _context.EmailTemplates
            .Where(t => t.TenantId == tenantId && t.Type == request.Type && t.IsActive)
            .FirstOrDefaultAsync(cancellationToken);

        // If no custom template, get system default
        template ??= await _context.EmailTemplates
            .Where(t => t.IsDefault && t.Type == request.Type)
            .FirstOrDefaultAsync(cancellationToken);

        NotificationResult result;

        // Send based on channel
        if (request.Channel == NotificationChannel.Email || request.Channel == NotificationChannel.Both)
        {
            var subject = ReplaceVariables(request.Subject ?? template?.Subject ?? "", request.Variables);
            var body = ReplaceVariables(request.Body ?? template?.HtmlBody ?? "", request.Variables);

            var emailRequest = new EmailRequest
            {
                To = request.Recipient,
                ToName = request.RecipientName,
                Subject = subject,
                HtmlBody = body
            };

            result = await _emailService.SendEmailAsync(emailRequest, cancellationToken);
            
            // Log notification
            await LogNotificationAsync(tenantId, request, NotificationChannel.Email, result, subject, body, cancellationToken);
        }

        if (request.Channel == NotificationChannel.Sms || request.Channel == NotificationChannel.Both)
        {
            var message = ReplaceVariables(request.Body ?? template?.SmsBody ?? "", request.Variables);

            var smsRequest = new SmsRequest
            {
                PhoneNumber = request.Recipient,
                Message = message
            };

            result = await _smsService.SendSmsAsync(smsRequest, cancellationToken);
            
            // Log notification
            await LogNotificationAsync(tenantId, request, NotificationChannel.Sms, result, "", message, cancellationToken);
        }
        else
        {
            result = new NotificationResult { Success = true, SentAt = DateTime.UtcNow };
        }

        return result;
    }

    public async Task SendOrderConfirmationAsync(Guid orderId, CancellationToken cancellationToken = default)
    {
        var order = await _context.Orders
            .Include(o => o.Customer)
            .Include(o => o.OrderItems)
            .ThenInclude(oi => oi.Product)
            .FirstOrDefaultAsync(o => o.Id == orderId, cancellationToken);

        if (order == null || order.Customer == null)
        {
            _logger.LogWarning("Order {OrderId} or customer not found for confirmation email", orderId);
            return;
        }

        // Parse totals from JSON
        var totals = System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, decimal>>(order.TotalsJson ?? "{}");
        var totalAmount = totals?.GetValueOrDefault("total", 0) ?? 0;
        
        var variables = new Dictionary<string, string>
        {
            { "CustomerName", order.Customer.FirstName + " " + order.Customer.LastName },
            { "OrderNumber", order.OrderNumber },
            { "OrderDate", order.CreatedAt.ToString("dd.MM.yyyy HH:mm") },
            { "TotalAmount", totalAmount.ToString("N2") + " TL" },
            { "OrderItems", string.Join("<br>", order.OrderItems.Select(oi => $"{oi.Product?.Title ?? "Unknown"} x {oi.Quantity}")) }
        };

        await SendNotificationAsync(new NotificationRequest
        {
            Type = NotificationType.OrderConfirmation,
            Channel = NotificationChannel.Email,
            Recipient = order.Customer.Email,
            RecipientName = order.Customer.FirstName + " " + order.Customer.LastName,
            CustomerId = order.CustomerId,
            OrderId = orderId,
            Variables = variables
        }, cancellationToken);
    }

    public async Task SendOrderStatusChangeAsync(Guid orderId, string newStatus, CancellationToken cancellationToken = default)
    {
        var order = await _context.Orders
            .Include(o => o.Customer)
            .FirstOrDefaultAsync(o => o.Id == orderId, cancellationToken);

        if (order == null || order.Customer == null)
            return;

        var variables = new Dictionary<string, string>
        {
            { "CustomerName", order.Customer.FirstName + " " + order.Customer.LastName },
            { "OrderNumber", order.OrderNumber },
            { "NewStatus", newStatus },
            { "StatusDate", DateTime.UtcNow.ToString("dd.MM.yyyy HH:mm") }
        };

        await SendNotificationAsync(new NotificationRequest
        {
            Type = NotificationType.OrderStatusChanged,
            Channel = NotificationChannel.Both,
            Recipient = order.Customer.Email,
            RecipientName = order.Customer.FirstName + " " + order.Customer.LastName,
            CustomerId = order.CustomerId,
            OrderId = orderId,
            Variables = variables
        }, cancellationToken);
    }

    public async Task SendShippingNotificationAsync(Guid orderId, string trackingNumber, CancellationToken cancellationToken = default)
    {
        var order = await _context.Orders
            .Include(o => o.Customer)
            .FirstOrDefaultAsync(o => o.Id == orderId, cancellationToken);

        if (order == null || order.Customer == null)
            return;

        var variables = new Dictionary<string, string>
        {
            { "CustomerName", order.Customer.FirstName + " " + order.Customer.LastName },
            { "OrderNumber", order.OrderNumber },
            { "TrackingNumber", trackingNumber },
            { "ShipDate", DateTime.UtcNow.ToString("dd.MM.yyyy") }
        };

        await SendNotificationAsync(new NotificationRequest
        {
            Type = NotificationType.OrderShipped,
            Channel = NotificationChannel.Both,
            Recipient = order.Customer.Email,
            RecipientName = order.Customer.FirstName + " " + order.Customer.LastName,
            CustomerId = order.CustomerId,
            OrderId = orderId,
            Variables = variables
        }, cancellationToken);
    }

    public async Task SendWelcomeEmailAsync(Guid customerId, CancellationToken cancellationToken = default)
    {
        var customer = await _context.Customers.FindAsync(new object[] { customerId }, cancellationToken);
        if (customer == null)
            return;

        var variables = new Dictionary<string, string>
        {
            { "CustomerName", customer.FirstName + " " + customer.LastName },
            { "Email", customer.Email }
        };

        await SendNotificationAsync(new NotificationRequest
        {
            Type = NotificationType.WelcomeEmail,
            Channel = NotificationChannel.Email,
            Recipient = customer.Email,
            RecipientName = customer.FirstName + " " + customer.LastName,
            CustomerId = customerId,
            Variables = variables
        }, cancellationToken);
    }

    public async Task SendPasswordResetAsync(string email, string resetToken, CancellationToken cancellationToken = default)
    {
        var variables = new Dictionary<string, string>
        {
            { "Email", email },
            { "ResetToken", resetToken },
            { "ResetLink", $"https://app.tinisoft.com/reset-password?token={resetToken}" }
        };

        await SendNotificationAsync(new NotificationRequest
        {
            Type = NotificationType.PasswordReset,
            Channel = NotificationChannel.Email,
            Recipient = email,
            Variables = variables
        }, cancellationToken);
    }

    public async Task SendAbandonedCartReminderAsync(Guid customerId, CancellationToken cancellationToken = default)
    {
        var customer = await _context.Customers.FindAsync(new object[] { customerId }, cancellationToken);
        if (customer == null)
            return;

        var variables = new Dictionary<string, string>
        {
            { "CustomerName", customer.FirstName + " " + customer.LastName },
            { "CartLink", "https://yourstore.com/cart" }
        };

        await SendNotificationAsync(new NotificationRequest
        {
            Type = NotificationType.AbandonedCart,
            Channel = NotificationChannel.Email,
            Recipient = customer.Email,
            RecipientName = customer.FirstName + " " + customer.LastName,
            CustomerId = customerId,
            Variables = variables
        }, cancellationToken);
    }

    public async Task SendLowStockAlertAsync(Guid productId, int currentStock, CancellationToken cancellationToken = default)
    {
        var product = await _context.Products.FindAsync(new object[] { productId }, cancellationToken);
        if (product == null)
            return;

        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);
        var tenant = await _context.Tenants.FindAsync(new object[] { tenantId }, cancellationToken);
        // Tenant'ın email'i yoksa notification gönderme
        if (tenant == null)
            return;

        var variables = new Dictionary<string, string>
        {
            { "ProductName", product.Title },
            { "ProductSKU", product.SKU ?? string.Empty },
            { "CurrentStock", currentStock.ToString() },
            { "AlertDate", DateTime.UtcNow.ToString("dd.MM.yyyy HH:mm") }
        };

        // Tenant'ın email adresi yoksa notification gönderme
        var recipientEmail = tenant.Slug + "@tinisoft.com"; // Fallback email
        await SendNotificationAsync(new NotificationRequest
        {
            Type = NotificationType.LowStockAlert,
            Channel = NotificationChannel.Email,
            Recipient = recipientEmail,
            ProductId = productId,
            Variables = variables
        }, cancellationToken);
    }

    private static string ReplaceVariables(string template, Dictionary<string, string>? variables)
    {
        if (variables == null || !variables.Any())
            return template;

        foreach (var variable in variables)
        {
            template = template.Replace($"{{{{{variable.Key}}}}}", variable.Value);
        }

        return template;
    }

    private async Task LogNotificationAsync(
        Guid tenantId,
        NotificationRequest request,
        NotificationChannel channel,
        NotificationResult result,
        string subject,
        string body,
        CancellationToken cancellationToken)
    {
        var log = new NotificationLog
        {
            TenantId = tenantId,
            Type = request.Type,
            Channel = channel,
            Recipient = request.Recipient,
            RecipientName = request.RecipientName,
            CustomerId = request.CustomerId,
            Subject = subject,
            Body = body,
            IsSent = result.Success,
            SentAt = result.Success ? result.SentAt : null,
            IsDelivered = result.Success,
            DeliveredAt = result.Success ? result.SentAt : null,
            IsFailed = !result.Success,
            FailureReason = result.ErrorMessage,
            OrderId = request.OrderId,
            ProductId = request.ProductId,
            ProviderMessageId = result.MessageId
        };

        _context.NotificationLogs.Add(log);
        await _context.SaveChangesAsync(cancellationToken);
    }
}

