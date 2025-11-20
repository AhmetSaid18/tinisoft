using MediatR;

namespace Tinisoft.Application.Tenant.Queries.GetLayoutSettings;

public class GetLayoutSettingsQuery : IRequest<GetLayoutSettingsResponse>
{
}

public class GetLayoutSettingsResponse
{
    public Guid TenantId { get; set; }
    public Dictionary<string, object>? LayoutSettings { get; set; }
}



