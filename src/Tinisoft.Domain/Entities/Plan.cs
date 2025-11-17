using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class Plan : BaseEntity
{
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public decimal MonthlyPrice { get; set; }
    public decimal YearlyPrice { get; set; }
    
    // Limits
    public int MaxProducts { get; set; }
    public int MaxOrdersPerMonth { get; set; }
    public int MaxStorageGB { get; set; }
    public bool CustomDomainEnabled { get; set; }
    public bool AdvancedAnalytics { get; set; }
    
    public bool IsActive { get; set; } = true;
    
    // Navigation
    public ICollection<Tenant> Tenants { get; set; } = new List<Tenant>();
}

