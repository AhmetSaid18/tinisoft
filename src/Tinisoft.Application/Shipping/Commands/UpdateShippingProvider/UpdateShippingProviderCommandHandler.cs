using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Shipping.Commands.UpdateShippingProvider;

public class UpdateShippingProviderCommandHandler : IRequestHandler<UpdateShippingProviderCommand, UpdateShippingProviderResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<UpdateShippingProviderCommandHandler> _logger;

    public UpdateShippingProviderCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<UpdateShippingProviderCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<UpdateShippingProviderResponse> Handle(UpdateShippingProviderCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var provider = await _dbContext.ShippingProviders
            .FirstOrDefaultAsync(sp => 
                sp.Id == request.ShippingProviderId && 
                sp.TenantId == tenantId, cancellationToken);

        if (provider == null)
        {
            throw new NotFoundException("ShippingProvider", request.ShippingProviderId);
        }

        // Eğer default olarak işaretleniyorsa, diğer provider'ları default'tan çıkar
        if (request.IsDefault == true && !provider.IsDefault)
        {
            var defaultProviders = await _dbContext.ShippingProviders
                .Where(sp => sp.TenantId == tenantId && sp.IsDefault && sp.Id != request.ShippingProviderId)
                .ToListAsync(cancellationToken);

            foreach (var p in defaultProviders)
            {
                p.IsDefault = false;
            }
        }

        if (request.ProviderName != null)
            provider.ProviderName = request.ProviderName;
        if (request.ApiKey != null)
            provider.ApiKey = request.ApiKey;
        if (request.ApiSecret != null)
            provider.ApiSecret = request.ApiSecret;
        if (request.ApiUrl != null)
            provider.ApiUrl = request.ApiUrl;
        if (request.TestApiUrl != null)
            provider.TestApiUrl = request.TestApiUrl;
        if (request.UseTestMode.HasValue)
            provider.UseTestMode = request.UseTestMode.Value;
        if (request.SettingsJson != null)
            provider.SettingsJson = request.SettingsJson;
        if (request.IsDefault.HasValue)
            provider.IsDefault = request.IsDefault.Value;
        if (request.Priority.HasValue)
            provider.Priority = request.Priority.Value;
        if (request.IsActive.HasValue)
            provider.IsActive = request.IsActive.Value;

        provider.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Shipping provider updated: {ProviderCode} for tenant {TenantId}", 
            provider.ProviderCode, tenantId);

        return new UpdateShippingProviderResponse
        {
            ShippingProviderId = provider.Id,
            ProviderCode = provider.ProviderCode,
            ProviderName = provider.ProviderName
        };
    }
}

