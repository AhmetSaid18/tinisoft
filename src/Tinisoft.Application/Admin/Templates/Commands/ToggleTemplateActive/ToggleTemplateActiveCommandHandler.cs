using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Admin.Templates.Commands.ToggleTemplateActive;

public class ToggleTemplateActiveCommandHandler : IRequestHandler<ToggleTemplateActiveCommand, ToggleTemplateActiveResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ILogger<ToggleTemplateActiveCommandHandler> _logger;

    public ToggleTemplateActiveCommandHandler(
        ApplicationDbContext dbContext,
        ILogger<ToggleTemplateActiveCommandHandler> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task<ToggleTemplateActiveResponse> Handle(ToggleTemplateActiveCommand request, CancellationToken cancellationToken)
    {
        var template = await _dbContext.Set<Template>()
            .FirstOrDefaultAsync(t => t.Id == request.TemplateId, cancellationToken);

        if (template == null)
        {
            throw new NotFoundException("Template", request.TemplateId);
        }

        template.IsActive = request.IsActive;
        template.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Template active status changed: Id={TemplateId}, Code={Code}, IsActive={IsActive}",
            template.Id, template.Code, request.IsActive);

        return new ToggleTemplateActiveResponse
        {
            TemplateId = template.Id,
            IsActive = template.IsActive,
            Message = request.IsActive ? "Template aktif edildi." : "Template pasif edildi."
        };
    }
}

