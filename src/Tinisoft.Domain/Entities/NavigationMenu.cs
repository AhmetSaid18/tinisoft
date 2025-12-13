using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Site navigasyon menüsü: Header menü, Footer menü, vs.
/// </summary>
public class NavigationMenu : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    // Temel Bilgiler
    public string Title { get; set; } = string.Empty;           // "Hakkımızda", "Ürünler"
    public string? Url { get; set; }                            // Harici link için: "https://..."
    
    // Menü Tipi - Ne tür bir link?
    public NavigationItemType ItemType { get; set; } = NavigationItemType.Link;
    
    // İlişkili öğe (tip'e göre)
    public Guid? PageId { get; set; }                           // Sayfa linki ise
    public Page? Page { get; set; }
    
    public Guid? CategoryId { get; set; }                       // Kategori linki ise
    public Category? Category { get; set; }
    
    public Guid? ProductId { get; set; }                        // Ürün linki ise
    public Product? Product { get; set; }
    
    // Hiyerarşi (Alt menüler için)
    public Guid? ParentId { get; set; }
    public NavigationMenu? Parent { get; set; }
    public ICollection<NavigationMenu> Children { get; set; } = new List<NavigationMenu>();
    
    // Konum
    public NavigationLocation Location { get; set; } = NavigationLocation.Header;
    
    // Sıralama
    public int SortOrder { get; set; } = 0;
    
    // Görünürlük
    public bool IsVisible { get; set; } = true;
    
    // Stil
    public bool OpenInNewTab { get; set; } = false;             // Yeni sekmede aç
    public string? Icon { get; set; }                           // İkon (opsiyonel)
    public string? CssClass { get; set; }                       // Özel CSS class
}

/// <summary>
/// Menü öğesi tipi
/// </summary>
public enum NavigationItemType
{
    Link = 0,           // Harici veya özel link
    Page = 1,           // Sayfa linki
    Category = 2,       // Kategori linki
    Product = 3,        // Ürün linki
    Home = 4,           // Ana sayfa
    AllProducts = 5,    // Tüm ürünler
    AllCategories = 6,  // Tüm kategoriler
    Cart = 7,           // Sepet
    Account = 8         // Hesabım
}

/// <summary>
/// Menü konumu
/// </summary>
public enum NavigationLocation
{
    Header = 0,         // Üst menü
    Footer = 1,         // Alt menü
    Sidebar = 2,        // Yan menü
    MobileMenu = 3      // Mobil menü
}

