using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Tax.Commands.DeleteTaxRate;

public class DeleteTaxRateCommandHandler : IRequestHandler<DeleteTaxRateCommand, Unit>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<DeleteTaxRateCommandHandler> _logger;

    public DeleteTaxRateCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<DeleteTaxRateCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<Unit> Handle(DeleteTaxRateCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var taxRate = await _dbContext.Set<Domain.Entities.TaxRate>()
            .FirstOrDefaultAsync(t => t.Id == request.TaxRateId && t.TenantId == tenantId, cancellationToken);

        if (taxRate == null)
        {
            throw new KeyNotFoundException($"Vergi oranı bulunamadı: {request.TaxRateId}");
        }

        // Kullanılıyor mu kontrol et
        var isUsed = await _dbContext.Products
            .AnyAsync(p => p.TaxRateId == request.TaxRateId, cancellationToken) ||
            await _dbContext.Set<Domain.Entities.TaxRule>()
            .AnyAsync(tr => tr.TaxRateId == request.TaxRateId, cancellationToken);

        if (isUsed)
        {
            // Silme yerine pasif yap
            taxRate.IsActive = false;
            _logger.LogWarning("Tax rate {TaxRateId} is in use, deactivating instead of deleting", request.TaxRateId);
        }
        else
        {
            _dbContext.Set<Domain.Entities.TaxRate>().Remove(taxRate);
        }

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Tax rate deleted/deactivated: {TaxRateId}", request.TaxRateId);

        return Unit.Value;
    }
}

