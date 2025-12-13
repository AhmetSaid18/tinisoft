using MediatR;
using Microsoft.EntityFrameworkCore;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Interfaces;

namespace Tinisoft.Application.Tenant.Commands.RemoveDomain;

public class RemoveDomainCommandHandler : IRequestHandler<RemoveDomainCommand, RemoveDomainResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ITraefikDomainService _traefikDomainService;
    private readonly ILogger<RemoveDomainCommandHandler> _logger;

    public RemoveDomainCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ITraefikDomainService traefikDomainService,
        ILogger<RemoveDomainCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _traefikDomainService = traefikDomainService;
        _logger = logger;
    }

    public async Task<RemoveDomainResponse> Handle(RemoveDomainCommand request, CancellationToken cancellationToken)
    {
        try
        {
            var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

            // Domain'i bul
            var domain = await _dbContext.Domains
                .FirstOrDefaultAsync(d => d.Id == request.DomainId && d.TenantId == tenantId, cancellationToken);

            if (domain == null)
            {
                return new RemoveDomainResponse
                {
                    Success = false,
                    Message = "Domain not found"
                };
            }

            // Traefik'ten domain'i kaldır
            await _traefikDomainService.RemoveDomainAsync(domain.Host, cancellationToken);

            // Database'den sil
            _dbContext.Domains.Remove(domain);
            await _dbContext.SaveChangesAsync(cancellationToken);

            _logger.LogInformation("Domain {Host} removed for tenant {TenantId}", domain.Host, tenantId);

            return new RemoveDomainResponse
            {
                Success = true,
                Message = "Domain removed successfully"
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error removing domain {DomainId}", request.DomainId);
            return new RemoveDomainResponse
            {
                Success = false,
                Message = $"Error removing domain: {ex.Message}"
            };
        }
    }
}

