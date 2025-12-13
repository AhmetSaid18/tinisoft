using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Finbuckle.MultiTenant;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Navigation.Commands.CreateMenuItem;

public class CreateMenuItemCommandHandler : IRequestHandler<CreateMenuItemCommand, CreateMenuItemResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CreateMenuItemCommandHandler> _logger;

    public CreateMenuItemCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CreateMenuItemCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CreateMenuItemResponse> Handle(CreateMenuItemCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Parent kontrolü
        if (request.ParentId.HasValue)
        {
            var parentExists = await _dbContext.Set<NavigationMenu>()
                .AnyAsync(nm => nm.TenantId == tenantId && nm.Id == request.ParentId.Value, cancellationToken);

            if (!parentExists)
            {
                throw new NotFoundException("Parent NavigationMenu", request.ParentId.Value);
            }
        }

        // URL oluştur (tip'e göre)
        var url = request.Url;
        
        if (request.ItemType == NavigationItemType.Page && request.PageId.HasValue)
        {
            var page = await _dbContext.Set<Page>()
                .FirstOrDefaultAsync(p => p.TenantId == tenantId && p.Id == request.PageId.Value, cancellationToken);
            if (page != null)
            {
                url = $"/{page.Slug}";
            }
        }
        else if (request.ItemType == NavigationItemType.Category && request.CategoryId.HasValue)
        {
            var category = await _dbContext.Set<Category>()
                .FirstOrDefaultAsync(c => c.TenantId == tenantId && c.Id == request.CategoryId.Value, cancellationToken);
            if (category != null)
            {
                url = $"/kategori/{category.Slug}";
            }
        }
        else if (request.ItemType == NavigationItemType.Product && request.ProductId.HasValue)
        {
            var product = await _dbContext.Set<Product>()
                .FirstOrDefaultAsync(p => p.TenantId == tenantId && p.Id == request.ProductId.Value, cancellationToken);
            if (product != null)
            {
                url = $"/urun/{product.Slug}";
            }
        }
        else if (request.ItemType == NavigationItemType.Home)
        {
            url = "/";
        }
        else if (request.ItemType == NavigationItemType.AllProducts)
        {
            url = "/urunler";
        }
        else if (request.ItemType == NavigationItemType.AllCategories)
        {
            url = "/kategoriler";
        }
        else if (request.ItemType == NavigationItemType.Cart)
        {
            url = "/sepet";
        }
        else if (request.ItemType == NavigationItemType.Account)
        {
            url = "/hesabim";
        }

        var menuItem = new NavigationMenu
        {
            TenantId = tenantId,
            Title = request.Title,
            Url = url,
            ItemType = request.ItemType,
            PageId = request.PageId,
            CategoryId = request.CategoryId,
            ProductId = request.ProductId,
            ParentId = request.ParentId,
            Location = request.Location,
            SortOrder = request.SortOrder,
            IsVisible = true,
            OpenInNewTab = request.OpenInNewTab,
            Icon = request.Icon,
            CssClass = request.CssClass
        };

        _dbContext.Set<NavigationMenu>().Add(menuItem);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("NavigationMenu created: TenantId={TenantId}, MenuItemId={MenuItemId}, Title={Title}",
            tenantId, menuItem.Id, menuItem.Title);

        return new CreateMenuItemResponse
        {
            MenuItemId = menuItem.Id,
            Title = menuItem.Title
        };
    }
}

