namespace Tinisoft.Domain.Common;

public static class Roles
{
    public const string SystemAdmin = "SystemAdmin";
    public const string TenantAdmin = "TenantAdmin";
    public const string Customer = "Customer";
    
    // Tenant içi roller (UserTenantRole için)
    public const string Owner = "Owner";
    public const string Admin = "Admin";
    public const string Member = "Member";
}

