using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Finbuckle.MultiTenant;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Pages.Commands.CreatePage;

public class CreatePageCommandHandler : IRequestHandler<CreatePageCommand, CreatePageResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CreatePageCommandHandler> _logger;

    public CreatePageCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CreatePageCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CreatePageResponse> Handle(CreatePageCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Slug kontrolü
        var slugExists = await _dbContext.Set<Page>()
            .AnyAsync(p => p.TenantId == tenantId && p.Slug == request.Slug, cancellationToken);

        if (slugExists)
        {
            throw new BadRequestException($"'{request.Slug}' slug'ı zaten kullanılıyor.");
        }

        var page = new Page
        {
            TenantId = tenantId,
            Title = request.Title,
            Slug = request.Slug.ToLowerInvariant().Trim(),
            Content = request.Content,
            MetaTitle = request.MetaTitle ?? request.Title,
            MetaDescription = request.MetaDescription,
            MetaKeywords = request.MetaKeywords,
            FeaturedImageUrl = request.FeaturedImageUrl,
            IsPublished = request.IsPublished,
            PublishedAt = request.IsPublished ? DateTime.UtcNow : null,
            Template = request.Template,
            SortOrder = request.SortOrder
        };

        _dbContext.Set<Page>().Add(page);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Page created: TenantId={TenantId}, PageId={PageId}, Title={Title}",
            tenantId, page.Id, page.Title);

        return new CreatePageResponse
        {
            PageId = page.Id,
            Title = page.Title,
            Slug = page.Slug
        };
    }
}

