using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using System.Text;
using Tinisoft.Application.Notifications.Models;
using Tinisoft.Application.Notifications.Services;

namespace Tinisoft.Infrastructure.Services;

public class NetgsmSmsService : ISmsService
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<NetgsmSmsService> _logger;
    private readonly HttpClient _httpClient;
    private readonly string _userName;
    private readonly string _password;
    private readonly string _sender;

    public NetgsmSmsService(
        IConfiguration configuration,
        ILogger<NetgsmSmsService> logger,
        HttpClient httpClient)
    {
        _configuration = configuration;
        _logger = logger;
        _httpClient = httpClient;
        _userName = _configuration["Netgsm:UserName"] ?? throw new InvalidOperationException("Netgsm:UserName not configured");
        _password = _configuration["Netgsm:Password"] ?? throw new InvalidOperationException("Netgsm:Password not configured");
        _sender = _configuration["Netgsm:Sender"] ?? "TINISOFT";
        
        _httpClient.BaseAddress = new Uri("https://api.netgsm.com.tr/");
    }

    public async Task<NotificationResult> SendSmsAsync(SmsRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            // Clean phone number (remove spaces, dashes, parentheses)
            var cleanPhone = CleanPhoneNumber(request.PhoneNumber);
            
            // Netgsm SMS API
            var postData = $"usercode={_userName}" +
                          $"&password={_password}" +
                          $"&gsmno={cleanPhone}" +
                          $"&message={Uri.EscapeDataString(request.Message)}" +
                          $"&msgheader={_sender}" +
                          "&dil=TR";

            var content = new StringContent(postData, Encoding.UTF8, "application/x-www-form-urlencoded");
            var response = await _httpClient.PostAsync("sms/send/get/", content, cancellationToken);
            var result = await response.Content.ReadAsStringAsync(cancellationToken);

            // Netgsm returns:
            // Success: "00 <bulk_id>" or "00 <message_id>"
            // Error: "20", "30", etc.
            if (result.StartsWith("00"))
            {
                var messageId = result.Replace("00 ", "").Trim();
                _logger.LogInformation("SMS sent successfully to {Phone}, MessageId: {MessageId}", cleanPhone, messageId);
                
                return new NotificationResult
                {
                    Success = true,
                    MessageId = messageId,
                    SentAt = DateTime.UtcNow
                };
            }
            else
            {
                var errorMessage = GetNetgsmErrorMessage(result);
                _logger.LogError("Netgsm SMS error: {Code} - {Message}", result, errorMessage);
                
                return new NotificationResult
                {
                    Success = false,
                    ErrorMessage = errorMessage,
                    SentAt = DateTime.UtcNow
                };
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to send SMS to {Phone}", request.PhoneNumber);
            
            return new NotificationResult
            {
                Success = false,
                ErrorMessage = ex.Message,
                SentAt = DateTime.UtcNow
            };
        }
    }

    public async Task<NotificationResult> SendBulkSmsAsync(List<SmsRequest> requests, CancellationToken cancellationToken = default)
    {
        var results = new List<bool>();
        
        foreach (var request in requests)
        {
            var result = await SendSmsAsync(request, cancellationToken);
            results.Add(result.Success);
        }

        return new NotificationResult
        {
            Success = results.All(r => r),
            ErrorMessage = results.All(r => r) ? null : $"{results.Count(r => !r)} SMS failed",
            SentAt = DateTime.UtcNow
        };
    }

    private static string CleanPhoneNumber(string phone)
    {
        // Remove all non-digit characters
        var cleaned = new string(phone.Where(char.IsDigit).ToArray());
        
        // If starts with 0, remove it (Turkey format)
        if (cleaned.StartsWith("0"))
        {
            cleaned = cleaned[1..];
        }
        
        // Add country code if not present
        if (!cleaned.StartsWith("90"))
        {
            cleaned = "90" + cleaned;
        }
        
        return cleaned;
    }

    private static string GetNetgsmErrorMessage(string code)
    {
        return code.Trim() switch
        {
            "20" => "Mesaj metninde hata var (Boş mesaj)",
            "30" => "Geçersiz kullanıcı adı veya şifre",
            "40" => "Mesaj başlığı sisteme tanımlı değil",
            "50" => "Abone hesabında kredi yok",
            "51" => "Mesaj gönderim limitine ulaşıldı",
            "70" => "Hatalı numara",
            "85" => "Gönderim tarihi formatı hatalı",
            _ => $"Bilinmeyen hata kodu: {code}"
        };
    }
}

