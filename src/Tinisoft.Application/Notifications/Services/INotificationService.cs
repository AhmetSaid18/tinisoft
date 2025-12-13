using Tinisoft.Application.Notifications.Models;

namespace Tinisoft.Application.Notifications.Services;

public interface INotificationService
{
    Task<NotificationResult> SendNotificationAsync(NotificationRequest request, CancellationToken cancellationToken = default);
    Task SendOrderConfirmationAsync(Guid orderId, CancellationToken cancellationToken = default);
    Task SendOrderStatusChangeAsync(Guid orderId, string newStatus, CancellationToken cancellationToken = default);
    Task SendShippingNotificationAsync(Guid orderId, string trackingNumber, CancellationToken cancellationToken = default);
    Task SendWelcomeEmailAsync(Guid customerId, CancellationToken cancellationToken = default);
    Task SendPasswordResetAsync(string email, string resetToken, CancellationToken cancellationToken = default);
    Task SendAbandonedCartReminderAsync(Guid customerId, CancellationToken cancellationToken = default);
    Task SendLowStockAlertAsync(Guid productId, int currentStock, CancellationToken cancellationToken = default);
}

