namespace Tinisoft.Application.Payments.Services;

/// <summary>
/// Ödeme sağlayıcı servis factory'si (Provider pattern)
/// </summary>
public interface IPaymentServiceFactory
{
    IPaymentService GetService(string providerCode);
    bool IsProviderSupported(string providerCode);
}

