using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Interfaces;
using Finbuckle.MultiTenant;
using System.Text.Json;

namespace Tinisoft.Application.Customers.Queries.GetCustomerOrder;

public class GetCustomerOrderQueryHandler : IRequestHandler<GetCustomerOrderQuery, GetCustomerOrderResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly ICurrentCustomerService _currentCustomerService;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetCustomerOrderQueryHandler> _logger;

    public GetCustomerOrderQueryHandler(
        IApplicationDbContext dbContext,
        ICurrentCustomerService currentCustomerService,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetCustomerOrderQueryHandler> logger)
    {
        _dbContext = dbContext;
        _currentCustomerService = currentCustomerService;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetCustomerOrderResponse> Handle(GetCustomerOrderQuery request, CancellationToken cancellationToken)
    {
        var customerId = _currentCustomerService.GetCurrentCustomerId();
        if (!customerId.HasValue)
        {
            throw new UnauthorizedAccessException("Müşteri bilgisi bulunamadı");
        }

        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Sadece bu müşterinin siparişini getir
        var order = await _dbContext.Orders
            .AsNoTracking()
            .Include(o => o.OrderItems)
            .FirstOrDefaultAsync(o => o.Id == request.OrderId && 
                o.TenantId == tenantId && 
                o.CustomerId == customerId.Value, cancellationToken);

        if (order == null)
        {
            throw new KeyNotFoundException("Sipariş bulunamadı veya bu sipariş size ait değil");
        }

        var totals = JsonSerializer.Deserialize<OrderTotalsDto>(order.TotalsJson) ?? new OrderTotalsDto();

        return new GetCustomerOrderResponse
        {
            Id = order.Id,
            OrderNumber = order.OrderNumber,
            Status = order.Status,
            CustomerEmail = order.CustomerEmail,
            CustomerPhone = order.CustomerPhone,
            CustomerFirstName = order.CustomerFirstName,
            CustomerLastName = order.CustomerLastName,
            ShippingAddress = new ShippingAddressDto
            {
                AddressLine1 = order.ShippingAddressLine1,
                AddressLine2 = order.ShippingAddressLine2,
                City = order.ShippingCity,
                State = order.ShippingState,
                PostalCode = order.ShippingPostalCode,
                Country = order.ShippingCountry
            },
            Totals = totals,
            PaymentStatus = order.PaymentStatus,
            PaymentProvider = order.PaymentProvider,
            PaidAt = order.PaidAt,
            ShippingMethod = order.ShippingMethod,
            TrackingNumber = order.TrackingNumber,
            Items = order.OrderItems.Select(oi => new OrderItemDto
            {
                Id = oi.Id,
                ProductId = oi.ProductId,
                ProductVariantId = oi.ProductVariantId,
                Title = oi.Title,
                SKU = oi.SKU,
                Quantity = oi.Quantity,
                UnitPrice = oi.UnitPrice,
                TotalPrice = oi.TotalPrice
            }).ToList(),
            CreatedAt = order.CreatedAt,
            UpdatedAt = order.UpdatedAt
        };
    }
}



