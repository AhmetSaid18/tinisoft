using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Finbuckle.MultiTenant;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Navigation.Commands.DeleteMenuItem;

public class DeleteMenuItemCommandHandler : IRequestHandler<DeleteMenuItemCommand, DeleteMenuItemResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<DeleteMenuItemCommandHandler> _logger;

    public DeleteMenuItemCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<DeleteMenuItemCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<DeleteMenuItemResponse> Handle(DeleteMenuItemCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var menuItem = await _dbContext.Set<NavigationMenu>()
            .Include(nm => nm.Children)
            .FirstOrDefaultAsync(nm => nm.TenantId == tenantId && nm.Id == request.MenuItemId, cancellationToken);

        if (menuItem == null)
        {
            throw new NotFoundException("NavigationMenu", request.MenuItemId);
        }

        // Alt menüler varsa onları da sil (veya üst seviyeye taşı)
        if (menuItem.Children.Any())
        {
            foreach (var child in menuItem.Children)
            {
                child.ParentId = null; // Alt menüleri üst seviyeye taşı
            }
        }

        _dbContext.Set<NavigationMenu>().Remove(menuItem);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("NavigationMenu deleted: TenantId={TenantId}, MenuItemId={MenuItemId}",
            tenantId, request.MenuItemId);

        return new DeleteMenuItemResponse
        {
            MenuItemId = request.MenuItemId
        };
    }
}

