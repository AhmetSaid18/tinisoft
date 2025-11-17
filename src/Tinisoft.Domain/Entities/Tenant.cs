using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class Tenant : BaseEntity
{
    public string Name { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty; // tenant.tinisoft.com için
    public bool IsActive { get; set; } = true;
    public Guid PlanId { get; set; }
    public Plan? Plan { get; set; }
    
    // SaaS Billing
    public DateTime? SubscriptionStartDate { get; set; }
    public DateTime? SubscriptionEndDate { get; set; }
    public string? PayTRSubscriptionToken { get; set; }
    
    // Navigation
    public ICollection<Domain> Domains { get; set; } = new List<Domain>();
    public ICollection<UserTenantRole> UserTenantRoles { get; set; } = new List<UserTenantRole>();
    public ICollection<Product> Products { get; set; } = new List<Product>();
    public ICollection<Order> Orders { get; set; } = new List<Order>();
}

