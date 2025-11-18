using Tinisoft.Application.Shipping.Services;

namespace Tinisoft.Infrastructure.Services;

public class ShippingServiceFactory : IShippingServiceFactory
{
    private readonly Dictionary<string, IShippingService> _services;
    private readonly ILogger<ShippingServiceFactory> _logger;

    public ShippingServiceFactory(
        ArasShippingService arasService,
        MngShippingService mngService,
        YurticiShippingService yurticiService,
        ILogger<ShippingServiceFactory> logger)
    {
        _logger = logger;
        _services = new Dictionary<string, IShippingService>
        {
            { "ARAS", arasService },
            { "MNG", mngService },
            { "YURTICI", yurticiService }
        };
    }

    public IShippingService GetService(string providerCode)
    {
        var normalizedCode = providerCode.ToUpper();
        
        if (!_services.TryGetValue(normalizedCode, out var service))
        {
            throw new NotSupportedException($"Shipping provider not supported: {providerCode}");
        }

        return service;
    }

    public bool IsProviderSupported(string providerCode)
    {
        var normalizedCode = providerCode.ToUpper();
        return _services.ContainsKey(normalizedCode);
    }
}

