using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;

namespace Tinisoft.Application.Admin.Templates.Queries.GetAllTemplates;

public class GetAllTemplatesQueryHandler : IRequestHandler<GetAllTemplatesQuery, GetAllTemplatesResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ILogger<GetAllTemplatesQueryHandler> _logger;

    public GetAllTemplatesQueryHandler(
        ApplicationDbContext dbContext,
        ILogger<GetAllTemplatesQueryHandler> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task<GetAllTemplatesResponse> Handle(GetAllTemplatesQuery request, CancellationToken cancellationToken)
    {
        var templates = await _dbContext.Set<Template>()
            .Select(t => new TemplateDto
            {
                Id = t.Id,
                Code = t.Code,
                Name = t.Name,
                Description = t.Description,
                Version = t.Version,
                PreviewImageUrl = t.PreviewImageUrl,
                IsActive = t.IsActive,
                CreatedAt = t.CreatedAt,
                UpdatedAt = t.UpdatedAt,
                TenantCount = _dbContext.Set<Tenant>()
                    .Count(tenant => tenant.SelectedTemplateCode == t.Code && tenant.SelectedTemplateVersion == t.Version)
            })
            .OrderBy(t => t.Code)
            .ThenByDescending(t => t.Version)
            .ToListAsync(cancellationToken);

        return new GetAllTemplatesResponse
        {
            Templates = templates
        };
    }
}

