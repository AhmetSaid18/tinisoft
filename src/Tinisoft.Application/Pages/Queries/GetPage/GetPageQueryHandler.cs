using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Finbuckle.MultiTenant;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Pages.Queries.GetPage;

public class GetPageQueryHandler : IRequestHandler<GetPageQuery, GetPageResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetPageQueryHandler> _logger;

    public GetPageQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetPageQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetPageResponse> Handle(GetPageQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        Page? page = null;

        if (request.PageId.HasValue)
        {
            page = await _dbContext.Set<Page>()
                .FirstOrDefaultAsync(p => p.TenantId == tenantId && p.Id == request.PageId.Value, cancellationToken);
        }
        else if (!string.IsNullOrWhiteSpace(request.Slug))
        {
            page = await _dbContext.Set<Page>()
                .FirstOrDefaultAsync(p => p.TenantId == tenantId && p.Slug == request.Slug.ToLower(), cancellationToken);
        }

        if (page == null)
        {
            throw new NotFoundException("Page", request.PageId?.ToString() ?? request.Slug ?? "unknown");
        }

        return new GetPageResponse
        {
            Id = page.Id,
            Title = page.Title,
            Slug = page.Slug,
            Content = page.Content,
            MetaTitle = page.MetaTitle,
            MetaDescription = page.MetaDescription,
            MetaKeywords = page.MetaKeywords,
            CanonicalUrl = page.CanonicalUrl,
            FeaturedImageUrl = page.FeaturedImageUrl,
            IsPublished = page.IsPublished,
            PublishedAt = page.PublishedAt,
            Template = page.Template,
            SortOrder = page.SortOrder,
            IsSystemPage = page.IsSystemPage,
            SystemPageType = page.SystemPageType,
            CreatedAt = page.CreatedAt,
            UpdatedAt = page.UpdatedAt
        };
    }
}

