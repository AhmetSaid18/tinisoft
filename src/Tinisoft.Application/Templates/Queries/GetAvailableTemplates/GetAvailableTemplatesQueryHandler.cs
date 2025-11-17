using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;

namespace Tinisoft.Application.Templates.Queries.GetAvailableTemplates;

public class GetAvailableTemplatesQueryHandler : IRequestHandler<GetAvailableTemplatesQuery, GetAvailableTemplatesResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ILogger<GetAvailableTemplatesQueryHandler> _logger;

    public GetAvailableTemplatesQueryHandler(
        ApplicationDbContext dbContext,
        ILogger<GetAvailableTemplatesQueryHandler> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task<GetAvailableTemplatesResponse> Handle(GetAvailableTemplatesQuery request, CancellationToken cancellationToken)
    {
        // Sadece aktif template'leri getir, her template code için en son versiyonu al
        var templates = await _dbContext.Set<Template>()
            .Where(t => t.IsActive)
            .GroupBy(t => t.Code)
            .Select(g => g.OrderByDescending(t => t.Version).First())
            .Select(t => new TemplateDto
            {
                Id = t.Id,
                Code = t.Code,
                Name = t.Name,
                Description = t.Description,
                Version = t.Version,
                PreviewImageUrl = t.PreviewImageUrl,
                IsActive = t.IsActive
            })
            .OrderBy(t => t.Name)
            .ToListAsync(cancellationToken);

        return new GetAvailableTemplatesResponse
        {
            Templates = templates
        };
    }
}

