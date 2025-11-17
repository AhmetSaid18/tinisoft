using Finbuckle.MultiTenant;

namespace Tinisoft.Infrastructure.MultiTenant;

public class TenantInfo : ITenantInfo
{
    public string Id { get; set; } = string.Empty;
    public string Identifier { get; set; } = string.Empty; // Host veya slug
    public string Name { get; set; } = string.Empty;
    public string ConnectionString { get; set; } = string.Empty;
    public Dictionary<string, object> Items { get; set; } = new();
}

