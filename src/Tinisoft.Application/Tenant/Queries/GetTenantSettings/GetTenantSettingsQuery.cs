using MediatR;

namespace Tinisoft.Application.Tenant.Queries.GetTenantSettings;

public class GetTenantSettingsQuery : IRequest<GetTenantSettingsResponse>
{
}

public class GetTenantSettingsResponse
{
    public Guid TenantId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    
    // Sosyal Medya Linkleri
    public string? FacebookUrl { get; set; }
    public string? InstagramUrl { get; set; }
    public string? TwitterUrl { get; set; }
    public string? LinkedInUrl { get; set; }
    public string? YouTubeUrl { get; set; }
    public string? TikTokUrl { get; set; }
    public string? PinterestUrl { get; set; }
    public string? WhatsAppNumber { get; set; }
    public string? TelegramUsername { get; set; }
    
    // İletişim Bilgileri
    public string? Email { get; set; }
    public string? Phone { get; set; }
    public string? Address { get; set; }
    public string? City { get; set; }
    public string? Country { get; set; }
    
    // E-Ticaret Site Görsel Ayarları
    public string? LogoUrl { get; set; }
    public string? FaviconUrl { get; set; }
    public string? SiteTitle { get; set; }
    public string? SiteDescription { get; set; }
    
    // Tema Renkleri
    public string? PrimaryColor { get; set; }
    public string? SecondaryColor { get; set; }
    public string? BackgroundColor { get; set; }
    public string? TextColor { get; set; }
    public string? LinkColor { get; set; }
    public string? ButtonColor { get; set; }
    public string? ButtonTextColor { get; set; }
    
    // Font Ayarları
    public string? FontFamily { get; set; }
    public string? HeadingFontFamily { get; set; }
    public int? BaseFontSize { get; set; }
}



