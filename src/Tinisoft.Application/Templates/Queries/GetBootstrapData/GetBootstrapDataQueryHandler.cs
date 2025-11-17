using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Templates.Queries.GetBootstrapData;

public class GetBootstrapDataQueryHandler : IRequestHandler<GetBootstrapDataQuery, GetBootstrapDataResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetBootstrapDataQueryHandler> _logger;

    public GetBootstrapDataQueryHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetBootstrapDataQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetBootstrapDataResponse> Handle(GetBootstrapDataQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var tenant = await _dbContext.Set<Tenant>()
            .FirstOrDefaultAsync(t => t.Id == tenantId && t.IsActive, cancellationToken);

        if (tenant == null)
        {
            throw new NotFoundException("Tenant", tenantId);
        }

        // Layout settings JSON'ı parse et
        Dictionary<string, object>? layoutSettings = null;
        if (!string.IsNullOrWhiteSpace(tenant.LayoutSettingsJson))
        {
            try
            {
                layoutSettings = System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, object>>(tenant.LayoutSettingsJson);
            }
            catch
            {
                // JSON parse hatası durumunda null bırak
            }
        }

        var theme = new BootstrapTheme
        {
            PrimaryColor = tenant.PrimaryColor,
            SecondaryColor = tenant.SecondaryColor,
            BackgroundColor = tenant.BackgroundColor,
            TextColor = tenant.TextColor,
            LinkColor = tenant.LinkColor,
            ButtonColor = tenant.ButtonColor,
            ButtonTextColor = tenant.ButtonTextColor,
            FontFamily = tenant.FontFamily,
            HeadingFontFamily = tenant.HeadingFontFamily,
            BaseFontSize = tenant.BaseFontSize,
            LayoutSettings = layoutSettings
        };

        var settings = new BootstrapSettings
        {
            LogoUrl = tenant.LogoUrl,
            FaviconUrl = tenant.FaviconUrl,
            SiteTitle = tenant.SiteTitle,
            SiteDescription = tenant.SiteDescription,
            FacebookUrl = tenant.FacebookUrl,
            InstagramUrl = tenant.InstagramUrl,
            TwitterUrl = tenant.TwitterUrl,
            LinkedInUrl = tenant.LinkedInUrl,
            YouTubeUrl = tenant.YouTubeUrl,
            TikTokUrl = tenant.TikTokUrl,
            PinterestUrl = tenant.PinterestUrl,
            WhatsAppNumber = tenant.WhatsAppNumber,
            TelegramUsername = tenant.TelegramUsername,
            Email = tenant.Email,
            Phone = tenant.Phone,
            Address = tenant.Address,
            City = tenant.City,
            Country = tenant.Country
        };

        return new GetBootstrapDataResponse
        {
            TenantId = tenant.Id,
            TenantName = tenant.Name,
            TemplateKey = tenant.SelectedTemplateCode,
            TemplateVersion = tenant.SelectedTemplateVersion,
            Theme = theme,
            Settings = settings
        };
    }
}

