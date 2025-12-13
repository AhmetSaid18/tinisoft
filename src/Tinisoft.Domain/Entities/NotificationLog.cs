using Tinisoft.Domain.Common;
using Tinisoft.Domain.Enums;

namespace Tinisoft.Domain.Entities;

public class NotificationLog : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public NotificationType Type { get; set; }
    public NotificationChannel Channel { get; set; }
    
    // Recipient info
    public string Recipient { get; set; } = string.Empty; // Email or phone
    public string? RecipientName { get; set; }
    public Guid? CustomerId { get; set; }
    
    // Content
    public string Subject { get; set; } = string.Empty;
    public string Body { get; set; } = string.Empty;
    
    // Delivery status
    public bool IsSent { get; set; }
    public DateTime? SentAt { get; set; }
    public bool IsDelivered { get; set; }
    public DateTime? DeliveredAt { get; set; }
    public bool IsFailed { get; set; }
    public string? FailureReason { get; set; }
    
    // Reference
    public Guid? OrderId { get; set; }
    public Guid? ProductId { get; set; }
    
    // Provider info
    public string? ProviderMessageId { get; set; } // SendGrid/Netgsm message ID
    public string? Metadata { get; set; } // JSON for additional data
    
    // Navigation
    public virtual Tenant Tenant { get; set; } = null!;
    public virtual Customer? Customer { get; set; }
    public virtual Order? Order { get; set; }
}

