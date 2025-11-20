using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Admin.Templates.Commands.CreateTemplate;

public class CreateTemplateCommandHandler : IRequestHandler<CreateTemplateCommand, CreateTemplateResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly ILogger<CreateTemplateCommandHandler> _logger;

    public CreateTemplateCommandHandler(
        IApplicationDbContext dbContext,
        ILogger<CreateTemplateCommandHandler> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task<CreateTemplateResponse> Handle(CreateTemplateCommand request, CancellationToken cancellationToken)
    {
        // Aynı code ve version zaten var mı kontrol et
        var existing = await _dbContext.Set<Template>()
            .FirstOrDefaultAsync(t => t.Code == request.Code && t.Version == request.Version, cancellationToken);

        if (existing != null)
        {
            throw new BadRequestException($"Template '{request.Code}' versiyon {request.Version} zaten mevcut.");
        }

        var template = new Template
        {
            Code = request.Code,
            Name = request.Name,
            Description = request.Description,
            Version = request.Version,
            PreviewImageUrl = request.PreviewImageUrl,
            IsActive = request.IsActive
        };

        if (request.Metadata != null)
        {
            template.MetadataJson = System.Text.Json.JsonSerializer.Serialize(request.Metadata);
        }

        _dbContext.Set<Template>().Add(template);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Template created: Code={Code}, Version={Version}", request.Code, request.Version);

        return new CreateTemplateResponse
        {
            TemplateId = template.Id,
            Code = template.Code,
            Name = template.Name,
            Message = "Template başarıyla oluşturuldu."
        };
    }
}



