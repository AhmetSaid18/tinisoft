namespace Tinisoft.Application.ExchangeRates.Services;

/// <summary>
/// Exchange rate service - Cache'den veya DB'den kur getirir
/// </summary>
public interface IExchangeRateService
{
    /// <summary>
    /// Belirli bir para birimi için güncel kur getirir (cache'den veya DB'den)
    /// </summary>
    Task<decimal?> GetRateAsync(string targetCurrency, CancellationToken cancellationToken = default);

    /// <summary>
    /// Effective rate getirir (kur + margin)
    /// </summary>
    Task<decimal?> GetEffectiveRateAsync(string targetCurrency, decimal marginPercent = 0, CancellationToken cancellationToken = default);
}

