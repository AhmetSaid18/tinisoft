using Tinisoft.Domain.Common;
using Tinisoft.Domain.Enums;

namespace Tinisoft.Domain.Entities;

public class EmailTemplate : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public NotificationType Type { get; set; }
    
    public string TemplateCode { get; set; } = string.Empty; // "ORDER_CONFIRMATION", "ORDER_SHIPPED", vb.
    public string TemplateName { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty; // Alias for TemplateName (backward compatibility)
    public string Subject { get; set; } = string.Empty;
    public string HtmlBody { get; set; } = string.Empty;
    public string BodyHtml { get => HtmlBody; set => HtmlBody = value; } // Alias for HtmlBody (backward compatibility)
    public string? TextBody { get; set; } // Plain text fallback
    public string? BodyText { get => TextBody; set => TextBody = value; } // Alias for TextBody (backward compatibility)
    
    // SMS template (for same notification type)
    public string? SmsBody { get; set; }
    
    public bool IsActive { get; set; } = true;
    public bool IsDefault { get; set; } // System default template
    
    // Variables guide (e.g., {{CustomerName}}, {{OrderNumber}})
    public string? AvailableVariables { get; set; }
    
    // Localization
    public string Language { get; set; } = "tr-TR";
    
    // Navigation
    public virtual Tenant Tenant { get; set; } = null!;
}
