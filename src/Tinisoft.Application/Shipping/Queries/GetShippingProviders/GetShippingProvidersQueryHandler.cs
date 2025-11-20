using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Shipping.Queries.GetShippingProviders;

public class GetShippingProvidersQueryHandler : IRequestHandler<GetShippingProvidersQuery, GetShippingProvidersResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetShippingProvidersQueryHandler> _logger;

    public GetShippingProvidersQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetShippingProvidersQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetShippingProvidersResponse> Handle(GetShippingProvidersQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var query = _dbContext.ShippingProviders
            .AsNoTracking()
            .Where(sp => sp.TenantId == tenantId);

        if (request.IsActive.HasValue)
        {
            query = query.Where(sp => sp.IsActive == request.IsActive.Value);
        }

        var providers = await query
            .OrderBy(sp => sp.Priority)
            .ThenBy(sp => sp.ProviderName)
            .Select(sp => new ShippingProviderDto
            {
                Id = sp.Id,
                ProviderCode = sp.ProviderCode,
                ProviderName = sp.ProviderName,
                IsActive = sp.IsActive,
                IsDefault = sp.IsDefault,
                Priority = sp.Priority,
                UseTestMode = sp.UseTestMode,
                HasApiKey = !string.IsNullOrEmpty(sp.ApiKey)
            })
            .ToListAsync(cancellationToken);

        return new GetShippingProvidersResponse
        {
            Providers = providers
        };
    }
}



