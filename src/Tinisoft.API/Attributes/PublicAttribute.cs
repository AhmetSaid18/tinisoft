namespace Tinisoft.API.Attributes;

/// <summary>
/// Bu attribute ile işaretlenen endpoint'ler authentication gerektirmez (public)
/// </summary>
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class)]
public class PublicAttribute : Attribute
{
}

