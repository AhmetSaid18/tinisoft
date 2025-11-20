using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Templates.Queries.GetSelectedTemplate;

public class GetSelectedTemplateQueryHandler : IRequestHandler<GetSelectedTemplateQuery, GetSelectedTemplateResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetSelectedTemplateQueryHandler> _logger;

    public GetSelectedTemplateQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetSelectedTemplateQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetSelectedTemplateResponse> Handle(GetSelectedTemplateQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var tenant = await _dbContext.Set<Entities.Tenant>()
            .FirstOrDefaultAsync(t => t.Id == tenantId, cancellationToken);

        if (tenant == null)
        {
            throw new NotFoundException("Tenant", tenantId);
        }

        return new GetSelectedTemplateResponse
        {
            TemplateCode = tenant.SelectedTemplateCode,
            TemplateVersion = tenant.SelectedTemplateVersion,
            SelectedAt = tenant.TemplateSelectedAt
        };
    }
}



