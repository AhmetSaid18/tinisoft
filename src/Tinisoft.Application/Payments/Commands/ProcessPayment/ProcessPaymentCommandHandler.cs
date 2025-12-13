using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.Payments.Services;
using Tinisoft.Shared.Contracts;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Payments.Commands.ProcessPayment;

public class ProcessPaymentCommandHandler : IRequestHandler<ProcessPaymentCommand, ProcessPaymentResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IPaymentServiceFactory _paymentServiceFactory;
    private readonly IEventBus _eventBus;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<ProcessPaymentCommandHandler> _logger;

    public ProcessPaymentCommandHandler(
        IApplicationDbContext dbContext,
        IPaymentServiceFactory paymentServiceFactory,
        IEventBus eventBus,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<ProcessPaymentCommandHandler> logger)
    {
        _dbContext = dbContext;
        _paymentServiceFactory = paymentServiceFactory;
        _eventBus = eventBus;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<ProcessPaymentResponse> Handle(ProcessPaymentCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var order = await _dbContext.Orders
            .FirstOrDefaultAsync(o => 
                o.Id == request.OrderId && 
                o.TenantId == tenantId, cancellationToken);

        if (order == null)
        {
            throw new KeyNotFoundException($"Sipariş bulunamadı: {request.OrderId}");
        }

        if (order.PaymentStatus == "Paid")
        {
            return new ProcessPaymentResponse
            {
                Success = false,
                ErrorMessage = "Bu sipariş zaten ödendi"
            };
        }

        // Tenant'ın ödeme sağlayıcı bilgilerini database'den al
        var providerCode = request.PaymentProvider.ToUpper();
        var provider = await _dbContext.Set<PaymentProvider>()
            .FirstOrDefaultAsync(p => 
                p.TenantId == tenantId && 
                p.ProviderCode == providerCode && 
                p.IsActive, cancellationToken);

        if (provider == null)
        {
            return new ProcessPaymentResponse
            {
                Success = false,
                ErrorMessage = $"Ödeme sağlayıcı bulunamadı veya aktif değil: {request.PaymentProvider}"
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
            return new ProcessPaymentResponse
            {
                Success = false,
                ErrorMessage = $"Desteklenmeyen ödeme sağlayıcı: {request.PaymentProvider}"
            };
        }

        var paymentService = _paymentServiceFactory.GetService(providerCode);

        // Customer email
        var customerEmail = order.CustomerEmail;
        if (request.ProviderSpecificData?.ContainsKey("email") == true)
        {
            customerEmail = request.ProviderSpecificData["email"];
        }

        // Payment token request
        var paymentRequest = new PaymentTokenRequest
        {
            Email = customerEmail,
            Amount = request.Amount,
            OrderId = order.OrderNumber,
            Currency = request.Currency,
            Installment = request.ProviderSpecificData?.GetValueOrDefault("installment"),
            AdditionalData = request.ProviderSpecificData
        };

        var paymentResponse = await paymentService.GetPaymentTokenAsync(credentials, paymentRequest, cancellationToken);

        if (paymentResponse.Success && !string.IsNullOrEmpty(paymentResponse.Token))
        {
            // Order'ı güncelle
            order.PaymentProvider = providerCode;
            order.PaymentStatus = "Pending";
            await _dbContext.SaveChangesAsync(cancellationToken);

            return new ProcessPaymentResponse
            {
                Success = true,
                PaymentToken = paymentResponse.Token,
                RedirectUrl = paymentResponse.RedirectUrl
            };
        }
        else
        {
            return new ProcessPaymentResponse
            {
                Success = false,
                ErrorMessage = paymentResponse.ErrorMessage ?? "Ödeme token'ı alınamadı"
            };
        }
    }
}



