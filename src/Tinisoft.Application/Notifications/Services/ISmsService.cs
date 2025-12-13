using Tinisoft.Application.Notifications.Models;

namespace Tinisoft.Application.Notifications.Services;

public interface ISmsService
{
    Task<NotificationResult> SendSmsAsync(SmsRequest request, CancellationToken cancellationToken = default);
    Task<NotificationResult> SendBulkSmsAsync(List<SmsRequest> requests, CancellationToken cancellationToken = default);
}

