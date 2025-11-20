using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Payments.Commands.ProcessPayment;

public class ProcessPaymentCommandHandler : IRequestHandler<ProcessPaymentCommand, ProcessPaymentResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IPayTRService _payTRService;
    private readonly IEventBus _eventBus;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<ProcessPaymentCommandHandler> _logger;

    public ProcessPaymentCommandHandler(
        IApplicationDbContext dbContext,
        IPayTRService payTRService,
        IEventBus eventBus,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<ProcessPaymentCommandHandler> logger)
    {
        _dbContext = dbContext;
        _payTRService = payTRService;
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

        // Payment provider'a göre işlem
        if (request.PaymentProvider == "PayTR")
        {
            var customerEmail = order.CustomerEmail;
            if (request.ProviderSpecificData?.ContainsKey("email") == true)
            {
                customerEmail = request.ProviderSpecificData["email"];
            }

            var payTRRequest = new PayTRTokenRequest
            {
                Email = customerEmail,
                Amount = request.Amount,
                OrderId = order.OrderNumber,
                Currency = request.Currency
            };

            var payTRResponse = await _payTRService.GetTokenAsync(payTRRequest, cancellationToken);

            if (payTRResponse.Success && !string.IsNullOrEmpty(payTRResponse.Token))
            {
                // Order'ı güncelle
                order.PaymentProvider = "PayTR";
                order.PaymentStatus = "Pending";
                await _dbContext.SaveChangesAsync(cancellationToken);

                return new ProcessPaymentResponse
                {
                    Success = true,
                    PaymentToken = payTRResponse.Token,
                    RedirectUrl = $"https://www.paytr.com/odeme/guvenli/{payTRResponse.Token}"
                };
            }
            else
            {
                return new ProcessPaymentResponse
                {
                    Success = false,
                    ErrorMessage = payTRResponse.ErrorMessage ?? "Ödeme token'ı alınamadı"
                };
            }
        }

        return new ProcessPaymentResponse
        {
            Success = false,
            ErrorMessage = $"Desteklenmeyen ödeme sağlayıcı: {request.PaymentProvider}"
        };
    }
}



