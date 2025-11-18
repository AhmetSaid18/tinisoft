using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Email şablonları
/// </summary>
public class EmailTemplate : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }

    public string TemplateCode { get; set; } = string.Empty; // "ORDER_CONFIRMATION", "ORDER_SHIPPED", "LOW_STOCK_ALERT", vb.
    public string TemplateName { get; set; } = string.Empty;
    public string Subject { get; set; } = string.Empty; // Email konusu (template variable'lar içerebilir: {{OrderNumber}})
    public string BodyHtml { get; set; } = string.Empty; // HTML body
    public string? BodyText { get; set; } // Plain text body (opsiyonel)

    public bool IsActive { get; set; } = true;
}

