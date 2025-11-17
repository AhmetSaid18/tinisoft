using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class Warehouse : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public string Name { get; set; } = string.Empty;
    public string? Address { get; set; }
    public string? City { get; set; }
    public string? Country { get; set; }
    public bool IsDefault { get; set; }
    public bool IsActive { get; set; } = true;
}

