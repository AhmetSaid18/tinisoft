namespace Tinisoft.Shared.Contracts;

public interface ICircuitBreakerService
{
    Task<bool> IsCircuitOpenAsync(CancellationToken cancellationToken = default);
    Task RecordSuccessAsync(CancellationToken cancellationToken = default);
    Task RecordFailureAsync(CancellationToken cancellationToken = default);
}

