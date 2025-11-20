using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Tinisoft.Application.Resellers.Services;
using Microsoft.Extensions.Logging;
using Tinisoft.Infrastructure.Persistence;

using Microsoft.Extensions.Logging;
namespace Tinisoft.Infrastructure.Services;

public class ResellerPricingService : IResellerPricingService
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ILogger<ResellerPricingService> _logger;

    public ResellerPricingService(
        ApplicationDbContext dbContext,
        ILogger<ResellerPricingService> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task<decimal?> GetResellerPriceAsync(Guid resellerId, Guid productId, int quantity = 1, CancellationToken cancellationToken = default)
    {
        // Reseller kontrolü
        var reseller = await _dbContext.Resellers
            .FirstOrDefaultAsync(r => r.Id == resellerId && r.IsActive, cancellationToken);

        if (reseller == null || !reseller.IsActive)
        {
            return null;
        }

        // Özel fiyat var mı kontrol et (quantity break pricing ile)
        var resellerPrice = await _dbContext.ResellerPrices
            .Where(rp => 
                rp.ResellerId == resellerId &&
                rp.ProductId == productId &&
                rp.IsActive &&
                (rp.ValidFrom == null || rp.ValidFrom <= DateTime.UtcNow) &&
                (rp.ValidUntil == null || rp.ValidUntil >= DateTime.UtcNow) &&
                (rp.MinQuantity == null || rp.MinQuantity <= quantity) &&
                (rp.MaxQuantity == null || rp.MaxQuantity >= quantity))
            .OrderByDescending(rp => rp.MinQuantity) // En yüksek min quantity'li olanı al (quantity break için)
            .FirstOrDefaultAsync(cancellationToken);

        if (resellerPrice != null)
        {
            return resellerPrice.Price;
        }

        // Özel fiyat yoksa, default discount uygula
        var product = await _dbContext.Products
            .FirstOrDefaultAsync(p => p.Id == productId, cancellationToken);

        if (product == null)
        {
            return null;
        }

        if (reseller.DefaultDiscountPercent > 0)
        {
            var discountedPrice = product.Price * (1 - reseller.DefaultDiscountPercent / 100);
            return Math.Round(discountedPrice, 2, MidpointRounding.AwayFromZero);
        }

        return null; // Reseller fiyatı yok
    }

    public async Task<decimal> GetEffectivePriceAsync(Guid? resellerId, Guid productId, int quantity = 1, CancellationToken cancellationToken = default)
    {
        // Reseller varsa reseller fiyatını getir
        if (resellerId.HasValue)
        {
            var resellerPrice = await GetResellerPriceAsync(resellerId.Value, productId, quantity);
            if (resellerPrice.HasValue)
            {
                return resellerPrice.Value;
            }
        }

        // Reseller fiyatı yoksa normal fiyatı getir
        var product = await _dbContext.Products
            .FirstOrDefaultAsync(p => p.Id == productId);

        return product?.Price ?? 0;
    }
}

