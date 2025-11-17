using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Tenant.Commands.UpdateLayoutSettings;

public class UpdateLayoutSettingsCommandHandler : IRequestHandler<UpdateLayoutSettingsCommand, UpdateLayoutSettingsResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<UpdateLayoutSettingsCommandHandler> _logger;

    public UpdateLayoutSettingsCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<UpdateLayoutSettingsCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<UpdateLayoutSettingsResponse> Handle(UpdateLayoutSettingsCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var tenant = await _dbContext.Set<Tenant>()
            .FirstOrDefaultAsync(t => t.Id == tenantId, cancellationToken);

        if (tenant == null)
        {
            throw new NotFoundException("Tenant", tenantId);
        }

        // Layout settings'i JSON olarak kaydet
        tenant.LayoutSettingsJson = System.Text.Json.JsonSerializer.Serialize(request.LayoutSettings);
        tenant.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Layout settings updated for tenant: {TenantId}", tenantId);

        return new UpdateLayoutSettingsResponse
        {
            TenantId = tenant.Id,
            LayoutSettings = request.LayoutSettings,
            Message = "Layout ayarları başarıyla güncellendi."
        };
    }
}

