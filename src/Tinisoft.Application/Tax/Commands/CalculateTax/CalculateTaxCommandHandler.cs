using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Tax.Commands.CalculateTax;

public class CalculateTaxCommandHandler : IRequestHandler<CalculateTaxCommand, CalculateTaxResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CalculateTaxCommandHandler> _logger;

    public CalculateTaxCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CalculateTaxCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CalculateTaxResponse> Handle(CalculateTaxCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);
        var subtotal = request.Price * request.Quantity;
        var taxDetails = new List<TaxDetailDto>();
        var totalTaxAmount = 0m;

        // 1. Önce ürünün kendi vergi oranını kontrol et
        TaxRate? taxRate = null;
        
        if (request.TaxRateId.HasValue)
        {
            // Manuel vergi oranı seçilmişse
            taxRate = await _dbContext.Set<TaxRate>()
                .FirstOrDefaultAsync(t => t.Id == request.TaxRateId.Value && 
                                          t.TenantId == tenantId && 
                                          t.IsActive, cancellationToken);
        }
        else if (request.ProductId.HasValue)
        {
            // Ürünün vergi oranını al
            var product = await _dbContext.Products
                .Include(p => p.TaxRate)
                .FirstOrDefaultAsync(p => p.Id == request.ProductId.Value && 
                                        p.TenantId == tenantId, cancellationToken);

            if (product?.ChargeTaxes == true && product.TaxRateId.HasValue)
            {
                taxRate = product.TaxRate;
            }
        }

        // 2. Eğer ürün vergi oranı yoksa, TaxRule'lardan bul
        if (taxRate == null)
        {
            var taxRules = await _dbContext.Set<TaxRule>()
                .Include(tr => tr.TaxRate)
                .Where(tr => tr.TenantId == tenantId && 
                            tr.IsActive &&
                            tr.TaxRate != null &&
                            tr.TaxRate.IsActive)
                .OrderByDescending(tr => tr.Priority)
                .ToListAsync(cancellationToken);

            foreach (var rule in taxRules)
            {
                // Koşulları kontrol et
                bool matches = true;

                // Ürün kontrolü
                if (rule.ProductId.HasValue && request.ProductId != rule.ProductId.Value)
                {
                    matches = false;
                    continue;
                }

                // Kategori kontrolü
                if (rule.CategoryId.HasValue && request.CategoryId != rule.CategoryId.Value)
                {
                    matches = false;
                    continue;
                }

                // Fiyat kontrolü
                if (rule.MinPrice.HasValue && request.Price < rule.MinPrice.Value)
                {
                    matches = false;
                    continue;
                }

                if (rule.MaxPrice.HasValue && request.Price > rule.MaxPrice.Value)
                {
                    matches = false;
                    continue;
                }

                // Ülke kontrolü
                if (!string.IsNullOrEmpty(rule.CountryCode) && 
                    !string.IsNullOrEmpty(request.CountryCode) &&
                    rule.CountryCode != request.CountryCode)
                {
                    matches = false;
                    continue;
                }

                // Bölge kontrolü
                if (!string.IsNullOrEmpty(rule.Region) && 
                    !string.IsNullOrEmpty(request.Region) &&
                    rule.Region != request.Region)
                {
                    matches = false;
                    continue;
                }

                if (matches)
                {
                    taxRate = rule.TaxRate;
                    break;
                }
            }
        }

        // 3. Varsayılan vergi oranı (KDV %20 - Türkiye standart)
        if (taxRate == null)
        {
            taxRate = await _dbContext.Set<TaxRate>()
                .FirstOrDefaultAsync(t => t.TenantId == tenantId && 
                                         t.Code == "KDV20" && 
                                         t.IsActive, cancellationToken);

            // Eğer yoksa oluştur
            if (taxRate == null)
            {
                taxRate = new Domain.Entities.TaxRate
                {
                    TenantId = tenantId,
                    Name = "KDV %20",
                    Code = "KDV20",
                    Rate = 20.00m,
                    Type = "VAT",
                    TaxCode = "001",
                    IsIncludedInPrice = false,
                    IsActive = true
                };
                _dbContext.Set<Domain.Entities.TaxRate>().Add(taxRate);
                await _dbContext.SaveChangesAsync(cancellationToken);
            }
        }

        // 4. Vergi hesapla
        if (taxRate != null)
        {
            var taxAmount = subtotal * (taxRate.Rate / 100m);
            totalTaxAmount = taxAmount;

            taxDetails.Add(new TaxDetailDto
            {
                TaxRateId = taxRate.Id,
                TaxName = taxRate.Name,
                TaxCode = taxRate.Code,
                Rate = taxRate.Rate,
                TaxableAmount = subtotal,
                TaxAmount = taxAmount,
                Type = taxRate.Type
            });
        }

        return new CalculateTaxResponse
        {
            Subtotal = subtotal,
            TaxAmount = totalTaxAmount,
            Total = subtotal + totalTaxAmount,
            TaxDetails = taxDetails
        };
    }
}

