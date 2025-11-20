using Microsoft.Extensions.Caching.Distributed;
using System.Text.Json;
using Tinisoft.Shared.Contracts;
using Microsoft.Extensions.Logging;

namespace Tinisoft.Infrastructure.Services;

/// <summary>
/// Circuit Breaker Pattern - Database yükü çok olduğunda koruma
/// Cold start senaryosunda database'i korur
/// </summary>
public class CircuitBreakerService : ICircuitBreakerService
{
    private readonly IDistributedCache _cache;
    private readonly ILogger<CircuitBreakerService> _logger;
    
    private const string CircuitBreakerKey = "circuitbreaker:database";
    private const int FailureThreshold = 200; // 200 başarısız istek sonra circuit aç (cold start için yeterli)
    private const int SuccessThreshold = 50; // 50 başarılı istek sonra circuit kapat
    private readonly TimeSpan OpenDuration = TimeSpan.FromSeconds(30); // 30 saniye açık kal (daha hızlı recovery)

    public CircuitBreakerService(
        IDistributedCache cache,
        ILogger<CircuitBreakerService> logger)
    {
        _cache = cache;
        _logger = logger;
    }

    public async Task<bool> IsCircuitOpenAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            var stateJson = await _cache.GetStringAsync(CircuitBreakerKey, cancellationToken);
            if (string.IsNullOrEmpty(stateJson))
            {
                return false; // Circuit kapalı
            }

            var state = JsonSerializer.Deserialize<CircuitBreakerState>(stateJson);
            if (state == null)
            {
                return false;
            }

            // Circuit açık ve süre dolmamışsa
            if (state.IsOpen && DateTime.UtcNow < state.OpenedAt.Add(OpenDuration))
            {
                return true; // Circuit açık
            }

            // Süre dolmuşsa circuit'i kapat
            if (state.IsOpen && DateTime.UtcNow >= state.OpenedAt.Add(OpenDuration))
            {
                await ResetCircuitAsync(cancellationToken);
                return false;
            }

            return false;
        }
        catch
        {
            // Cache hatası durumunda circuit'i açık sayma (güvenli taraf)
            return false;
        }
    }

    public async Task RecordSuccessAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            var stateJson = await _cache.GetStringAsync(CircuitBreakerKey, cancellationToken);
            if (string.IsNullOrEmpty(stateJson))
            {
                return;
            }

            var state = JsonSerializer.Deserialize<CircuitBreakerState>(stateJson);
            if (state == null)
            {
                return;
            }

            state.SuccessCount++;
            state.FailureCount = 0; // Başarılı istek failure count'u sıfırlar

            // Yeterli başarılı istek varsa circuit'i kapat
            if (state.SuccessCount >= SuccessThreshold)
            {
                await ResetCircuitAsync(cancellationToken);
                _logger.LogInformation("Circuit breaker closed after {SuccessCount} successful requests", state.SuccessCount);
            }
            else
            {
                await SaveStateAsync(state, cancellationToken);
            }
        }
        catch
        {
            // Cache hatası kritik değil
        }
    }

    public async Task RecordFailureAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            var stateJson = await _cache.GetStringAsync(CircuitBreakerKey, cancellationToken);
            CircuitBreakerState state;

            if (string.IsNullOrEmpty(stateJson))
            {
                state = new CircuitBreakerState();
            }
            else
            {
                state = JsonSerializer.Deserialize<CircuitBreakerState>(stateJson) ?? new CircuitBreakerState();
            }

            state.FailureCount++;
            state.SuccessCount = 0; // Başarısız istek success count'u sıfırlar

            // Yeterli başarısız istek varsa circuit'i aç
            if (state.FailureCount >= FailureThreshold)
            {
                state.IsOpen = true;
                state.OpenedAt = DateTime.UtcNow;
                _logger.LogWarning("Circuit breaker opened after {FailureCount} failures", state.FailureCount);
            }

            await SaveStateAsync(state, cancellationToken);
        }
        catch
        {
            // Cache hatası kritik değil
        }
    }

    private async Task ResetCircuitAsync(CancellationToken cancellationToken)
    {
        await _cache.RemoveAsync(CircuitBreakerKey, cancellationToken);
    }

    private async Task SaveStateAsync(CircuitBreakerState state, CancellationToken cancellationToken)
    {
        var stateJson = JsonSerializer.Serialize(state);
        var options = new DistributedCacheEntryOptions
        {
            AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(10)
        };
        await _cache.SetStringAsync(CircuitBreakerKey, stateJson, options, cancellationToken);
    }

    private class CircuitBreakerState
    {
        public bool IsOpen { get; set; }
        public DateTime OpenedAt { get; set; }
        public int FailureCount { get; set; }
        public int SuccessCount { get; set; }
    }
}

