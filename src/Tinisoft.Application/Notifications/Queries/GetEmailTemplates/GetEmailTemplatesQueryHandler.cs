using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Notifications.Queries.GetEmailTemplates;

public class GetEmailTemplatesQueryHandler : IRequestHandler<GetEmailTemplatesQuery, GetEmailTemplatesResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetEmailTemplatesQueryHandler> _logger;

    public GetEmailTemplatesQueryHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetEmailTemplatesQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetEmailTemplatesResponse> Handle(GetEmailTemplatesQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var query = _dbContext.EmailTemplates
            .AsNoTracking()
            .Where(et => et.TenantId == tenantId);

        if (request.IsActive.HasValue)
        {
            query = query.Where(et => et.IsActive == request.IsActive.Value);
        }

        var templates = await query
            .OrderBy(et => et.TemplateName)
            .Select(et => new EmailTemplateDto
            {
                Id = et.Id,
                TemplateCode = et.TemplateCode,
                TemplateName = et.TemplateName,
                Subject = et.Subject,
                IsActive = et.IsActive
            })
            .ToListAsync(cancellationToken);

        return new GetEmailTemplatesResponse
        {
            Templates = templates
        };
    }
}

