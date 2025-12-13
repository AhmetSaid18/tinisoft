using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using SendGrid;
using SendGrid.Helpers.Mail;
using Tinisoft.Application.Notifications.Models;
using Tinisoft.Application.Notifications.Services;

namespace Tinisoft.Infrastructure.Services;

public class SendGridEmailService : IEmailService
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<SendGridEmailService> _logger;
    private readonly string _apiKey;
    private readonly string _fromEmail;
    private readonly string _fromName;

    public SendGridEmailService(
        IConfiguration configuration,
        ILogger<SendGridEmailService> logger)
    {
        _configuration = configuration;
        _logger = logger;
        _apiKey = _configuration["SendGrid:ApiKey"] ?? throw new InvalidOperationException("SendGrid:ApiKey not configured");
        _fromEmail = _configuration["SendGrid:FromEmail"] ?? "noreply@tinisoft.com";
        _fromName = _configuration["SendGrid:FromName"] ?? "Tinisoft";
    }

    public async Task<NotificationResult> SendEmailAsync(EmailRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var client = new SendGridClient(_apiKey);
            
            var from = new EmailAddress(_fromEmail, _fromName);
            var to = new EmailAddress(request.To, request.ToName ?? request.To);
            
            var msg = MailHelper.CreateSingleEmail(
                from,
                to,
                request.Subject,
                request.TextBody ?? StripHtml(request.HtmlBody),
                request.HtmlBody
            );

            // Add attachments if any
            if (request.Attachments?.Any() == true)
            {
                foreach (var attachment in request.Attachments)
                {
                    msg.AddAttachment(
                        attachment.FileName,
                        Convert.ToBase64String(attachment.Content),
                        attachment.ContentType
                    );
                }
            }

            var response = await client.SendEmailAsync(msg, cancellationToken);

            if (response.IsSuccessStatusCode)
            {
                _logger.LogInformation("Email sent successfully to {Email}", request.To);
                
                return new NotificationResult
                {
                    Success = true,
                    MessageId = response.Headers.GetValues("X-Message-Id").FirstOrDefault(),
                    SentAt = DateTime.UtcNow
                };
            }
            else
            {
                var body = await response.Body.ReadAsStringAsync(cancellationToken);
                _logger.LogError("SendGrid error: {StatusCode} - {Body}", response.StatusCode, body);
                
                return new NotificationResult
                {
                    Success = false,
                    ErrorMessage = $"SendGrid error: {response.StatusCode}",
                    SentAt = DateTime.UtcNow
                };
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to send email to {Email}", request.To);
            
            return new NotificationResult
            {
                Success = false,
                ErrorMessage = ex.Message,
                SentAt = DateTime.UtcNow
            };
        }
    }

    public async Task<NotificationResult> SendBulkEmailAsync(List<EmailRequest> requests, CancellationToken cancellationToken = default)
    {
        // SendGrid allows up to 1000 emails per batch
        var results = new List<bool>();
        
        foreach (var request in requests)
        {
            var result = await SendEmailAsync(request, cancellationToken);
            results.Add(result.Success);
        }

        return new NotificationResult
        {
            Success = results.All(r => r),
            ErrorMessage = results.All(r => r) ? null : $"{results.Count(r => !r)} emails failed",
            SentAt = DateTime.UtcNow
        };
    }

    private static string StripHtml(string html)
    {
        // Simple HTML stripping for plain text fallback
        return System.Text.RegularExpressions.Regex.Replace(html, "<.*?>", string.Empty);
    }
}

