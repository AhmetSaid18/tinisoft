using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Tax.Commands.CreateTaxRate;

public class CreateTaxRateCommandHandler : IRequestHandler<CreateTaxRateCommand, CreateTaxRateResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CreateTaxRateCommandHandler> _logger;

    public CreateTaxRateCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CreateTaxRateCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CreateTaxRateResponse> Handle(CreateTaxRateCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Code'un unique olduğunu kontrol et
        var existing = await _dbContext.Set<Entities.TaxRate>()
            .FirstOrDefaultAsync(t => t.TenantId == tenantId && t.Code == request.Code, cancellationToken);

        if (existing != null)
        {
            throw new InvalidOperationException($"Vergi oranı kodu '{request.Code}' zaten kullanılıyor");
        }

        var taxRate = new Entities.TaxRate
        {
            TenantId = tenantId,
            Name = request.Name,
            Code = request.Code,
            Rate = request.Rate,
            Type = request.Type,
            TaxCode = request.TaxCode,
            ExciseTaxCode = request.ExciseTaxCode,
            ProductServiceCode = request.ProductServiceCode,
            IsIncludedInPrice = request.IsIncludedInPrice,
            EInvoiceTaxType = request.EInvoiceTaxType,
            IsExempt = request.IsExempt,
            ExemptionReason = request.ExemptionReason,
            Description = request.Description,
            IsActive = true
        };

        _dbContext.Set<Entities.TaxRate>().Add(taxRate);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Tax rate created: {TaxRateId} - {Name} ({Code})", taxRate.Id, taxRate.Name, taxRate.Code);

        return new CreateTaxRateResponse
        {
            TaxRateId = taxRate.Id,
            Name = taxRate.Name
        };
    }
}



