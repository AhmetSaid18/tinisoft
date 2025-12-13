using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Payments.Commands.UpdatePaymentProvider;

public class UpdatePaymentProviderCommandHandler : IRequestHandler<UpdatePaymentProviderCommand, UpdatePaymentProviderResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<UpdatePaymentProviderCommandHandler> _logger;

    public UpdatePaymentProviderCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<UpdatePaymentProviderCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<UpdatePaymentProviderResponse> Handle(UpdatePaymentProviderCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var provider = await _dbContext.Set<Domain.Entities.PaymentProvider>()
            .FirstOrDefaultAsync(pp => 
                pp.Id == request.PaymentProviderId && 
                pp.TenantId == tenantId, cancellationToken);

        if (provider == null)
        {
            throw new KeyNotFoundException($"Ödeme sağlayıcı bulunamadı: {request.PaymentProviderId}");
        }

        // Eğer default olarak işaretleniyorsa, diğer provider'ları default'tan çıkar
        if (request.IsDefault == true && !provider.IsDefault)
        {
            var defaultProviders = await _dbContext.Set<Domain.Entities.PaymentProvider>()
                .Where(pp => pp.TenantId == tenantId && pp.IsDefault && pp.Id != request.PaymentProviderId)
                .ToListAsync(cancellationToken);

            foreach (var p in defaultProviders)
            {
                p.IsDefault = false;
            }
        }

        // Update fields
        if (request.ProviderName != null)
            provider.ProviderName = request.ProviderName;
        if (request.ApiKey != null)
            provider.ApiKey = request.ApiKey;
        if (request.ApiSecret != null)
            provider.ApiSecret = request.ApiSecret;
        if (request.ApiUrl != null)
            provider.ApiUrl = request.ApiUrl;
        if (request.TestApiUrl != null)
            provider.TestApiUrl = request.TestApiUrl;
        if (request.UseTestMode.HasValue)
            provider.UseTestMode = request.UseTestMode.Value;
        if (request.SettingsJson != null)
            provider.SettingsJson = request.SettingsJson;
        if (request.IsActive.HasValue)
            provider.IsActive = request.IsActive.Value;
        if (request.IsDefault.HasValue)
            provider.IsDefault = request.IsDefault.Value;
        if (request.Priority.HasValue)
            provider.Priority = request.Priority.Value;

        provider.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Payment provider updated: {ProviderCode} for tenant {TenantId}", 
            provider.ProviderCode, tenantId);

        return new UpdatePaymentProviderResponse
        {
            PaymentProviderId = provider.Id,
            ProviderCode = provider.ProviderCode,
            ProviderName = provider.ProviderName
        };
    }
}

