using Microsoft.Extensions.DependencyInjection;

namespace Tinisoft.Application.Marketplace.Services;

public class MarketplaceServiceFactory : IMarketplaceServiceFactory
{
    private readonly IServiceProvider _serviceProvider;

    public MarketplaceServiceFactory(IServiceProvider serviceProvider)
    {
        _serviceProvider = serviceProvider;
    }

    public IMarketplaceService GetService(string marketplace)
    {
        return marketplace.ToLower() switch
        {
            "trendyol" => _serviceProvider.GetRequiredService<TrendyolMarketplaceService>(),
            "hepsiburada" => _serviceProvider.GetRequiredService<HepsiburadaMarketplaceService>(),
            "n11" => _serviceProvider.GetRequiredService<N11MarketplaceService>(),
            _ => throw new NotSupportedException($"Marketplace desteklenmiyor: {marketplace}")
        };
    }
}

