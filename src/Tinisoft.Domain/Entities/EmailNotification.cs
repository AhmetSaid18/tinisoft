using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Gönderilen email'lerin kaydı
/// </summary>
public class EmailNotification : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }

    public Guid? EmailProviderId { get; set; }
    public EmailProvider? EmailProvider { get; set; }

    public Guid? EmailTemplateId { get; set; }
    public EmailTemplate? EmailTemplate { get; set; }

    // Alıcı bilgileri
    public string ToEmail { get; set; } = string.Empty;
    public string? ToName { get; set; }
    public string? CcEmail { get; set; }
    public string? BccEmail { get; set; }

    // Email içeriği
    public string Subject { get; set; } = string.Empty;
    public string BodyHtml { get; set; } = string.Empty;
    public string? BodyText { get; set; }

    // Durum
    public string Status { get; set; } = "Pending"; // Pending, Sent, Failed, Bounced
    public DateTime? SentAt { get; set; }
    public string? ErrorMessage { get; set; }

    // Referans bilgileri
    public Guid? ReferenceId { get; set; } // OrderId, ProductId, vb.
    public string? ReferenceType { get; set; } // "Order", "Product", "Customer", vb.

    // Provider yanıt bilgileri
    public string? ProviderResponseJson { get; set; } // Email provider'dan gelen yanıt
}

