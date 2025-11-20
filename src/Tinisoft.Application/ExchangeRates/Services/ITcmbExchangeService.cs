namespace Tinisoft.Application.ExchangeRates.Services;

/// <summary>
/// TCMB (Türkiye Cumhuriyet Merkez Bankası) döviz kuru servisi
/// </summary>
public interface ITcmbExchangeService
{
    /// <summary>
    /// TCMB'den güncel döviz kurlarını çeker
    /// </summary>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Currency code -> Rate dictionary (TRY base)</returns>
    Task<Dictionary<string, decimal>> GetLatestRatesAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Belirli bir para birimi için kur getirir
    /// </summary>
    Task<decimal?> GetRateAsync(string targetCurrency, CancellationToken cancellationToken = default);
}



