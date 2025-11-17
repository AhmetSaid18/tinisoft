using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class ApiKey : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public string Name { get; set; } = string.Empty;
    public string Key { get; set; } = string.Empty; // Hashed
    public string KeyPrefix { get; set; } = string.Empty; // İlk 8 karakter (gösterim için)
    public bool IsActive { get; set; } = true;
    public DateTime? ExpiresAt { get; set; }
    public List<string> Permissions { get; set; } = new(); // products:read, orders:write, etc.
    public DateTime? LastUsedAt { get; set; }
}

