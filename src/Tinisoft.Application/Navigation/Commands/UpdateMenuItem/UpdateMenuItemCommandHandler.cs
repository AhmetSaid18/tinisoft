using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Finbuckle.MultiTenant;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Navigation.Commands.UpdateMenuItem;

public class UpdateMenuItemCommandHandler : IRequestHandler<UpdateMenuItemCommand, UpdateMenuItemResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<UpdateMenuItemCommandHandler> _logger;

    public UpdateMenuItemCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<UpdateMenuItemCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<UpdateMenuItemResponse> Handle(UpdateMenuItemCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var menuItem = await _dbContext.Set<NavigationMenu>()
            .FirstOrDefaultAsync(nm => nm.TenantId == tenantId && nm.Id == request.MenuItemId, cancellationToken);

        if (menuItem == null)
        {
            throw new NotFoundException("NavigationMenu", request.MenuItemId);
        }

        // Parent kontrolü (kendisi olamaz)
        if (request.ParentId.HasValue && request.ParentId.Value == request.MenuItemId)
        {
            throw new BadRequestException("Bir menü öğesi kendisinin alt öğesi olamaz.");
        }

        menuItem.Title = request.Title;
        menuItem.Url = request.Url;
        menuItem.ItemType = request.ItemType;
        menuItem.PageId = request.PageId;
        menuItem.CategoryId = request.CategoryId;
        menuItem.ProductId = request.ProductId;
        menuItem.ParentId = request.ParentId;
        menuItem.Location = request.Location;
        menuItem.SortOrder = request.SortOrder;
        menuItem.IsVisible = request.IsVisible;
        menuItem.OpenInNewTab = request.OpenInNewTab;
        menuItem.Icon = request.Icon;
        menuItem.CssClass = request.CssClass;
        menuItem.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("NavigationMenu updated: TenantId={TenantId}, MenuItemId={MenuItemId}",
            tenantId, menuItem.Id);

        return new UpdateMenuItemResponse
        {
            MenuItemId = menuItem.Id,
            Title = menuItem.Title
        };
    }
}

