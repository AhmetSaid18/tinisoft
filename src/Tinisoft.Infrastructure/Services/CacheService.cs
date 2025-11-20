using Microsoft.Extensions.Caching.Distributed;
using System.Text.Json;
using Tinisoft.Application.Common.Interfaces;
using Microsoft.Extensions.Logging;

namespace Tinisoft.Infrastructure.Services;

public class CacheService : ICacheService
{
    private readonly IDistributedCache _cache;
    private readonly ILogger<CacheService> _logger;

    public CacheService(IDistributedCache cache, ILogger<CacheService> logger)
    {
        _cache = cache;
        _logger = logger;
    }

    public async Task<T?> GetAsync<T>(string key, CancellationToken cancellationToken = default) where T : class
    {
        try
        {
            var cachedValue = await _cache.GetStringAsync(key, cancellationToken);
            if (string.IsNullOrEmpty(cachedValue))
            {
                return null;
            }

            return JsonSerializer.Deserialize<T>(cachedValue);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Cache get error for key: {Key}", key);
            return null; // Cache hatası durumunda null döndür, DB'den çeksin
        }
    }

    public async Task SetAsync<T>(string key, T value, TimeSpan? absoluteExpiration = null, TimeSpan? slidingExpiration = null, CancellationToken cancellationToken = default) where T : class
    {
        try
        {
            var options = new DistributedCacheEntryOptions();

            if (absoluteExpiration.HasValue)
            {
                options.AbsoluteExpirationRelativeToNow = absoluteExpiration.Value;
            }

            if (slidingExpiration.HasValue)
            {
                options.SlidingExpiration = slidingExpiration.Value;
            }

            var serializedValue = JsonSerializer.Serialize(value);
            await _cache.SetStringAsync(key, serializedValue, options, cancellationToken);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Cache set error for key: {Key}", key);
            // Cache hatası durumunda devam et, kritik değil
        }
    }

    public async Task RemoveAsync(string key, CancellationToken cancellationToken = default)
    {
        try
        {
            await _cache.RemoveAsync(key, cancellationToken);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Cache remove error for key: {Key}", key);
        }
    }

    public async Task RemoveByPatternAsync(string pattern, CancellationToken cancellationToken = default)
    {
        // Redis'te pattern ile silme için StackExchange.Redis kullanılabilir
        // Şimdilik basit implementasyon, ileride genişletilebilir
        _logger.LogWarning("RemoveByPatternAsync not fully implemented. Pattern: {Pattern}", pattern);
        await Task.CompletedTask;
    }
}

