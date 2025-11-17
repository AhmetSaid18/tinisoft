using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Tenant.Commands.UpdateTenantSettings;

public class UpdateTenantSettingsCommandHandler : IRequestHandler<UpdateTenantSettingsCommand, UpdateTenantSettingsResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<UpdateTenantSettingsCommandHandler> _logger;

    public UpdateTenantSettingsCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<UpdateTenantSettingsCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<UpdateTenantSettingsResponse> Handle(UpdateTenantSettingsCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var tenant = await _dbContext.Set<Tenant>()
            .FirstOrDefaultAsync(t => t.Id == tenantId, cancellationToken);

        if (tenant == null)
        {
            throw new NotFoundException("Tenant", tenantId);
        }

        // Temel bilgiler
        if (!string.IsNullOrWhiteSpace(request.Name))
        {
            tenant.Name = request.Name;
        }

        // Sosyal medya linkleri (opsiyonel - sadece gönderilenler güncellenir)
        if (request.FacebookUrl != null) tenant.FacebookUrl = request.FacebookUrl;
        if (request.InstagramUrl != null) tenant.InstagramUrl = request.InstagramUrl;
        if (request.TwitterUrl != null) tenant.TwitterUrl = request.TwitterUrl;
        if (request.LinkedInUrl != null) tenant.LinkedInUrl = request.LinkedInUrl;
        if (request.YouTubeUrl != null) tenant.YouTubeUrl = request.YouTubeUrl;
        if (request.TikTokUrl != null) tenant.TikTokUrl = request.TikTokUrl;
        if (request.PinterestUrl != null) tenant.PinterestUrl = request.PinterestUrl;
        if (request.WhatsAppNumber != null) tenant.WhatsAppNumber = request.WhatsAppNumber;
        if (request.TelegramUsername != null) tenant.TelegramUsername = request.TelegramUsername;

        // İletişim bilgileri
        if (request.Email != null) tenant.Email = request.Email;
        if (request.Phone != null) tenant.Phone = request.Phone;
        if (request.Address != null) tenant.Address = request.Address;
        if (request.City != null) tenant.City = request.City;
        if (request.Country != null) tenant.Country = request.Country;

        // E-Ticaret Site Görsel Ayarları
        if (request.LogoUrl != null) tenant.LogoUrl = request.LogoUrl;
        if (request.FaviconUrl != null) tenant.FaviconUrl = request.FaviconUrl;
        if (request.SiteTitle != null) tenant.SiteTitle = request.SiteTitle;
        if (request.SiteDescription != null) tenant.SiteDescription = request.SiteDescription;

        // Tema Renkleri
        if (request.PrimaryColor != null) tenant.PrimaryColor = request.PrimaryColor;
        if (request.SecondaryColor != null) tenant.SecondaryColor = request.SecondaryColor;
        if (request.BackgroundColor != null) tenant.BackgroundColor = request.BackgroundColor;
        if (request.TextColor != null) tenant.TextColor = request.TextColor;
        if (request.LinkColor != null) tenant.LinkColor = request.LinkColor;
        if (request.ButtonColor != null) tenant.ButtonColor = request.ButtonColor;
        if (request.ButtonTextColor != null) tenant.ButtonTextColor = request.ButtonTextColor;

        // Font Ayarları
        if (request.FontFamily != null) tenant.FontFamily = request.FontFamily;
        if (request.HeadingFontFamily != null) tenant.HeadingFontFamily = request.HeadingFontFamily;
        if (request.BaseFontSize.HasValue) tenant.BaseFontSize = request.BaseFontSize;

        tenant.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Tenant settings updated: {TenantId}", tenantId);

        return new UpdateTenantSettingsResponse
        {
            TenantId = tenant.Id,
            Name = tenant.Name,
            Message = "Ayarlar başarıyla güncellendi."
        };
    }
}

