using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Tax.Queries.GetTaxRates;

public class GetTaxRatesQueryHandler : IRequestHandler<GetTaxRatesQuery, List<TaxRateDto>>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;

    public GetTaxRatesQueryHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
    }

    public async Task<List<TaxRateDto>> Handle(GetTaxRatesQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var query = _dbContext.Set<Domain.Entities.TaxRate>()
            .Where(tr => tr.TenantId == tenantId)
            .AsQueryable();

        if (request.IsActive.HasValue)
        {
            query = query.Where(tr => tr.IsActive == request.IsActive.Value);
        }

        var taxRates = await query
            .OrderBy(tr => tr.Name)
            .Select(tr => new TaxRateDto
            {
                Id = tr.Id,
                Name = tr.Name,
                Code = tr.Code,
                Rate = tr.Rate,
                Type = tr.Type,
                TaxCode = tr.TaxCode,
                ExciseTaxCode = tr.ExciseTaxCode,
                ProductServiceCode = tr.ProductServiceCode,
                IsIncludedInPrice = tr.IsIncludedInPrice,
                EInvoiceTaxType = tr.EInvoiceTaxType,
                IsExempt = tr.IsExempt,
                ExemptionReason = tr.ExemptionReason,
                IsActive = tr.IsActive,
                Description = tr.Description
            })
            .ToListAsync(cancellationToken);

        return taxRates;
    }
}

