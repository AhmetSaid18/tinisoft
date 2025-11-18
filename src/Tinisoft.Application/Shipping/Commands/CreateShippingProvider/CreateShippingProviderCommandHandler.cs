using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Shipping.Commands.CreateShippingProvider;

public class CreateShippingProviderCommandHandler : IRequestHandler<CreateShippingProviderCommand, CreateShippingProviderResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CreateShippingProviderCommandHandler> _logger;

    public CreateShippingProviderCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CreateShippingProviderCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CreateShippingProviderResponse> Handle(CreateShippingProviderCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Aynı provider code'un daha önce eklenip eklenmediğini kontrol et
        var existingProvider = await _dbContext.ShippingProviders
            .FirstOrDefaultAsync(sp => 
                sp.TenantId == tenantId && 
                sp.ProviderCode == request.ProviderCode, cancellationToken);

        if (existingProvider != null)
        {
            throw new InvalidOperationException($"Bu kargo firması zaten eklenmiş: {request.ProviderCode}");
        }

        // Eğer default olarak işaretleniyorsa, diğer provider'ları default'tan çıkar
        if (request.IsDefault)
        {
            var defaultProviders = await _dbContext.ShippingProviders
                .Where(sp => sp.TenantId == tenantId && sp.IsDefault)
                .ToListAsync(cancellationToken);

            foreach (var provider in defaultProviders)
            {
                provider.IsDefault = false;
            }
        }

        var shippingProvider = new Domain.Entities.ShippingProvider
        {
            TenantId = tenantId,
            ProviderCode = request.ProviderCode.ToUpper(),
            ProviderName = request.ProviderName,
            ApiKey = request.ApiKey,
            ApiSecret = request.ApiSecret,
            ApiUrl = request.ApiUrl,
            TestApiUrl = request.TestApiUrl,
            UseTestMode = request.UseTestMode,
            SettingsJson = request.SettingsJson,
            IsDefault = request.IsDefault,
            Priority = request.Priority,
            IsActive = true
        };

        _dbContext.ShippingProviders.Add(shippingProvider);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Shipping provider created: {ProviderCode} for tenant {TenantId}", 
            request.ProviderCode, tenantId);

        return new CreateShippingProviderResponse
        {
            ShippingProviderId = shippingProvider.Id,
            ProviderCode = shippingProvider.ProviderCode,
            ProviderName = shippingProvider.ProviderName
        };
    }
}

