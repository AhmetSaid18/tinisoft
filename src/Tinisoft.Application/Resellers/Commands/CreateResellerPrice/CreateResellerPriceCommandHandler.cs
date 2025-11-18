using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Resellers.Commands.CreateResellerPrice;

public class CreateResellerPriceCommandHandler : IRequestHandler<CreateResellerPriceCommand, CreateResellerPriceResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CreateResellerPriceCommandHandler> _logger;

    public CreateResellerPriceCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CreateResellerPriceCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CreateResellerPriceResponse> Handle(CreateResellerPriceCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Reseller kontrolü
        var reseller = await _dbContext.Resellers
            .FirstOrDefaultAsync(r => r.Id == request.ResellerId && r.TenantId == tenantId, cancellationToken);

        if (reseller == null)
        {
            throw new KeyNotFoundException($"Reseller bulunamadı: {request.ResellerId}");
        }

        // Product kontrolü
        var product = await _dbContext.Products
            .FirstOrDefaultAsync(p => p.Id == request.ProductId && p.TenantId == tenantId, cancellationToken);

        if (product == null)
        {
            throw new KeyNotFoundException($"Product bulunamadı: {request.ProductId}");
        }

        // Aynı reseller + product + minQuantity kombinasyonu var mı kontrol et
        var existingPrice = await _dbContext.ResellerPrices
            .FirstOrDefaultAsync(rp => 
                rp.ResellerId == request.ResellerId && 
                rp.ProductId == request.ProductId && 
                rp.MinQuantity == request.MinQuantity &&
                rp.TenantId == tenantId, 
                cancellationToken);

        if (existingPrice != null)
        {
            throw new InvalidOperationException(
                $"Bu reseller ve ürün için zaten bir fiyat tanımlı (MinQuantity: {request.MinQuantity})");
        }

        var resellerPrice = new ResellerPrice
        {
            TenantId = tenantId,
            ResellerId = request.ResellerId,
            ProductId = request.ProductId,
            Price = request.Price,
            CompareAtPrice = request.CompareAtPrice,
            Currency = request.Currency,
            MinQuantity = request.MinQuantity,
            MaxQuantity = request.MaxQuantity,
            IsActive = true,
            ValidFrom = request.ValidFrom,
            ValidUntil = request.ValidUntil,
            Notes = request.Notes
        };

        _dbContext.ResellerPrices.Add(resellerPrice);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Reseller price created: ResellerId={ResellerId}, ProductId={ProductId}, Price={Price}",
            request.ResellerId, request.ProductId, request.Price);

        return new CreateResellerPriceResponse
        {
            ResellerPriceId = resellerPrice.Id,
            ResellerId = resellerPrice.ResellerId,
            ProductId = resellerPrice.ProductId,
            Price = resellerPrice.Price
        };
    }
}

