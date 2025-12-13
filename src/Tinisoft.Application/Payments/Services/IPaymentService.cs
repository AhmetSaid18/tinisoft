namespace Tinisoft.Application.Payments.Services;

/// <summary>
/// Ödeme sağlayıcı entegrasyon servisi interface'i
/// </summary>
public interface IPaymentService
{
    /// <summary>
    /// Ödeme token'ı al (iFrame için)
    /// </summary>
    Task<PaymentTokenResponse> GetPaymentTokenAsync(
        PaymentProviderCredentials credentials,
        PaymentTokenRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Ödeme callback'ini doğrula
    /// </summary>
    Task<bool> VerifyCallbackAsync(
        PaymentProviderCredentials credentials,
        string hash,
        Dictionary<string, string> parameters,
        CancellationToken cancellationToken = default);
}

/// <summary>
/// Tenant'ın ödeme sağlayıcı API bilgileri
/// </summary>
public record PaymentProviderCredentials(
    string? ApiKey,
    string? ApiSecret,
    string? ApiUrl,
    string? TestApiUrl,
    bool UseTestMode,
    string? SettingsJson // JSON formatında ek ayarlar (StoreId, CustomerId, Username, Password vb.)
);

public class PaymentTokenRequest
{
    public string Email { get; set; } = string.Empty;
    public decimal Amount { get; set; }
    public string OrderId { get; set; } = string.Empty;
    public string? Installment { get; set; }
    public string Currency { get; set; } = "TRY";
    public Dictionary<string, string>? AdditionalData { get; set; }
}

public class PaymentTokenResponse
{
    public bool Success { get; set; }
    public string? Token { get; set; }
    public string? RedirectUrl { get; set; }
    public string? ErrorMessage { get; set; }
}

