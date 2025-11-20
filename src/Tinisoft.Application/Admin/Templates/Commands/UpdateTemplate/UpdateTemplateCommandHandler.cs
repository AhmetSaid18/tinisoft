using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Admin.Templates.Commands.UpdateTemplate;

public class UpdateTemplateCommandHandler : IRequestHandler<UpdateTemplateCommand, UpdateTemplateResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly ILogger<UpdateTemplateCommandHandler> _logger;

    public UpdateTemplateCommandHandler(
        IApplicationDbContext dbContext,
        ILogger<UpdateTemplateCommandHandler> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task<UpdateTemplateResponse> Handle(UpdateTemplateCommand request, CancellationToken cancellationToken)
    {
        var template = await _dbContext.Set<Template>()
            .FirstOrDefaultAsync(t => t.Id == request.TemplateId, cancellationToken);

        if (template == null)
        {
            throw new NotFoundException("Template", request.TemplateId);
        }

        // Update fields (sadece gönderilenler güncellenir)
        if (request.Name != null) template.Name = request.Name;
        if (request.Description != null) template.Description = request.Description;
        if (request.PreviewImageUrl != null) template.PreviewImageUrl = request.PreviewImageUrl;
        if (request.IsActive.HasValue) template.IsActive = request.IsActive.Value;
        if (request.Metadata != null)
        {
            template.MetadataJson = System.Text.Json.JsonSerializer.Serialize(request.Metadata);
        }

        template.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Template updated: Id={TemplateId}, Code={Code}", template.Id, template.Code);

        return new UpdateTemplateResponse
        {
            TemplateId = template.Id,
            Code = template.Code,
            Message = "Template başarıyla güncellendi."
        };
    }
}



