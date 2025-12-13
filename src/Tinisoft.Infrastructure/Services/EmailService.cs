using System.Net;
using System.Net.Mail;
using Tinisoft.Application.Notifications.Services;
using Tinisoft.Application.Notifications.Models;
using Microsoft.Extensions.Logging;

namespace Tinisoft.Infrastructure.Services;

public class EmailService : IEmailService
{
    private readonly ILogger<EmailService> _logger;

    public EmailService(ILogger<EmailService> logger)
    {
        _logger = logger;
    }

    public async Task<NotificationResult> SendEmailAsync(EmailRequest request, CancellationToken cancellationToken = default)
    {
        // EmailService artık kullanılmıyor, SendGridEmailService kullanılıyor
        // Bu implementasyon sadece backward compatibility için
        _logger.LogWarning("EmailService.SendEmailAsync called - This service is deprecated. Use SendGridEmailService instead.");
        
        return new NotificationResult
        {
            Success = false,
            ErrorMessage = "EmailService is deprecated. Use SendGridEmailService instead.",
            SentAt = DateTime.UtcNow
        };
    }

    public async Task<NotificationResult> SendBulkEmailAsync(List<EmailRequest> requests, CancellationToken cancellationToken = default)
    {
        var results = new List<NotificationResult>();
        
        foreach (var request in requests)
        {
            var result = await SendEmailAsync(request, cancellationToken);
            results.Add(result);
        }

        var successCount = results.Count(r => r.Success);
        var failureCount = results.Count - successCount;

        return new NotificationResult
        {
            Success = failureCount == 0,
            ErrorMessage = failureCount > 0 ? $"{failureCount} email(s) failed to send" : null,
            SentAt = DateTime.UtcNow
        };
    }
}

