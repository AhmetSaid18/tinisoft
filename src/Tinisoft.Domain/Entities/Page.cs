using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Özel sayfalar: Hakkımızda, İletişim, KVKK, İade Politikası, vs.
/// </summary>
public class Page : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    // Temel Bilgiler
    public string Title { get; set; } = string.Empty;           // "Hakkımızda"
    public string Slug { get; set; } = string.Empty;            // "hakkimizda" (URL için)
    public string Content { get; set; } = string.Empty;         // HTML içerik (zengin metin)
    
    // SEO
    public string? MetaTitle { get; set; }                      // SEO başlık
    public string? MetaDescription { get; set; }                // SEO açıklama
    public string? MetaKeywords { get; set; }                   // SEO anahtar kelimeler
    public string? CanonicalUrl { get; set; }                   // Canonical URL
    
    // Görsel
    public string? FeaturedImageUrl { get; set; }               // Öne çıkan görsel
    
    // Durum
    public bool IsPublished { get; set; } = false;              // Yayında mı?
    public DateTime? PublishedAt { get; set; }                  // Yayın tarihi
    
    // Şablon
    public string Template { get; set; } = "default";           // Sayfa şablonu (default, full-width, sidebar)
    
    // Sıralama
    public int SortOrder { get; set; } = 0;
    
    // Sistem sayfası mı? (silinemez)
    public bool IsSystemPage { get; set; } = false;             // KVKK, Gizlilik gibi zorunlu sayfalar
    public string? SystemPageType { get; set; }                 // "privacy", "terms", "refund", "contact"
}

