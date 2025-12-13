# Kargo Entegrasyonu Düzeltme Notları

## 🔍 Mevcut Durum

### ✅ Doğru Olanlar:
1. **ShippingProvider Entity**: Tenant bazlı (`ITenantEntity`)
2. **Handler**: Tenant'ın provider'ını database'den alıyor
3. **Marketplace Integration**: Zaten tenant bazlı çalışıyor

### ❌ Sorun:
**Shipping Servisleri** (YurticiShippingService, ArasShippingService, MngShippingService) hala `appsettings.json`'dan okuyor - sistem seviyesinde!

## 🎯 Çözüm

### Seçenek 1: Interface'e Provider Bilgileri Ekle (Önerilen)
```csharp
// IShippingService interface'ine ekle
Task<decimal?> CalculateShippingCostAsync(
    string providerCode,
    ShippingProviderCredentials? credentials, // YENİ
    string fromCity,
    ...
);

public class ShippingProviderCredentials
{
    public string? ApiKey { get; set; }
    public string? ApiSecret { get; set; }
    public string? ApiUrl { get; set; }
    public string? TestApiUrl { get; set; }
    public bool UseTestMode { get; set; }
    public string? SettingsJson { get; set; } // Username, Password, CustomerNumber vb.
}
```

### Seçenek 2: Handler'da Provider Bilgilerini Geçir
Handler'da provider bilgilerini alıp, servise geçirmek. Ama interface değişikliği gerekiyor.

## 📝 Yapılacaklar

1. ✅ `ShippingProvider` entity zaten tenant bazlı - TAMAM
2. ✅ Handler tenant'ın provider'ını buluyor - TAMAM  
3. ❌ Servisler hala appsettings.json'dan okuyor - DÜZELTİLMELİ
4. ❌ Handler provider bilgilerini servise geçirmiyor - DÜZELTİLMELİ

## 🔧 Düzeltme Adımları

1. `IShippingService` interface'ine `ShippingProviderCredentials` parametresi ekle
2. Handler'da provider bilgilerini al ve servise geçir
3. Servis implementasyonlarını güncelle (appsettings yerine parametre kullan)
4. `appsettings.json`'daki shipping ayarlarını kaldır (artık gerek yok)

## 💡 Not

- `.env` dosyasındaki kargo API key'leri **SİSTEM SEVİYESİNDE** değil
- Her tenant kendi API key'lerini **DATABASE'DE** (ShippingProvider tablosunda) tutuyor
- Bu doğru yaklaşım! ✅

