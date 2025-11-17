using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Tenant.Queries.GetTenantPublicInfo;

public class GetTenantPublicInfoQueryHandler : IRequestHandler<GetTenantPublicInfoQuery, GetTenantPublicInfoResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetTenantPublicInfoQueryHandler> _logger;

    public GetTenantPublicInfoQueryHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetTenantPublicInfoQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetTenantPublicInfoResponse> Handle(GetTenantPublicInfoQuery request, CancellationToken cancellationToken)
    {
        Tenant? tenant;

        if (!string.IsNullOrWhiteSpace(request.Slug))
        {
            // Slug ile tenant bul
            tenant = await _dbContext.Set<Tenant>()
                .FirstOrDefaultAsync(t => t.Slug == request.Slug && t.IsActive, cancellationToken);
        }
        else
        {
            // Multi-tenant context'ten tenant bul
            var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);
            tenant = await _dbContext.Set<Tenant>()
                .FirstOrDefaultAsync(t => t.Id == tenantId && t.IsActive, cancellationToken);
        }

        if (tenant == null)
        {
            throw new NotFoundException("Tenant", "Bulunamadı");
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

        return new GetTenantPublicInfoResponse
        {
            TenantId = tenant.Id,
            Name = tenant.Name,
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
            Country = tenant.Country,
            LogoUrl = tenant.LogoUrl,
            FaviconUrl = tenant.FaviconUrl,
            SiteTitle = tenant.SiteTitle,
            SiteDescription = tenant.SiteDescription,
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
    }
}

