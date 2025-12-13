using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Finbuckle.MultiTenant;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;

namespace Tinisoft.Application.Navigation.Queries.GetNavigation;

public class GetNavigationQueryHandler : IRequestHandler<GetNavigationQuery, GetNavigationResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetNavigationQueryHandler> _logger;

    public GetNavigationQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetNavigationQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetNavigationResponse> Handle(GetNavigationQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var query = _dbContext.Set<NavigationMenu>()
            .Where(nm => nm.TenantId == tenantId);

        if (request.Location.HasValue)
        {
            query = query.Where(nm => nm.Location == request.Location.Value);
        }

        if (request.OnlyVisible)
        {
            query = query.Where(nm => nm.IsVisible);
        }

        var allItems = await query
            .OrderBy(nm => nm.SortOrder)
            .Select(nm => new NavigationMenuDto
            {
                Id = nm.Id,
                Title = nm.Title,
                Url = nm.Url,
                ItemType = nm.ItemType.ToString().ToLower(),
                PageId = nm.PageId,
                CategoryId = nm.CategoryId,
                ProductId = nm.ProductId,
                ParentId = nm.ParentId,
                Location = nm.Location.ToString().ToLower(),
                SortOrder = nm.SortOrder,
                IsVisible = nm.IsVisible,
                OpenInNewTab = nm.OpenInNewTab,
                Icon = nm.Icon,
                CssClass = nm.CssClass
            })
            .ToListAsync(cancellationToken);

        // Hiyerarşik yapı oluştur
        var rootItems = allItems.Where(x => x.ParentId == null).ToList();
        
        foreach (var item in rootItems)
        {
            BuildChildren(item, allItems);
        }

        return new GetNavigationResponse
        {
            MenuItems = rootItems
        };
    }

    private void BuildChildren(NavigationMenuDto parent, List<NavigationMenuDto> allItems)
    {
        parent.Children = allItems.Where(x => x.ParentId == parent.Id).ToList();
        
        foreach (var child in parent.Children)
        {
            BuildChildren(child, allItems);
        }
    }
}

