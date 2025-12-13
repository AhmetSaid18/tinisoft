using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Finbuckle.MultiTenant;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;

namespace Tinisoft.Application.Storefront.Queries.GetStorefrontNavigation;

public class GetStorefrontNavigationQueryHandler : IRequestHandler<GetStorefrontNavigationQuery, GetStorefrontNavigationResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetStorefrontNavigationQueryHandler> _logger;

    public GetStorefrontNavigationQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetStorefrontNavigationQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetStorefrontNavigationResponse> Handle(GetStorefrontNavigationQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var allItems = await _dbContext.Set<NavigationMenu>()
            .Where(nm => nm.TenantId == tenantId && nm.IsVisible)
            .OrderBy(nm => nm.SortOrder)
            .ToListAsync(cancellationToken);

        var response = new GetStorefrontNavigationResponse
        {
            Header = BuildMenuTree(allItems, NavigationLocation.Header),
            Footer = BuildMenuTree(allItems, NavigationLocation.Footer),
            Mobile = BuildMenuTree(allItems, NavigationLocation.MobileMenu)
        };

        return response;
    }

    private List<StorefrontMenuItemDto> BuildMenuTree(List<NavigationMenu> allItems, NavigationLocation location)
    {
        var locationItems = allItems.Where(x => x.Location == location).ToList();
        var rootItems = locationItems.Where(x => x.ParentId == null).ToList();

        return rootItems.Select(item => MapToDto(item, locationItems)).ToList();
    }

    private StorefrontMenuItemDto MapToDto(NavigationMenu item, List<NavigationMenu> allItems)
    {
        var dto = new StorefrontMenuItemDto
        {
            Title = item.Title,
            Url = item.Url ?? "#",
            OpenInNewTab = item.OpenInNewTab,
            Icon = item.Icon,
            Children = allItems
                .Where(x => x.ParentId == item.Id)
                .Select(child => MapToDto(child, allItems))
                .ToList()
        };

        return dto;
    }
}

