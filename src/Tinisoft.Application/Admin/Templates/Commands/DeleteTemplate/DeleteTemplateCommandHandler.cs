using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Admin.Templates.Commands.DeleteTemplate;

public class DeleteTemplateCommandHandler : IRequestHandler<DeleteTemplateCommand, DeleteTemplateResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly ILogger<DeleteTemplateCommandHandler> _logger;

    public DeleteTemplateCommandHandler(
        IApplicationDbContext dbContext,
        ILogger<DeleteTemplateCommandHandler> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task<DeleteTemplateResponse> Handle(DeleteTemplateCommand request, CancellationToken cancellationToken)
    {
        var template = await _dbContext.Set<Template>()
            .FirstOrDefaultAsync(t => t.Id == request.TemplateId, cancellationToken);

        if (template == null)
        {
            throw new NotFoundException("Template", request.TemplateId);
        }

        // Bu template'i kullanan tenant var mı kontrol et
        var tenantCount = await _dbContext.Set<Entities.Tenant>()
            .CountAsync(t => t.SelectedTemplateCode == template.Code && t.SelectedTemplateVersion == template.Version, cancellationToken);

        if (tenantCount > 0)
        {
            throw new BadRequestException($"Bu template {tenantCount} tenant tarafından kullanılıyor. Önce template'i pasif yapın veya tenant'ları başka template'e geçirin.");
        }

        _dbContext.Set<Template>().Remove(template);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Template deleted: Id={TemplateId}, Code={Code}", template.Id, template.Code);

        return new DeleteTemplateResponse
        {
            TemplateId = request.TemplateId,
            Message = "Template başarıyla silindi."
        };
    }
}



