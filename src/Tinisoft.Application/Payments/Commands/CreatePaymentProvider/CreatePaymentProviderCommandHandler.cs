using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Payments.Commands.CreatePaymentProvider;

public class CreatePaymentProviderCommandHandler : IRequestHandler<CreatePaymentProviderCommand, CreatePaymentProviderResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CreatePaymentProviderCommandHandler> _logger;

    public CreatePaymentProviderCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CreatePaymentProviderCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CreatePaymentProviderResponse> Handle(CreatePaymentProviderCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Aynı provider code'un daha önce eklenip eklenmediğini kontrol et
        var existingProvider = await _dbContext.Set<Domain.Entities.PaymentProvider>()
            .FirstOrDefaultAsync(pp => 
                pp.TenantId == tenantId && 
                pp.ProviderCode == request.ProviderCode, cancellationToken);

        if (existingProvider != null)
        {
            throw new InvalidOperationException($"Bu ödeme sağlayıcı zaten eklenmiş: {request.ProviderCode}");
        }

        // Eğer default olarak işaretleniyorsa, diğer provider'ları default'tan çıkar
        if (request.IsDefault)
        {
            var defaultProviders = await _dbContext.Set<Domain.Entities.PaymentProvider>()
                .Where(pp => pp.TenantId == tenantId && pp.IsDefault)
                .ToListAsync(cancellationToken);

            foreach (var provider in defaultProviders)
            {
                provider.IsDefault = false;
            }
        }

        var paymentProvider = new Domain.Entities.PaymentProvider
        {
            TenantId = tenantId,
            ProviderCode = request.ProviderCode.ToUpper(),
            ProviderName = request.ProviderName,
            ApiKey = request.ApiKey,
            ApiSecret = request.ApiSecret,
            ApiUrl = request.ApiUrl,
            TestApiUrl = request.TestApiUrl,
            UseTestMode = request.UseTestMode,
            SettingsJson = request.SettingsJson,
            IsDefault = request.IsDefault,
            Priority = request.Priority,
            IsActive = true
        };

        _dbContext.Set<Domain.Entities.PaymentProvider>().Add(paymentProvider);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Payment provider created: {ProviderCode} for tenant {TenantId}", 
            request.ProviderCode, tenantId);

        return new CreatePaymentProviderResponse
        {
            PaymentProviderId = paymentProvider.Id,
            ProviderCode = paymentProvider.ProviderCode,
            ProviderName = paymentProvider.ProviderName
        };
    }
}

