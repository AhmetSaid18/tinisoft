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
    
    // System Role: SystemAdmin, TenantAdmin, Customer
    // SystemAdmin: Sistem sahipleri (biz) - tüm sistem istatistiklerine erişim
    // TenantAdmin: E-ticaret yapan kişiler (bizden paket alanlar) - kendi tenant'larını yönetir
    // Customer: E-ticaret sitesine giren müşteriler - sadece ürün görüntüleme, sipariş verme
    public string SystemRole { get; set; } = "Customer"; // SystemAdmin, TenantAdmin, Customer
    
    // 2FA
    public bool TwoFactorEnabled { get; set; }
    public string? TwoFactorSecret { get; set; }
    
    // Navigation
    public ICollection<UserTenantRole> UserTenantRoles { get; set; } = new List<UserTenantRole>();
}

