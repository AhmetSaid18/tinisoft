using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Payments.Queries.GetPaymentProviders;

public class GetPaymentProvidersQueryHandler : IRequestHandler<GetPaymentProvidersQuery, GetPaymentProvidersResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetPaymentProvidersQueryHandler> _logger;

    public GetPaymentProvidersQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetPaymentProvidersQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetPaymentProvidersResponse> Handle(GetPaymentProvidersQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var query = _dbContext.Set<Domain.Entities.PaymentProvider>()
            .AsNoTracking()
            .Where(pp => pp.TenantId == tenantId);

        if (request.IsActive.HasValue)
        {
            query = query.Where(pp => pp.IsActive == request.IsActive.Value);
        }

        var providers = await query
            .OrderBy(pp => pp.Priority)
            .ThenBy(pp => pp.ProviderName)
            .Select(pp => new PaymentProviderDto
            {
                Id = pp.Id,
                ProviderCode = pp.ProviderCode,
                ProviderName = pp.ProviderName,
                IsActive = pp.IsActive,
                IsDefault = pp.IsDefault,
                Priority = pp.Priority,
                UseTestMode = pp.UseTestMode,
                HasApiKey = !string.IsNullOrEmpty(pp.ApiKey)
            })
            .ToListAsync(cancellationToken);

        return new GetPaymentProvidersResponse
        {
            Providers = providers
        };
    }
}

