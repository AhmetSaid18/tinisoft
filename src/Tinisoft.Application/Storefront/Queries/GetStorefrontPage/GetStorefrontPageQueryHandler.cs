using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Finbuckle.MultiTenant;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;

namespace Tinisoft.Application.Storefront.Queries.GetStorefrontPage;

public class GetStorefrontPageQueryHandler : IRequestHandler<GetStorefrontPageQuery, GetStorefrontPageResponse?>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetStorefrontPageQueryHandler> _logger;

    public GetStorefrontPageQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetStorefrontPageQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetStorefrontPageResponse?> Handle(GetStorefrontPageQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var page = await _dbContext.Set<Page>()
            .Where(p => p.TenantId == tenantId && p.Slug == request.Slug.ToLower() && p.IsPublished)
            .Select(p => new GetStorefrontPageResponse
            {
                Title = p.Title,
                Slug = p.Slug,
                Content = p.Content,
                MetaTitle = p.MetaTitle,
                MetaDescription = p.MetaDescription,
                MetaKeywords = p.MetaKeywords,
                CanonicalUrl = p.CanonicalUrl,
                FeaturedImageUrl = p.FeaturedImageUrl,
                Template = p.Template
            })
            .FirstOrDefaultAsync(cancellationToken);

        return page;
    }
}

