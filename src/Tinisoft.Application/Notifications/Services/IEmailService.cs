namespace Tinisoft.Application.Notifications.Services;

public interface IEmailService
{
    Task<SendEmailResult> SendEmailAsync(
        Domain.Entities.EmailProvider provider,
        Domain.Entities.EmailNotification notification,
        CancellationToken cancellationToken = default);
}

public class SendEmailResult
{
    public bool Success { get; set; }
    public string? ErrorMessage { get; set; }
    public string? ProviderResponseJson { get; set; }
}

