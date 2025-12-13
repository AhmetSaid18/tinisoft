using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Shipping.Services;
using Tinisoft.Application.Common.Exceptions;
using System.Text.Json;

namespace Tinisoft.Application.Shipping.Commands.CalculateShippingCost;

public class CalculateShippingCostCommandHandler : IRequestHandler<CalculateShippingCostCommand, CalculateShippingCostResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IShippingServiceFactory _shippingServiceFactory;
    private readonly ILogger<CalculateShippingCostCommandHandler> _logger;

    public CalculateShippingCostCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IShippingServiceFactory shippingServiceFactory,
        ILogger<CalculateShippingCostCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _shippingServiceFactory = shippingServiceFactory;
        _logger = logger;
    }

    public async Task<CalculateShippingCostResponse> Handle(CalculateShippingCostCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        Domain.Entities.ShippingProvider? provider = null;

        if (request.ShippingProviderId.HasValue)
        {
            provider = await _dbContext.ShippingProviders
                .AsNoTracking()
                .FirstOrDefaultAsync(sp => 
                    sp.Id == request.ShippingProviderId.Value && 
                    sp.TenantId == tenantId && 
                    sp.IsActive, cancellationToken);

            if (provider == null)
            {
                throw new NotFoundException("ShippingProvider", request.ShippingProviderId.Value);
            }

            if (string.IsNullOrEmpty(provider.ApiKey))
            {
                return new CalculateShippingCostResponse
                {
                    Success = false,
                    ErrorMessage = "Kargo firması için API key tanımlanmamış"
                };
            }
        }
        else if (!string.IsNullOrEmpty(request.ProviderCode))
        {
            var providerCode = request.ProviderCode.ToUpper();
            
            provider = await _dbContext.ShippingProviders
                .AsNoTracking()
                .FirstOrDefaultAsync(sp => 
                    sp.ProviderCode == providerCode && 
                    sp.TenantId == tenantId && 
                    sp.IsActive, cancellationToken);

            if (provider == null)
            {
                return new CalculateShippingCostResponse
                {
                    Success = false,
                    ErrorMessage = $"Kargo firması bulunamadı: {providerCode}"
                };
            }
        }
        else
        {
            // Varsayılan provider'ı kullan
            provider = await _dbContext.ShippingProviders
                .AsNoTracking()
                .FirstOrDefaultAsync(sp => 
                    sp.TenantId == tenantId && 
                    sp.IsActive && 
                    sp.IsDefault, cancellationToken);

            if (provider == null)
            {
                return new CalculateShippingCostResponse
                {
                    Success = false,
                    ErrorMessage = "Varsayılan kargo firması bulunamadı"
                };
            }
        }

        if (string.IsNullOrEmpty(provider.ApiKey))
        {
            return new CalculateShippingCostResponse
            {
                Success = false,
                ErrorMessage = "Kargo firması için API key tanımlanmamış"
            };
        }

        if (!_shippingServiceFactory.IsProviderSupported(provider.ProviderCode))
        {
            return new CalculateShippingCostResponse
            {
                Success = false,
                ErrorMessage = $"Kargo firması desteklenmiyor: {provider.ProviderCode}"
            };
        }

        // Tenant'ın provider bilgilerini credentials olarak hazırla
        var credentials = new ShippingProviderCredentials
        {
            ApiKey = provider.ApiKey,
            ApiSecret = provider.ApiSecret,
            ApiUrl = provider.UseTestMode ? provider.TestApiUrl : provider.ApiUrl,
            TestApiUrl = provider.TestApiUrl,
            UseTestMode = provider.UseTestMode,
            SettingsJson = provider.SettingsJson
        };

        try
        {
            var shippingService = _shippingServiceFactory.GetService(provider.ProviderCode);
            var cost = await shippingService.CalculateShippingCostAsync(
                provider.ProviderCode,
                credentials, // Tenant'ın API key'leri
                request.FromCity,
                request.ToCity,
                request.Weight,
                request.Width,
                request.Height,
                request.Depth,
                cancellationToken);

            return new CalculateShippingCostResponse
            {
                ShippingCost = cost,
                Currency = "TRY",
                ProviderCode = provider.ProviderCode,
                ProviderName = provider.ProviderName,
                Success = true
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calculating shipping cost for provider {ProviderCode}", provider.ProviderCode);
            return new CalculateShippingCostResponse
            {
                Success = false,
                ErrorMessage = $"Kargo ücreti hesaplanırken hata oluştu: {ex.Message}"
            };
        }
    }
}



