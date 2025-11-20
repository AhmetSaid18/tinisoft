using MediatR;

namespace Tinisoft.Application.Tenant.Queries.GetTenantPublicInfo;

public class GetTenantPublicInfoQuery : IRequest<GetTenantPublicInfoResponse>
{
    public string? Slug { get; set; } // Slug ile tenant bulunabilir
}

public class GetTenantPublicInfoResponse
{
    public Guid TenantId { get; set; }
    public string Name { get; set; } = string.Empty;
    
    // Sosyal Medya Linkleri (Public - site footer/header'da gösterilecek)
    public string? FacebookUrl { get; set; }
    public string? InstagramUrl { get; set; }
    public string? TwitterUrl { get; set; }
    public string? LinkedInUrl { get; set; }
    public string? YouTubeUrl { get; set; }
    public string? TikTokUrl { get; set; }
    public string? PinterestUrl { get; set; }
    public string? WhatsAppNumber { get; set; }
    public string? TelegramUsername { get; set; }
    
    // İletişim Bilgileri (Public)
    public string? Email { get; set; }
    public string? Phone { get; set; }
    public string? Address { get; set; }
    public string? City { get; set; }
    public string? Country { get; set; }
    
    // E-Ticaret Site Görsel Ayarları (Public - frontend'de kullanılacak)
    public string? LogoUrl { get; set; }
    public string? FaviconUrl { get; set; }
    public string? SiteTitle { get; set; }
    public string? SiteDescription { get; set; }
    
    // Tema Renkleri (Public - frontend'de CSS değişkenleri olarak kullanılacak)
    public string? PrimaryColor { get; set; }
    public string? SecondaryColor { get; set; }
    public string? BackgroundColor { get; set; }
    public string? TextColor { get; set; }
    public string? LinkColor { get; set; }
    public string? ButtonColor { get; set; }
    public string? ButtonTextColor { get; set; }
    
    // Font Ayarları (Public)
    public string? FontFamily { get; set; }
    public string? HeadingFontFamily { get; set; }
    public int? BaseFontSize { get; set; }
    
    // Layout Ayarları (Public - frontend'de layout'u dinamik oluşturmak için)
    public Dictionary<string, object>? LayoutSettings { get; set; }
}



