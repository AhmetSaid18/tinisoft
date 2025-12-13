using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Payments.Services;
using Tinisoft.Shared.Contracts;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Payments.Commands.VerifyPayment;

public class VerifyPaymentCommandHandler : IRequestHandler<VerifyPaymentCommand, VerifyPaymentResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IPaymentServiceFactory _paymentServiceFactory;
    private readonly IEventBus _eventBus;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<VerifyPaymentCommandHandler> _logger;

    public VerifyPaymentCommandHandler(
        IApplicationDbContext dbContext,
        IPaymentServiceFactory paymentServiceFactory,
        IEventBus eventBus,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<VerifyPaymentCommandHandler> logger)
    {
        _dbContext = dbContext;
        _paymentServiceFactory = paymentServiceFactory;
        _eventBus = eventBus;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<VerifyPaymentResponse> Handle(VerifyPaymentCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var order = await _dbContext.Orders
            .FirstOrDefaultAsync(o => 
                o.Id == request.OrderId && 
                o.TenantId == tenantId, cancellationToken);

        if (order == null)
        {
            return new VerifyPaymentResponse
            {
                IsValid = false,
                ErrorMessage = "Sipariş bulunamadı"
            };
        }

        if (string.IsNullOrEmpty(order.PaymentProvider))
        {
            return new VerifyPaymentResponse
            {
                IsValid = false,
                ErrorMessage = "Sipariş için ödeme sağlayıcı belirtilmemiş"
            };
        }

        // Tenant'ın ödeme sağlayıcı bilgilerini database'den al
        var providerCode = order.PaymentProvider.ToUpper();
        var provider = await _dbContext.Set<PaymentProvider>()
            .FirstOrDefaultAsync(p => 
                p.TenantId == tenantId && 
                p.ProviderCode == providerCode && 
                p.IsActive, cancellationToken);

        if (provider == null)
        {
            return new VerifyPaymentResponse
            {
                IsValid = false,
                ErrorMessage = $"Ödeme sağlayıcı bulunamadı veya aktif değil: {order.PaymentProvider}"
            };
        }

        // Provider'ın credentials'ını oluştur
        var credentials = new PaymentProviderCredentials(
            provider.ApiKey,
            provider.ApiSecret,
            provider.UseTestMode ? provider.TestApiUrl : provider.ApiUrl,
            provider.TestApiUrl,
            provider.UseTestMode,
            provider.SettingsJson
        );

        // Payment service'i al
        if (!_paymentServiceFactory.IsProviderSupported(providerCode))
        {
            return new VerifyPaymentResponse
            {
                IsValid = false,
                ErrorMessage = $"Desteklenmeyen ödeme sağlayıcı: {order.PaymentProvider}"
            };
        }

        var paymentService = _paymentServiceFactory.GetService(providerCode);

        // Callback verification
        var isValid = await paymentService.VerifyCallbackAsync(
            credentials,
            request.Hash, 
            request.CallbackData, 
            cancellationToken);

        if (!isValid)
        {
            return new VerifyPaymentResponse
            {
                IsValid = false,
                ErrorMessage = "Ödeme doğrulaması başarısız"
            };
        }

        // Callback'ten status kontrolü (provider'a göre değişebilir)
        var status = request.CallbackData.GetValueOrDefault("status", "").ToLower();
        var isPaid = status == "success" || status == "paid" || status == "completed";

        if (isPaid)
        {
            order.PaymentStatus = "Paid";
            order.PaymentReference = request.PaymentReference;
            order.PaidAt = DateTime.UtcNow;
            order.Status = "Paid";

            await _dbContext.SaveChangesAsync(cancellationToken);

            // Event publish
            await _eventBus.PublishAsync(new OrderPaidEvent
            {
                OrderId = order.Id,
                TenantId = tenantId,
                PaymentProvider = order.PaymentProvider,
                PaymentReference = request.PaymentReference
            }, cancellationToken);

            _logger.LogInformation("Payment verified for order: {OrderId}", order.Id);
        }

        return new VerifyPaymentResponse
        {
            IsValid = true,
            IsPaid = isPaid
        };
    }
}



