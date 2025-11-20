using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Payments.Commands.VerifyPayment;

public class VerifyPaymentCommandHandler : IRequestHandler<VerifyPaymentCommand, VerifyPaymentResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IPayTRService _payTRService;
    private readonly IEventBus _eventBus;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<VerifyPaymentCommandHandler> _logger;

    public VerifyPaymentCommandHandler(
        IApplicationDbContext dbContext,
        IPayTRService payTRService,
        IEventBus eventBus,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<VerifyPaymentCommandHandler> logger)
    {
        _dbContext = dbContext;
        _payTRService = payTRService;
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

        // PayTR callback verification
        if (order.PaymentProvider == "PayTR")
        {
            var isValid = await _payTRService.VerifyCallbackAsync(
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

            // Callback'ten status kontrolü
            var status = request.CallbackData.GetValueOrDefault("status", "");
            var isPaid = status == "success";

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
                    PaymentProvider = order.PaymentProvider ?? "PayTR",
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

        return new VerifyPaymentResponse
        {
            IsValid = false,
            ErrorMessage = "Desteklenmeyen ödeme sağlayıcı"
        };
    }
}



