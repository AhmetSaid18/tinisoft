using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class User : BaseEntity
{
    public string Email { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    public string? FirstName { get; set; }
    public string? LastName { get; set; }
    public bool IsActive { get; set; } = true;
    public bool EmailVerified { get; set; }
    
    // 2FA
    public bool TwoFactorEnabled { get; set; }
    public string? TwoFactorSecret { get; set; }
    
    // Navigation
    public ICollection<UserTenantRole> UserTenantRoles { get; set; } = new List<UserTenantRole>();
}

