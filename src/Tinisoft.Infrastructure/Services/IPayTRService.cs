namespace Tinisoft.Infrastructure.Services;

public interface IPayTRService
{
    Task<PayTRTokenResponse> GetTokenAsync(PayTRTokenRequest request, CancellationToken cancellationToken = default);
    Task<bool> VerifyCallbackAsync(string hash, Dictionary<string, string> parameters, CancellationToken cancellationToken = default);
}

public class PayTRTokenRequest
{
    public string MerchantId { get; set; } = string.Empty;
    public string MerchantKey { get; set; } = string.Empty;
    public string MerchantSalt { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public decimal Amount { get; set; }
    public string OrderId { get; set; } = string.Empty;
    public string? Installment { get; set; }
    public string? Currency { get; set; } = "TL";
}

public class PayTRTokenResponse
{
    public bool Success { get; set; }
    public string? Token { get; set; }
    public string? ErrorMessage { get; set; }
}

