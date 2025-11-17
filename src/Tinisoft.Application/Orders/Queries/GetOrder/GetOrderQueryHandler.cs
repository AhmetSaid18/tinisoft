using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;
using System.Text.Json;

namespace Tinisoft.Application.Orders.Queries.GetOrder;

public class GetOrderQueryHandler : IRequestHandler<GetOrderQuery, GetOrderResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;

    public GetOrderQueryHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
    }

    public async Task<GetOrderResponse> Handle(GetOrderQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var order = await _dbContext.Orders
            .Include(o => o.OrderItems)
            .FirstOrDefaultAsync(o => o.Id == request.OrderId && o.TenantId == tenantId, cancellationToken);

        if (order == null)
        {
            throw new KeyNotFoundException($"Sipariş bulunamadı: {request.OrderId}");
        }

        var totals = JsonSerializer.Deserialize<OrderTotalsDto>(order.TotalsJson) ?? new OrderTotalsDto();

        return new GetOrderResponse
        {
            Id = order.Id,
            OrderNumber = order.OrderNumber,
            Status = order.Status,
            CustomerEmail = order.CustomerEmail,
            CustomerPhone = order.CustomerPhone,
            CustomerFirstName = order.CustomerFirstName,
            CustomerLastName = order.CustomerLastName,
            Totals = totals,
            PaymentStatus = order.PaymentStatus,
            PaymentProvider = order.PaymentProvider,
            PaidAt = order.PaidAt,
            ShippingMethod = order.ShippingMethod,
            TrackingNumber = order.TrackingNumber,
            CreatedAt = order.CreatedAt,
            Items = order.OrderItems.Select(oi => new OrderItemResponse
            {
                Id = oi.Id,
                ProductId = oi.ProductId,
                ProductVariantId = oi.ProductVariantId,
                Title = oi.Title,
                Quantity = oi.Quantity,
                UnitPrice = oi.UnitPrice,
                TotalPrice = oi.TotalPrice
            }).ToList()
        };
    }
}

