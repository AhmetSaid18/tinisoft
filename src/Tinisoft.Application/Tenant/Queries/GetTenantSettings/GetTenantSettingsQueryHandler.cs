using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Tenant.Queries.GetTenantSettings;

public class GetTenantSettingsQueryHandler : IRequestHandler<GetTenantSettingsQuery, GetTenantSettingsResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetTenantSettingsQueryHandler> _logger;

    public GetTenantSettingsQueryHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetTenantSettingsQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetTenantSettingsResponse> Handle(GetTenantSettingsQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var tenant = await _dbContext.Set<Tenant>()
            .FirstOrDefaultAsync(t => t.Id == tenantId, cancellationToken);

        if (tenant == null)
        {
            throw new NotFoundException("Tenant", tenantId);
        }

        return new GetTenantSettingsResponse
        {
            TenantId = tenant.Id,
            Name = tenant.Name,
            Slug = tenant.Slug,
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
            BaseFontSize = tenant.BaseFontSize
        };
    }
}

