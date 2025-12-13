using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Finbuckle.MultiTenant;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;

namespace Tinisoft.Application.Pages.Queries.GetPages;

public class GetPagesQueryHandler : IRequestHandler<GetPagesQuery, GetPagesResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetPagesQueryHandler> _logger;

    public GetPagesQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetPagesQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetPagesResponse> Handle(GetPagesQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var query = _dbContext.Set<Page>()
            .Where(p => p.TenantId == tenantId);

        // Filtreler
        if (request.IsPublished.HasValue)
        {
            query = query.Where(p => p.IsPublished == request.IsPublished.Value);
        }

        if (!string.IsNullOrWhiteSpace(request.SearchTerm))
        {
            var term = request.SearchTerm.ToLower();
            query = query.Where(p => 
                p.Title.ToLower().Contains(term) || 
                p.Slug.ToLower().Contains(term));
        }

        var totalCount = await query.CountAsync(cancellationToken);

        var pages = await query
            .OrderBy(p => p.SortOrder)
            .ThenByDescending(p => p.CreatedAt)
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
            .Select(p => new PageDto
            {
                Id = p.Id,
                Title = p.Title,
                Slug = p.Slug,
                MetaTitle = p.MetaTitle,
                MetaDescription = p.MetaDescription,
                FeaturedImageUrl = p.FeaturedImageUrl,
                IsPublished = p.IsPublished,
                PublishedAt = p.PublishedAt,
                Template = p.Template,
                SortOrder = p.SortOrder,
                IsSystemPage = p.IsSystemPage,
                SystemPageType = p.SystemPageType,
                CreatedAt = p.CreatedAt,
                UpdatedAt = p.UpdatedAt
            })
            .ToListAsync(cancellationToken);

        return new GetPagesResponse
        {
            Pages = pages,
            TotalCount = totalCount,
            Page = request.Page,
            PageSize = request.PageSize,
            TotalPages = (int)Math.Ceiling((double)totalCount / request.PageSize)
        };
    }
}

