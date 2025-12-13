using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Tinisoft.Application.Payments.Services;
using System.Text.Json.Nodes;

namespace Tinisoft.Infrastructure.Services;

/// <summary>
/// Kuveyt Türk ödeme entegrasyonu
/// </summary>
public class KuveytTurkPaymentService : IPaymentService
{
    private readonly ILogger<KuveytTurkPaymentService> _logger;
    private readonly HttpClient _httpClient;
    private readonly IConfiguration _configuration;

    public KuveytTurkPaymentService(
        ILogger<KuveytTurkPaymentService> logger,
        HttpClient httpClient,
        IConfiguration configuration)
    {
        _logger = logger;
        _httpClient = httpClient;
        _configuration = configuration;
    }

    public async Task<PaymentTokenResponse> GetPaymentTokenAsync(
        PaymentProviderCredentials credentials,
        PaymentTokenRequest request,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Getting payment token from Kuveyt Türk for order: {OrderId}", request.OrderId);

        try
        {
            // Tenant'ın credentials'ını kullan, yoksa appsettings'den al (fallback)
            var apiUrl = credentials?.ApiUrl ?? 
                        (credentials?.UseTestMode == true ? credentials.TestApiUrl : null) ??
                        _configuration["KuveytTurk:ApiUrl"] ?? 
                        "https://www.kuveytturk.com.tr";

            // SettingsJson'dan Mağaza ID, Müşteri ID, Kullanıcı Adı, Parola al
            string? storeId = null;
            string? customerId = null;
            string? username = null;
            string? password = null;

            if (!string.IsNullOrEmpty(credentials?.SettingsJson))
            {
                try
                {
                    var settings = JsonNode.Parse(credentials.SettingsJson);
                    storeId = settings?["StoreId"]?.ToString();
                    customerId = settings?["CustomerId"]?.ToString();
                    username = settings?["Username"]?.ToString();
                    password = settings?["Password"]?.ToString();
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Failed to parse SettingsJson for Kuveyt Türk");
                }
            }

            // Fallback: appsettings'den al
            if (string.IsNullOrEmpty(storeId))
                storeId = _configuration["KuveytTurk:StoreId"];
            if (string.IsNullOrEmpty(customerId))
                customerId = _configuration["KuveytTurk:CustomerId"];
            if (string.IsNullOrEmpty(username))
                username = _configuration["KuveytTurk:Username"];
            if (string.IsNullOrEmpty(password))
                password = _configuration["KuveytTurk:Password"];

            if (string.IsNullOrEmpty(storeId) || string.IsNullOrEmpty(customerId) || 
                string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
            {
                return new PaymentTokenResponse
                {
                    Success = false,
                    ErrorMessage = "Kuveyt Türk API bilgileri eksik (StoreId, CustomerId, Username, Password)"
                };
            }

            // Kuveyt Türk API'ye ödeme isteği gönder
            // NOT: Bu gerçek API endpoint'i ve format'ı Kuveyt Türk dokümantasyonuna göre güncellenmelidir
            var payload = new
            {
                StoreId = storeId,
                CustomerId = customerId,
                Username = username,
                Password = password,
                OrderId = request.OrderId,
                Amount = request.Amount,
                Currency = request.Currency,
                Email = request.Email,
                Installment = request.Installment ?? "0",
                // Diğer gerekli alanlar...
            };

            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            // API endpoint - Kuveyt Türk dokümantasyonuna göre güncellenmeli
            var endpoint = $"{apiUrl}/api/payment/get-token"; // Örnek endpoint
            
            var response = await _httpClient.PostAsync(endpoint, content, cancellationToken);
            var responseContent = await response.Content.ReadAsStringAsync(cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                _logger.LogError("Kuveyt Türk API error: {StatusCode} - {Response}", 
                    response.StatusCode, responseContent);
                
                return new PaymentTokenResponse
                {
                    Success = false,
                    ErrorMessage = $"Kuveyt Türk API hatası: {response.StatusCode}"
                };
            }

            var result = JsonSerializer.Deserialize<JsonNode>(responseContent);
            
            // Kuveyt Türk response format'ına göre parse et
            // NOT: Gerçek response format'ı Kuveyt Türk dokümantasyonuna göre güncellenmelidir
            var token = result?["Token"]?.ToString();
            var redirectUrl = result?["RedirectUrl"]?.ToString();
            var errorMessage = result?["ErrorMessage"]?.ToString();

            if (!string.IsNullOrEmpty(token))
            {
                return new PaymentTokenResponse
                {
                    Success = true,
                    Token = token,
                    RedirectUrl = redirectUrl ?? $"{apiUrl}/payment/{token}"
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
            _logger.LogError(ex, "Error getting payment token from Kuveyt Türk");
            return new PaymentTokenResponse
            {
                Success = false,
                ErrorMessage = $"Kuveyt Türk entegrasyon hatası: {ex.Message}"
            };
        }
    }

    public async Task<bool> VerifyCallbackAsync(
        PaymentProviderCredentials credentials,
        string hash,
        Dictionary<string, string> parameters,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Verifying Kuveyt Türk payment callback");

        try
        {
            // SettingsJson'dan gerekli bilgileri al
            string? storeId = null;
            string? customerId = null;

            if (!string.IsNullOrEmpty(credentials?.SettingsJson))
            {
                try
                {
                    var settings = JsonNode.Parse(credentials.SettingsJson);
                    storeId = settings?["StoreId"]?.ToString();
                    customerId = settings?["CustomerId"]?.ToString();
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Failed to parse SettingsJson for Kuveyt Türk verification");
                }
            }

            // Fallback: appsettings'den al
            if (string.IsNullOrEmpty(storeId))
                storeId = _configuration["KuveytTurk:StoreId"];
            if (string.IsNullOrEmpty(customerId))
                customerId = _configuration["KuveytTurk:CustomerId"];

            // Kuveyt Türk callback verification
            // NOT: Gerçek hash algoritması ve doğrulama mantığı Kuveyt Türk dokümantasyonuna göre güncellenmelidir
            var orderId = parameters.GetValueOrDefault("OrderId", "");
            var status = parameters.GetValueOrDefault("Status", "");
            var amount = parameters.GetValueOrDefault("Amount", "");

            // Hash doğrulama - Kuveyt Türk'ün hash algoritmasına göre güncellenmeli
            var hashString = $"{orderId}{storeId}{customerId}{status}{amount}";
            // Hash hesaplama ve karşılaştırma burada yapılmalı

            // Şimdilik basit bir kontrol
            return status == "Success" || status == "SUCCESS";
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error verifying Kuveyt Türk payment callback");
            return false;
        }
    }
}

