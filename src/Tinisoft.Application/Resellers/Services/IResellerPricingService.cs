namespace Tinisoft.Application.Resellers.Services;

/// <summary>
/// Reseller pricing service - Bayi fiyatlarını hesaplar
/// </summary>
public interface IResellerPricingService
{
    /// <summary>
    /// Ürün için reseller fiyatını getirir
    /// </summary>
    Task<decimal?> GetResellerPriceAsync(Guid resellerId, Guid productId, int quantity = 1, CancellationToken cancellationToken = default);

    /// <summary>
    /// Ürün için efektif fiyatı getirir (reseller varsa reseller fiyatı, yoksa normal fiyat)
    /// </summary>
    Task<decimal> GetEffectivePriceAsync(Guid? resellerId, Guid productId, int quantity = 1, CancellationToken cancellationToken = default);
}



