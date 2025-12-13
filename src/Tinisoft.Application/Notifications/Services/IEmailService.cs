using Tinisoft.Application.Notifications.Models;

namespace Tinisoft.Application.Notifications.Services;

public interface IEmailService
{
    Task<NotificationResult> SendEmailAsync(EmailRequest request, CancellationToken cancellationToken = default);
    Task<NotificationResult> SendBulkEmailAsync(List<EmailRequest> requests, CancellationToken cancellationToken = default);
}
