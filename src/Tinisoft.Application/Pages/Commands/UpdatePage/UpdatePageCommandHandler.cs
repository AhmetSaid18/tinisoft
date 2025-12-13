using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Finbuckle.MultiTenant;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Pages.Commands.UpdatePage;

public class UpdatePageCommandHandler : IRequestHandler<UpdatePageCommand, UpdatePageResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<UpdatePageCommandHandler> _logger;

    public UpdatePageCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<UpdatePageCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<UpdatePageResponse> Handle(UpdatePageCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var page = await _dbContext.Set<Page>()
            .FirstOrDefaultAsync(p => p.TenantId == tenantId && p.Id == request.PageId, cancellationToken);

        if (page == null)
        {
            throw new NotFoundException("Page", request.PageId);
        }

        // Sistem sayfası kontrolü
        if (page.IsSystemPage && page.Slug != request.Slug)
        {
            throw new BadRequestException("Sistem sayfalarının slug'ı değiştirilemez.");
        }

        // Slug değişiyorsa kontrol et
        if (page.Slug != request.Slug)
        {
            var slugExists = await _dbContext.Set<Page>()
                .AnyAsync(p => p.TenantId == tenantId && p.Slug == request.Slug && p.Id != request.PageId, cancellationToken);

            if (slugExists)
            {
                throw new BadRequestException($"'{request.Slug}' slug'ı zaten kullanılıyor.");
            }
        }

        // Yayın durumu değişimi
        var wasPublished = page.IsPublished;
        
        page.Title = request.Title;
        page.Slug = request.Slug.ToLowerInvariant().Trim();
        page.Content = request.Content;
        page.MetaTitle = request.MetaTitle ?? request.Title;
        page.MetaDescription = request.MetaDescription;
        page.MetaKeywords = request.MetaKeywords;
        page.FeaturedImageUrl = request.FeaturedImageUrl;
        page.IsPublished = request.IsPublished;
        page.Template = request.Template;
        page.SortOrder = request.SortOrder;
        page.UpdatedAt = DateTime.UtcNow;

        // İlk kez yayınlanıyorsa
        if (!wasPublished && request.IsPublished)
        {
            page.PublishedAt = DateTime.UtcNow;
        }

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Page updated: TenantId={TenantId}, PageId={PageId}, Title={Title}",
            tenantId, page.Id, page.Title);

        return new UpdatePageResponse
        {
            PageId = page.Id,
            Title = page.Title,
            Slug = page.Slug
        };
    }
}

