using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Döviz kurları - TCMB'den çekilen veya manuel girilen kurlar
/// </summary>
public class ExchangeRate : BaseEntity
{
    public string BaseCurrency { get; set; } = "TRY"; // TCMB için her zaman TRY
    public string TargetCurrency { get; set; } = string.Empty; // USD, EUR, GBP, etc.
    public decimal Rate { get; set; } // 1 BaseCurrency = Rate TargetCurrency
    public string Provider { get; set; } = "TCMB"; // TCMB, Manual, etc.
    public bool IsManual { get; set; } = false; // Manuel mi, otomatik mi?
    public DateTime FetchedAt { get; set; } = DateTime.UtcNow; // Ne zaman çekildi
    public DateTime? ValidUntil { get; set; } // Geçerlilik süresi (opsiyonel)
    
    // TCMB XML'den gelen ek bilgiler
    public decimal? BanknoteBuying { get; set; } // Efektif alış
    public decimal? BanknoteSelling { get; set; } // Efektif satış (bunu kullanıyoruz)
    public decimal? ForexBuying { get; set; } // Döviz alış
    public decimal? ForexSelling { get; set; } // Döviz satış
}

