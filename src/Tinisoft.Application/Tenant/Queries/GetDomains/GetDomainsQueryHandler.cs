using MediatR;
using Microsoft.EntityFrameworkCore;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Interfaces;

namespace Tinisoft.Application.Tenant.Queries.GetDomains;

public class GetDomainsQueryHandler : IRequestHandler<GetDomainsQuery, GetDomainsResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;

    public GetDomainsQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
    }

    public async Task<GetDomainsResponse> Handle(GetDomainsQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var domains = await _dbContext.Domains
            .Where(d => d.TenantId == tenantId)
            .OrderByDescending(d => d.IsPrimary)
            .ThenByDescending(d => d.CreatedAt)
            .Select(d => new DomainDto
            {
                Id = d.Id,
                Host = d.Host,
                IsPrimary = d.IsPrimary,
                IsVerified = d.IsVerified,
                Status = d.IsVerified ? "active" : "pending_verification",
                SslEnabled = d.SslEnabled,
                SslExpiresAt = d.SslExpiresAt,
                CreatedAt = d.CreatedAt,
                VerifiedAt = d.VerifiedAt
            })
            .ToListAsync(cancellationToken);

        return new GetDomainsResponse { Domains = domains };
    }
}

