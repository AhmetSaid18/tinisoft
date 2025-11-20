namespace Tinisoft.Application.Shipping.Services;

/// <summary>
/// Kargo firması servis factory'si (Provider pattern)
/// </summary>
public interface IShippingServiceFactory
{
    IShippingService GetService(string providerCode);
    bool IsProviderSupported(string providerCode);
}



