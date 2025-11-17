using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class Webhook : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public string Url { get; set; } = string.Empty;
    public string Secret { get; set; } = string.Empty; // HMAC signing için
    public List<string> Events { get; set; } = new(); // order.created, product.updated, etc.
    public bool IsActive { get; set; } = true;
    
    public ICollection<WebhookDelivery> Deliveries { get; set; } = new List<WebhookDelivery>();
}

