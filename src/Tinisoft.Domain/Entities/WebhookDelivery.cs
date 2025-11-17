using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class WebhookDelivery : BaseEntity
{
    public Guid WebhookId { get; set; }
    public Webhook? Webhook { get; set; }
    
    public string Event { get; set; } = string.Empty;
    public string Payload { get; set; } = string.Empty; // JSON
    public int StatusCode { get; set; }
    public string? ResponseBody { get; set; }
    public DateTime? DeliveredAt { get; set; }
    public int RetryCount { get; set; }
}

