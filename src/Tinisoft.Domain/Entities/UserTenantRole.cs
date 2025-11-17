using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class UserTenantRole : BaseEntity
{
    public Guid UserId { get; set; }
    public User? User { get; set; }
    
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public string Role { get; set; } = "Member"; // Owner, Admin, Member
}

