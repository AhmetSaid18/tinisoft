namespace Tinisoft.Customers.API.Attributes;

/// <summary>
/// Bu attribute ile işaretlenen endpoint'ler belirli bir role sahip kullanıcılar tarafından erişilebilir
/// </summary>
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class)]
public class RequireRoleAttribute : Attribute
{
    public string[] Roles { get; }

    public RequireRoleAttribute(params string[] roles)
    {
        Roles = roles;
    }
}

