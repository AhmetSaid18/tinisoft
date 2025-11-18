namespace Tinisoft.Notifications.API.Attributes;

[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class)]
public class RequireRoleAttribute : Attribute
{
    public string[] Roles { get; }

    public RequireRoleAttribute(params string[] roles)
    {
        Roles = roles;
    }
}

