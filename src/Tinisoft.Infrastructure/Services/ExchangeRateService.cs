using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Distributed;
using Microsoft.Extensions.Logging;
using System.Text.Json;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.ExchangeRates.Services;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;

namespace Tinisoft.Infrastructure.Services;

/// <summary>
/// Exchange rate service - Cache ve DB'den kur getirir
/// </summary>
public class ExchangeRateService : IExchangeRateService
{
    private readonly GlobalDbContext _dbContext;
    private readonly ICacheService _cacheService;
    private readonly ILogger<ExchangeRateService> _logger;
    private const string CACHE_KEY_PREFIX = "exchange:";

    public ExchangeRateService(
        GlobalDbContext dbContext,
        ICacheService cacheService,
        ILogger<ExchangeRateService> logger)
    {
        _dbContext = dbContext;
        _cacheService = cacheService;
        _logger = logger;
    }

    public async Task<decimal?> GetRateAsync(string targetCurrency, CancellationToken cancellationToken = default)
    {
        var currency = targetCurrency.ToUpper();
        
        // Önce cache'den bak
        var cacheKey = $"{CACHE_KEY_PREFIX}{currency}";
        var cachedRate = await _cacheService.GetAsync<decimal?>(cacheKey, cancellationToken);
        if (cachedRate.HasValue)
        {
            _logger.LogDebug("Exchange rate found in cache: {Currency} = {Rate}", currency, cachedRate.Value);
            return cachedRate.Value;
        }

        // Cache'de yoksa DB'den en son kur'u getir
        var exchangeRate = await _dbContext.ExchangeRates
            .Where(er => er.TargetCurrency == currency && er.BaseCurrency == "TRY")
            .OrderByDescending(er => er.FetchedAt)
            .FirstOrDefaultAsync(cancellationToken);

        if (exchangeRate == null)
        {
            _logger.LogWarning("Exchange rate not found for currency: {Currency}", currency);
            return null;
        }

        // Cache'e yaz (1 saat geçerli)
        await _cacheService.SetAsync(cacheKey, exchangeRate.Rate, TimeSpan.FromHours(1), cancellationToken);

        _logger.LogDebug("Exchange rate fetched from DB: {Currency} = {Rate}", currency, exchangeRate.Rate);
        return exchangeRate.Rate;
    }

    public async Task<decimal?> GetEffectiveRateAsync(string targetCurrency, decimal marginPercent = 0, CancellationToken cancellationToken = default)
    {
        var baseRate = await GetRateAsync(targetCurrency, cancellationToken);
        if (!baseRate.HasValue)
            return null;

        // Margin ekle: effectiveRate = baseRate * (1 + marginPercent / 100)
        var effectiveRate = baseRate.Value * (1 + marginPercent / 100);
        return Math.Round(effectiveRate, 4, MidpointRounding.AwayFromZero);
    }
}

