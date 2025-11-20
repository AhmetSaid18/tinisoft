using MediatR;

namespace Tinisoft.Application.Templates.Queries.GetBootstrapData;

public class GetBootstrapDataQuery : IRequest<GetBootstrapDataResponse>
{
    // Host header'dan tenant bulunacak (Finbuckle ile)
}

public class GetBootstrapDataResponse
{
    public Guid TenantId { get; set; }
    public string TenantName { get; set; } = string.Empty;
    public string? TemplateKey { get; set; } // "minimal", "fashion", etc.
    public int? TemplateVersion { get; set; }
    
    // Theme ayarları (Tenant'tan)
    public BootstrapTheme Theme { get; set; } = new();
    
    // Site ayarları
    public BootstrapSettings Settings { get; set; } = new();
}

public class BootstrapTheme
{
    public string? PrimaryColor { get; set; }
    public string? SecondaryColor { get; set; }
    public string? BackgroundColor { get; set; }
    public string? TextColor { get; set; }
    public string? LinkColor { get; set; }
    public string? ButtonColor { get; set; }
    public string? ButtonTextColor { get; set; }
    public string? FontFamily { get; set; }
    public string? HeadingFontFamily { get; set; }
    public int? BaseFontSize { get; set; }
    public Dictionary<string, object>? LayoutSettings { get; set; }
}

public class BootstrapSettings
{
    public string? LogoUrl { get; set; }
    public string? FaviconUrl { get; set; }
    public string? SiteTitle { get; set; }
    public string? SiteDescription { get; set; }
    public string? FacebookUrl { get; set; }
    public string? InstagramUrl { get; set; }
    public string? TwitterUrl { get; set; }
    public string? LinkedInUrl { get; set; }
    public string? YouTubeUrl { get; set; }
    public string? TikTokUrl { get; set; }
    public string? PinterestUrl { get; set; }
    public string? WhatsAppNumber { get; set; }
    public string? TelegramUsername { get; set; }
    public string? Email { get; set; }
    public string? Phone { get; set; }
    public string? Address { get; set; }
    public string? City { get; set; }
    public string? Country { get; set; }
}



