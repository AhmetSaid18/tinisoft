using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Tinisoft.Application.Payments.Services;
using System.Text.Json.Nodes;

namespace Tinisoft.Infrastructure.Services;

/// <summary>
/// PayTR ödeme entegrasyonu - IPaymentService implementasyonu
/// </summary>
public class PayTRPaymentService : IPaymentService
{
    private readonly IConfiguration _configuration;
    private readonly HttpClient _httpClient;
    private readonly ILogger<PayTRPaymentService> _logger;

    public PayTRPaymentService(
        IConfiguration configuration, 
        HttpClient httpClient,
        ILogger<PayTRPaymentService> logger)
    {
        _configuration = configuration;
        _httpClient = httpClient;
        _logger = logger;
    }

    public async Task<PaymentTokenResponse> GetPaymentTokenAsync(
        PaymentProviderCredentials credentials,
        PaymentTokenRequest request,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Getting payment token from PayTR for order: {OrderId}", request.OrderId);

        try
        {
            // Tenant'ın credentials'ını kullan, yoksa appsettings'den al (fallback)
            var merchantId = credentials?.ApiKey ?? _configuration["PayTR:MerchantId"];
            var merchantKey = credentials?.ApiSecret ?? _configuration["PayTR:MerchantKey"];
            var merchantSalt = credentials?.SettingsJson ?? _configuration["PayTR:MerchantSalt"];

            // SettingsJson'dan da alabilir (JSON formatında)
            if (!string.IsNullOrEmpty(credentials?.SettingsJson) && string.IsNullOrEmpty(merchantSalt))
            {
                try
                {
                    var settings = JsonNode.Parse(credentials.SettingsJson);
                    merchantId = settings?["MerchantId"]?.ToString() ?? merchantId;
                    merchantKey = settings?["MerchantKey"]?.ToString() ?? merchantKey;
                    merchantSalt = settings?["MerchantSalt"]?.ToString() ?? merchantSalt;
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Failed to parse SettingsJson for PayTR");
                }
            }

            if (string.IsNullOrEmpty(merchantId) || string.IsNullOrEmpty(merchantKey) || string.IsNullOrEmpty(merchantSalt))
            {
                return new PaymentTokenResponse
                {
                    Success = false,
                    ErrorMessage = "PayTR API bilgileri eksik (MerchantId, MerchantKey, MerchantSalt)"
                };
            }

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
                currency = request.Currency ?? "TRY",
                hash = hash
            };

            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var apiUrl = credentials?.ApiUrl ?? 
                        (credentials?.UseTestMode == true ? credentials.TestApiUrl : null) ??
                        "https://www.paytr.com";

            var response = await _httpClient.PostAsync($"{apiUrl}/odeme/api/get-token", content, cancellationToken);
            var responseContent = await response.Content.ReadAsStringAsync(cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                _logger.LogError("PayTR API error: {StatusCode} - {Response}", 
                    response.StatusCode, responseContent);
                
                return new PaymentTokenResponse
                {
                    Success = false,
                    ErrorMessage = $"PayTR API hatası: {response.StatusCode}"
                };
            }

            var result = JsonSerializer.Deserialize<JsonNode>(responseContent);
            var token = result?["token"]?.ToString();
            var status = result?["status"]?.ToString();
            var errorMessage = result?["reason"]?.ToString();

            if (status == "success" && !string.IsNullOrEmpty(token))
            {
                return new PaymentTokenResponse
                {
                    Success = true,
                    Token = token,
                    RedirectUrl = $"https://www.paytr.com/odeme/guvenli/{token}"
                };
            }

            return new PaymentTokenResponse
            {
                Success = false,
                ErrorMessage = errorMessage ?? "Token alınamadı"
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting payment token from PayTR");
            return new PaymentTokenResponse
            {
                Success = false,
                ErrorMessage = $"PayTR entegrasyon hatası: {ex.Message}"
            };
        }
    }

    public async Task<bool> VerifyCallbackAsync(
        PaymentProviderCredentials credentials,
        string hash,
        Dictionary<string, string> parameters,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Verifying PayTR payment callback");

        try
        {
            var merchantSalt = credentials?.SettingsJson ?? _configuration["PayTR:MerchantSalt"];

            // SettingsJson'dan da alabilir
            if (!string.IsNullOrEmpty(credentials?.SettingsJson))
            {
                try
                {
                    var settings = JsonNode.Parse(credentials.SettingsJson);
                    merchantSalt = settings?["MerchantSalt"]?.ToString() ?? merchantSalt;
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Failed to parse SettingsJson for PayTR verification");
                }
            }

            if (string.IsNullOrEmpty(merchantSalt))
            {
                _logger.LogError("PayTR MerchantSalt not configured");
                return false;
            }

            var hashString = $"{parameters.GetValueOrDefault("merchant_oid", "")}{merchantSalt}{parameters.GetValueOrDefault("status", "")}{parameters.GetValueOrDefault("total_amount", "")}";
            var computedHash = ComputeHash(hashString);

            return computedHash == hash;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error verifying PayTR payment callback");
            return false;
        }
    }

    private static string ComputeHash(string input)
    {
        using var sha256 = SHA256.Create();
        var hashBytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(input));
        return Convert.ToBase64String(hashBytes);
    }
}

