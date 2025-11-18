using MediatR;

namespace Tinisoft.Application.Notifications.Commands.CreateEmailProvider;

public class CreateEmailProviderCommand : IRequest<CreateEmailProviderResponse>
{
    public string ProviderName { get; set; } = string.Empty;
    public string SmtpHost { get; set; } = string.Empty;
    public int SmtpPort { get; set; } = 587;
    public bool EnableSsl { get; set; } = true;
    public string SmtpUsername { get; set; } = string.Empty;
    public string SmtpPassword { get; set; } = string.Empty;
    public string FromEmail { get; set; } = string.Empty;
    public string FromName { get; set; } = string.Empty;
    public string? ReplyToEmail { get; set; }
    public string? SettingsJson { get; set; }
    public bool IsDefault { get; set; } = false;
}

public class CreateEmailProviderResponse
{
    public Guid EmailProviderId { get; set; }
    public string ProviderName { get; set; } = string.Empty;
}

