using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Email provider (SMTP) ayarları
/// </summary>
public class EmailProvider : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }

    public string ProviderName { get; set; } = string.Empty; // "SMTP", "SendGrid", "Mailgun", vb.
    public bool IsActive { get; set; } = true;
    public bool IsDefault { get; set; } = false;

    // SMTP Ayarları
    public string SmtpHost { get; set; } = string.Empty;
    public int SmtpPort { get; set; } = 587;
    public bool EnableSsl { get; set; } = true;
    public string SmtpUsername { get; set; } = string.Empty;
    public string SmtpPassword { get; set; } = string.Empty; // Encrypted olmalı

    // Gönderen bilgileri
    public string FromEmail { get; set; } = string.Empty;
    public string FromName { get; set; } = string.Empty;
    public string? ReplyToEmail { get; set; }

    // Ek ayarlar (JSON formatında)
    public string? SettingsJson { get; set; } // Özel ayarlar
}

