using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Ödeme sağlayıcı entegrasyon ayarları (PayTR, Kuveyt Türk, Iyzico, vb.)
/// </summary>
public class PaymentProvider : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }

    public string ProviderCode { get; set; } = string.Empty; // "PAYTR", "KUVEYTTURK", "IYZICO", "STRIPE", vb.
    public string ProviderName { get; set; } = string.Empty; // "PayTR", "Kuveyt Türk", vb.
    public bool IsActive { get; set; } = true;

    // API Key yönetimi
    public string? ApiKey { get; set; }
    public string? ApiSecret { get; set; }
    public string? ApiUrl { get; set; } // Ödeme sağlayıcının API URL'i
    public string? TestApiUrl { get; set; } // Test ortamı API URL'i
    public bool UseTestMode { get; set; } = false;

    // Ek ayarlar (JSON formatında - her ödeme sağlayıcı için farklı olabilir)
    // Örneğin Kuveyt Türk için: {"StoreId": "...", "CustomerId": "...", "Username": "...", "Password": "..."}
    public string? SettingsJson { get; set; }

    // Varsayılan ayarlar
    public bool IsDefault { get; set; } = false; // Varsayılan ödeme sağlayıcı mı?
    public int Priority { get; set; } = 0; // Öncelik sırası (düşük sayı = yüksek öncelik)
}

