using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Notifications.Commands.CreateEmailTemplate;

public class CreateEmailTemplateCommandHandler : IRequestHandler<CreateEmailTemplateCommand, CreateEmailTemplateResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CreateEmailTemplateCommandHandler> _logger;

    public CreateEmailTemplateCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CreateEmailTemplateCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CreateEmailTemplateResponse> Handle(CreateEmailTemplateCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Aynı template code'un daha önce eklenip eklenmediğini kontrol et
        var existingTemplate = await _dbContext.EmailTemplates
            .FirstOrDefaultAsync(et => 
                et.TenantId == tenantId && 
                et.TemplateCode == request.TemplateCode.ToUpper(), cancellationToken);

        if (existingTemplate != null)
        {
            throw new InvalidOperationException($"Bu email şablonu zaten mevcut: {request.TemplateCode}");
        }

        var emailTemplate = new Domain.Entities.EmailTemplate
        {
            TenantId = tenantId,
            TemplateCode = request.TemplateCode.ToUpper(),
            TemplateName = request.TemplateName,
            Subject = request.Subject,
            BodyHtml = request.BodyHtml,
            BodyText = request.BodyText,
            IsActive = true
        };

        _dbContext.EmailTemplates.Add(emailTemplate);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Email template created: {TemplateCode} for tenant {TenantId}", 
            request.TemplateCode, tenantId);

        return new CreateEmailTemplateResponse
        {
            EmailTemplateId = emailTemplate.Id,
            TemplateCode = emailTemplate.TemplateCode,
            TemplateName = emailTemplate.TemplateName
        };
    }
}



