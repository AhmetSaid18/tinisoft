using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Tenant.Queries.GetLayoutSettings;

public class GetLayoutSettingsQueryHandler : IRequestHandler<GetLayoutSettingsQuery, GetLayoutSettingsResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetLayoutSettingsQueryHandler> _logger;

    public GetLayoutSettingsQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetLayoutSettingsQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetLayoutSettingsResponse> Handle(GetLayoutSettingsQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var tenant = await _dbContext.Set<Entities.Tenant>()
            .FirstOrDefaultAsync(t => t.Id == tenantId, cancellationToken);

        if (tenant == null)
        {
            throw new NotFoundException("Tenant", tenantId);
        }

        // Layout settings JSON'ı parse et
        Dictionary<string, object>? layoutSettings = null;
        if (!string.IsNullOrWhiteSpace(tenant.LayoutSettingsJson))
        {
            try
            {
                layoutSettings = System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, object>>(tenant.LayoutSettingsJson);
            }
            catch
            {
                // JSON parse hatası durumunda null bırak
            }
        }

        return new GetLayoutSettingsResponse
        {
            TenantId = tenant.Id,
            LayoutSettings = layoutSettings
        };
    }
}



