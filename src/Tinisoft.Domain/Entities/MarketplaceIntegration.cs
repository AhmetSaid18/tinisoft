using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class MarketplaceIntegration : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public string Marketplace { get; set; } = string.Empty; // Trendyol, Hepsiburada, N11, GittiGidiyor
    public bool IsActive { get; set; }
    
    // API Credentials (encrypted)
    public string? ApiKey { get; set; }
    public string? ApiSecret { get; set; }
    public string? SupplierId { get; set; }
    public string? UserId { get; set; }
    
    // Settings
    public bool AutoSyncProducts { get; set; }
    public bool AutoSyncOrders { get; set; }
    public bool AutoSyncInventory { get; set; }
    
    public DateTime? LastSyncAt { get; set; }
    public string? LastSyncStatus { get; set; }
}

