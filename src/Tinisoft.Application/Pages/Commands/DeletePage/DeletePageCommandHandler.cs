using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Finbuckle.MultiTenant;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Pages.Commands.DeletePage;

public class DeletePageCommandHandler : IRequestHandler<DeletePageCommand, DeletePageResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<DeletePageCommandHandler> _logger;

    public DeletePageCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<DeletePageCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<DeletePageResponse> Handle(DeletePageCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var page = await _dbContext.Set<Page>()
            .FirstOrDefaultAsync(p => p.TenantId == tenantId && p.Id == request.PageId, cancellationToken);

        if (page == null)
        {
            throw new NotFoundException("Page", request.PageId);
        }

        // Sistem sayfası silinemez
        if (page.IsSystemPage)
        {
            throw new BadRequestException("Sistem sayfaları silinemez.");
        }

        // Bu sayfaya bağlı menü öğeleri varsa uyar
        var hasMenuItems = await _dbContext.Set<NavigationMenu>()
            .AnyAsync(nm => nm.TenantId == tenantId && nm.PageId == request.PageId, cancellationToken);

        if (hasMenuItems)
        {
            // Menü öğelerinin PageId'sini null yap
            var menuItems = await _dbContext.Set<NavigationMenu>()
                .Where(nm => nm.TenantId == tenantId && nm.PageId == request.PageId)
                .ToListAsync(cancellationToken);

            foreach (var item in menuItems)
            {
                item.PageId = null;
                item.ItemType = NavigationItemType.Link;
                item.Url = $"/{page.Slug}"; // Eski URL'yi koru
            }
        }

        _dbContext.Set<Page>().Remove(page);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Page deleted: TenantId={TenantId}, PageId={PageId}",
            tenantId, request.PageId);

        return new DeletePageResponse
        {
            PageId = request.PageId
        };
    }
}

