using System.Net;
using System.Net.Mail;
using Tinisoft.Application.Notifications.Services;
using Microsoft.Extensions.Logging;

namespace Tinisoft.Infrastructure.Services;

public class EmailService : IEmailService
{
    private readonly ILogger<EmailService> _logger;

    public EmailService(ILogger<EmailService> logger)
    {
        _logger = logger;
    }

    public async Task<SendEmailResult> SendEmailAsync(
        Domain.Entities.EmailProvider provider,
        Domain.Entities.EmailNotification notification,
        CancellationToken cancellationToken = default)
    {
        try
        {
            using var smtpClient = new SmtpClient(provider.SmtpHost, provider.SmtpPort)
            {
                EnableSsl = provider.EnableSsl,
                Credentials = new NetworkCredential(provider.SmtpUsername, provider.SmtpPassword),
                DeliveryMethod = SmtpDeliveryMethod.Network
            };

            using var mailMessage = new MailMessage
            {
                From = new MailAddress(provider.FromEmail, provider.FromName),
                Subject = notification.Subject,
                Body = notification.BodyHtml,
                IsBodyHtml = true
            };

            mailMessage.To.Add(new MailAddress(notification.ToEmail, notification.ToName));

            if (!string.IsNullOrEmpty(notification.CcEmail))
            {
                mailMessage.Cc.Add(notification.CcEmail);
            }

            if (!string.IsNullOrEmpty(notification.BccEmail))
            {
                mailMessage.Bcc.Add(notification.BccEmail);
            }

            if (!string.IsNullOrEmpty(provider.ReplyToEmail))
            {
                mailMessage.ReplyToList.Add(provider.ReplyToEmail);
            }

            await smtpClient.SendMailAsync(mailMessage);

            _logger.LogInformation("Email sent successfully to {ToEmail}", notification.ToEmail);

            return new SendEmailResult
            {
                Success = true,
                ProviderResponseJson = "{\"status\":\"sent\",\"method\":\"smtp\"}"
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error sending email to {ToEmail}", notification.ToEmail);
            return new SendEmailResult
            {
                Success = false,
                ErrorMessage = ex.Message
            };
        }
    }
}

