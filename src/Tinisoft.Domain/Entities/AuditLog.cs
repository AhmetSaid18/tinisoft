using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class AuditLog : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public Guid? UserId { get; set; }
    public User? User { get; set; }
    
    public string Action { get; set; } = string.Empty; // Created, Updated, Deleted
    public string EntityType { get; set; } = string.Empty; // Product, Order, etc.
    public Guid EntityId { get; set; }
    public string? ChangesJson { get; set; } // Before/After JSON
    public string? IpAddress { get; set; }
    public string? UserAgent { get; set; }
}

