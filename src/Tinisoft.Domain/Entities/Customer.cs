using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Storefront müşterisi (B2C)
/// </summary>
public class Customer : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }

    public string Email { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    public string? FirstName { get; set; }
    public string? LastName { get; set; }
    public string? Phone { get; set; }
    public bool EmailVerified { get; set; }
    public DateTime? LastLoginAt { get; set; }
    public bool IsActive { get; set; } = true;

    // Default addresses
    public Guid? DefaultShippingAddressId { get; set; }
    public Guid? DefaultBillingAddressId { get; set; }

    // Password reset
    public string? ResetPasswordToken { get; set; }
    public DateTime? ResetPasswordTokenExpiresAt { get; set; }

    // Navigation
    public ICollection<CustomerAddress> Addresses { get; set; } = new List<CustomerAddress>();
    public ICollection<Order> Orders { get; set; } = new List<Order>();
}


