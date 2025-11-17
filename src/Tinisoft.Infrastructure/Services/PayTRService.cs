using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;

namespace Tinisoft.Infrastructure.Services;

public class PayTRService : IPayTRService
{
    private readonly IConfiguration _configuration;
    private readonly HttpClient _httpClient;

    public PayTRService(IConfiguration configuration, HttpClient httpClient)
    {
        _configuration = configuration;
        _httpClient = httpClient;
    }

    public async Task<PayTRTokenResponse> GetTokenAsync(PayTRTokenRequest request, CancellationToken cancellationToken = default)
    {
        var merchantId = _configuration["PayTR:MerchantId"] ?? request.MerchantId;
        var merchantKey = _configuration["PayTR:MerchantKey"] ?? request.MerchantKey;
        var merchantSalt = _configuration["PayTR:MerchantSalt"] ?? request.MerchantSalt;

        // Hash oluştur
        var hashString = $"{merchantId}{request.Email}{request.Amount}{request.OrderId}{merchantSalt}";
        var hash = ComputeHash(hashString);

        var payload = new
        {
            merchant_id = merchantId,
            merchant_key = merchantKey,
            merchant_salt = merchantSalt,
            email = request.Email,
            payment_amount = (int)(request.Amount * 100), // Kuruş cinsinden
            merchant_oid = request.OrderId,
            installment = request.Installment ?? "0",
            currency = request.Currency ?? "TL",
            hash = hash
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await _httpClient.PostAsync("https://www.paytr.com/odeme/api/get-token", content, cancellationToken);
        var responseContent = await response.Content.ReadAsStringAsync(cancellationToken);

        var result = JsonSerializer.Deserialize<PayTRTokenResponse>(responseContent);

        return result ?? new PayTRTokenResponse { Success = false, ErrorMessage = "Invalid response" };
    }

    public Task<bool> VerifyCallbackAsync(string hash, Dictionary<string, string> parameters, CancellationToken cancellationToken = default)
    {
        var merchantSalt = _configuration["PayTR:MerchantSalt"] ?? throw new InvalidOperationException("PayTR MerchantSalt not configured");

        var hashString = $"{parameters["merchant_oid"]}{merchantSalt}{parameters["status"]}{parameters["total_amount"]}";
        var computedHash = ComputeHash(hashString);

        return Task.FromResult(computedHash == hash);
    }

    private static string ComputeHash(string input)
    {
        using var sha256 = SHA256.Create();
        var hashBytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(input));
        return Convert.ToBase64String(hashBytes);
    }
}

