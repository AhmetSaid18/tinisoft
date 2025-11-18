using Hangfire;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Tinisoft.Application.ExchangeRates.Services;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;

namespace Tinisoft.Infrastructure.Jobs;

/// <summary>
/// TCMB'den döviz kurlarını çeken Hangfire job
/// </summary>
public class SyncExchangeRatesJob
{
    private readonly ITcmbExchangeService _tcmbService;
    private readonly GlobalDbContext _dbContext;
    private readonly ILogger<SyncExchangeRatesJob> _logger;

    public SyncExchangeRatesJob(
        ITcmbExchangeService tcmbService,
        GlobalDbContext dbContext,
        ILogger<SyncExchangeRatesJob> logger)
    {
        _tcmbService = tcmbService;
        _dbContext = dbContext;
        _logger = logger;
    }

    [AutomaticRetry(Attempts = 3, DelaysInSeconds = new[] { 60, 300, 900 })]
    public async Task ExecuteAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            _logger.LogInformation("Starting exchange rate sync from TCMB");

            var rates = await _tcmbService.GetLatestRatesAsync(cancellationToken);

            if (rates.Count == 0)
            {
                _logger.LogWarning("No exchange rates fetched from TCMB");
                return;
            }

            var now = DateTime.UtcNow;
            var exchangeRates = new List<ExchangeRate>();

            foreach (var (currency, rate) in rates)
            {
                // Yeni exchange rate kaydı oluştur
                var exchangeRate = new ExchangeRate
                {
                    BaseCurrency = "TRY",
                    TargetCurrency = currency,
                    Rate = rate,
                    Provider = "TCMB",
                    IsManual = false,
                    FetchedAt = now
                };

                exchangeRates.Add(exchangeRate);
            }

            // DB'ye kaydet
            await _dbContext.ExchangeRates.AddRangeAsync(exchangeRates, cancellationToken);
            await _dbContext.SaveChangesAsync(cancellationToken);

            _logger.LogInformation(
                "Successfully synced {Count} exchange rates from TCMB",
                exchangeRates.Count);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error syncing exchange rates from TCMB");
            throw; // Hangfire retry için
        }
    }
}

