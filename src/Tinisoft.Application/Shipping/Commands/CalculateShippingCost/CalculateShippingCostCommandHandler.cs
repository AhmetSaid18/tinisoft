using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Shipping.Services;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Shipping.Commands.CalculateShippingCost;

public class CalculateShippingCostCommandHandler : IRequestHandler<CalculateShippingCostCommand, CalculateShippingCostResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IShippingServiceFactory _shippingServiceFactory;
    private readonly ILogger<CalculateShippingCostCommandHandler> _logger;

    public CalculateShippingCostCommandHandler(
        ApplicationDbContext dbContext,
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

        string providerCode;
        string providerName;

        if (request.ShippingProviderId.HasValue)
        {
            var provider = await _dbContext.ShippingProviders
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

            providerCode = provider.ProviderCode;
            providerName = provider.ProviderName;
        }
        else if (!string.IsNullOrEmpty(request.ProviderCode))
        {
            providerCode = request.ProviderCode.ToUpper();
            
            var provider = await _dbContext.ShippingProviders
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

            providerName = provider.ProviderName;
        }
        else
        {
            // Varsayılan provider'ı kullan
            var defaultProvider = await _dbContext.ShippingProviders
                .AsNoTracking()
                .FirstOrDefaultAsync(sp => 
                    sp.TenantId == tenantId && 
                    sp.IsActive && 
                    sp.IsDefault, cancellationToken);

            if (defaultProvider == null)
            {
                return new CalculateShippingCostResponse
                {
                    Success = false,
                    ErrorMessage = "Varsayılan kargo firması bulunamadı"
                };
            }

            providerCode = defaultProvider.ProviderCode;
            providerName = defaultProvider.ProviderName;
        }

        if (!_shippingServiceFactory.IsProviderSupported(providerCode))
        {
            return new CalculateShippingCostResponse
            {
                Success = false,
                ErrorMessage = $"Kargo firması desteklenmiyor: {providerCode}"
            };
        }

        try
        {
            var shippingService = _shippingServiceFactory.GetService(providerCode);
            var cost = await shippingService.CalculateShippingCostAsync(
                providerCode,
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
                ProviderCode = providerCode,
                ProviderName = providerName,
                Success = true
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calculating shipping cost for provider {ProviderCode}", providerCode);
            return new CalculateShippingCostResponse
            {
                Success = false,
                ErrorMessage = $"Kargo ücreti hesaplanırken hata oluştu: {ex.Message}"
            };
        }
    }
}

