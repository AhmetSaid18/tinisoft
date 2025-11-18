using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Kargo firması entegrasyon ayarları
/// </summary>
public class ShippingProvider : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }

    public string ProviderCode { get; set; } = string.Empty; // "ARAS", "MNG", "YURTICI", "SURAT", vb.
    public string ProviderName { get; set; } = string.Empty; // "Aras Kargo", "MNG Kargo", vb.
    public bool IsActive { get; set; } = true;

    // API Key yönetimi
    public string? ApiKey { get; set; }
    public string? ApiSecret { get; set; }
    public string? ApiUrl { get; set; } // Kargo firmasının API URL'i
    public string? TestApiUrl { get; set; } // Test ortamı API URL'i
    public bool UseTestMode { get; set; } = false;

    // Ek ayarlar (JSON formatında - her kargo firması için farklı olabilir)
    public string? SettingsJson { get; set; } // Özel ayarlar (branch code, customer code, vb.)

    // Varsayılan ayarlar
    public bool IsDefault { get; set; } = false; // Varsayılan kargo firması mı?
    public int Priority { get; set; } = 0; // Öncelik sırası (düşük sayı = yüksek öncelik)
}

