using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Templates.Commands.SelectTemplate;

public class SelectTemplateCommandHandler : IRequestHandler<SelectTemplateCommand, SelectTemplateResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<SelectTemplateCommandHandler> _logger;

    public SelectTemplateCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<SelectTemplateCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<SelectTemplateResponse> Handle(SelectTemplateCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var tenant = await _dbContext.Set<Entities.Tenant>()
            .FirstOrDefaultAsync(t => t.Id == tenantId, cancellationToken);

        if (tenant == null)
        {
            throw new NotFoundException("Tenant", tenantId);
        }

        // Template zaten seçilmişse hata ver
        if (!string.IsNullOrWhiteSpace(tenant.SelectedTemplateCode))
        {
            throw new BadRequestException("Template zaten seçilmiş. Template değiştirilemez.");
        }

        // Template'i kontrol et
        var templateQuery = _dbContext.Set<Template>()
            .Where(t => t.Code == request.TemplateCode && t.IsActive);

        if (request.TemplateVersion.HasValue)
        {
            templateQuery = templateQuery.Where(t => t.Version == request.TemplateVersion.Value);
        }
        else
        {
            // En son versiyonu al
            templateQuery = templateQuery.OrderByDescending(t => t.Version);
        }

        var template = await templateQuery.FirstOrDefaultAsync(cancellationToken);

        if (template == null)
        {
            throw new NotFoundException("Template", request.TemplateCode);
        }

        // Template'i seç
        tenant.SelectedTemplateCode = template.Code;
        tenant.SelectedTemplateVersion = template.Version;
        tenant.TemplateSelectedAt = DateTime.UtcNow;
        tenant.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Template selected: TenantId={TenantId}, TemplateCode={TemplateCode}, Version={Version}",
            tenantId, template.Code, template.Version);

        // Background job'lar (CreateDefaultCategoriesJob, CreateSampleProductsJob, etc.) 
        // ileride Hangfire ile eklenecek. Şimdilik template seçimi tamamlandı olarak işaretleniyor.
        var setupStarted = true;

        return new SelectTemplateResponse
        {
            TenantId = tenant.Id,
            TemplateCode = template.Code,
            TemplateVersion = template.Version,
            Message = "Template başarıyla seçildi. Site hazırlanıyor...",
            SetupStarted = setupStarted
        };
    }
}



