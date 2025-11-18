using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class Tenant : BaseEntity
{
    public string Name { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty; // tenant.tinisoft.com için
    public bool IsActive { get; set; } = true;
    public Guid PlanId { get; set; }
    public Plan? Plan { get; set; }
    
    // SaaS Billing
    public DateTime? SubscriptionStartDate { get; set; }
    public DateTime? SubscriptionEndDate { get; set; }
    public string? PayTRSubscriptionToken { get; set; }
    
    // Sosyal Medya Linkleri (Opsiyonel - Dashboard'dan düzenlenebilir)
    public string? FacebookUrl { get; set; }
    public string? InstagramUrl { get; set; }
    public string? TwitterUrl { get; set; }
    public string? LinkedInUrl { get; set; }
    public string? YouTubeUrl { get; set; }
    public string? TikTokUrl { get; set; }
    public string? PinterestUrl { get; set; }
    public string? WhatsAppNumber { get; set; } // WhatsApp Business numarası
    public string? TelegramUsername { get; set; }
    
    // İletişim Bilgileri
    public string? Email { get; set; } // İletişim email'i
    public string? Phone { get; set; } // İletişim telefonu
    public string? Address { get; set; } // Adres
    public string? City { get; set; }
    public string? Country { get; set; }
    
    // E-Ticaret Site Görsel Ayarları (Dashboard'dan düzenlenebilir)
    public string? LogoUrl { get; set; } // Site logosu
    public string? FaviconUrl { get; set; } // Favicon
    public string? SiteTitle { get; set; } // Site başlığı (header'da gösterilecek)
    public string? SiteDescription { get; set; } // Site açıklaması
    
    // Tema Renkleri
    public string? PrimaryColor { get; set; } // Ana renk (örn: #FF5733)
    public string? SecondaryColor { get; set; } // İkincil renk
    public string? BackgroundColor { get; set; } // Arka plan rengi
    public string? TextColor { get; set; } // Metin rengi
    public string? LinkColor { get; set; } // Link rengi
    public string? ButtonColor { get; set; } // Buton rengi
    public string? ButtonTextColor { get; set; } // Buton metin rengi
    
    // Font Ayarları
    public string? FontFamily { get; set; } // Font ailesi (örn: "Roboto", "Inter", "Poppins")
    public string? HeadingFontFamily { get; set; } // Başlık fontu
    public int? BaseFontSize { get; set; } // Temel font boyutu (px)
    
    // Layout Ayarları (JSON - esnek yapı için)
    // Örnek: {headerStyle: "sticky", footerStyle: "fixed", productGridColumns: 4, showBreadcrumbs: true}
    public string? LayoutSettingsJson { get; set; }
    
    // Template Seçimi (Tek seferlik, geri dönülemez)
    public string? SelectedTemplateCode { get; set; } // "minimal", "fashion", "restaurant"
    public int? SelectedTemplateVersion { get; set; } // 1, 2, 3...
    public DateTime? TemplateSelectedAt { get; set; } // Ne zaman seçildi
    
    // Currency Settings
    public string BaseCurrency { get; set; } = "TRY"; // Varsayılan para birimi
    public string? PurchaseCurrency { get; set; } // Giriş para birimi (EUR, USD, etc.)
    public string SaleCurrency { get; set; } = "TRY"; // Satış para birimi (sitede gösterilecek)
    public decimal CurrencyMarginPercent { get; set; } = 0; // Kur marjı (%)
    public bool AutoUpdateExchangeRates { get; set; } = true; // Otomatik kur güncelleme
    
    // Navigation
    public ICollection<Domain> Domains { get; set; } = new List<Domain>();
    public ICollection<UserTenantRole> UserTenantRoles { get; set; } = new List<UserTenantRole>();
    public ICollection<Product> Products { get; set; } = new List<Product>();
    public ICollection<Order> Orders { get; set; } = new List<Order>();
}

