using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Tax.Commands.UpdateTaxRate;

public class UpdateTaxRateCommandHandler : IRequestHandler<UpdateTaxRateCommand, UpdateTaxRateResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<UpdateTaxRateCommandHandler> _logger;

    public UpdateTaxRateCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<UpdateTaxRateCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<UpdateTaxRateResponse> Handle(UpdateTaxRateCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var taxRate = await _dbContext.Set<Domain.Entities.TaxRate>()
            .FirstOrDefaultAsync(t => t.Id == request.TaxRateId && t.TenantId == tenantId, cancellationToken);

        if (taxRate == null)
        {
            throw new KeyNotFoundException($"Vergi oranı bulunamadı: {request.TaxRateId}");
        }

        // Code değişiyorsa unique kontrolü
        if (taxRate.Code != request.Code)
        {
            var existing = await _dbContext.Set<Domain.Entities.TaxRate>()
                .FirstOrDefaultAsync(t => t.TenantId == tenantId && t.Code == request.Code && t.Id != request.TaxRateId, cancellationToken);

            if (existing != null)
            {
                throw new InvalidOperationException($"Vergi oranı kodu '{request.Code}' zaten kullanılıyor");
            }
        }

        taxRate.Name = request.Name;
        taxRate.Code = request.Code;
        taxRate.Rate = request.Rate;
        taxRate.Type = request.Type;
        taxRate.TaxCode = request.TaxCode;
        taxRate.ExciseTaxCode = request.ExciseTaxCode;
        taxRate.ProductServiceCode = request.ProductServiceCode;
        taxRate.IsIncludedInPrice = request.IsIncludedInPrice;
        taxRate.EInvoiceTaxType = request.EInvoiceTaxType;
        taxRate.IsExempt = request.IsExempt;
        taxRate.ExemptionReason = request.ExemptionReason;
        taxRate.IsActive = request.IsActive;
        taxRate.Description = request.Description;

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Tax rate updated: {TaxRateId} - {Name}", taxRate.Id, taxRate.Name);

        return new UpdateTaxRateResponse
        {
            TaxRateId = taxRate.Id,
            Name = taxRate.Name
        };
    }
}

