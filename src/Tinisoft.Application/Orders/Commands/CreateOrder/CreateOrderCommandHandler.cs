using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using System.Text.Json;

namespace Tinisoft.Application.Orders.Commands.CreateOrder;

public class CreateOrderCommandHandler : IRequestHandler<CreateOrderCommand, CreateOrderResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IEventBus _eventBus;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CreateOrderCommandHandler> _logger;

    public CreateOrderCommandHandler(
        IApplicationDbContext dbContext,
        IEventBus eventBus,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CreateOrderCommandHandler> logger)
    {
        _dbContext = dbContext;
        _eventBus = eventBus;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CreateOrderResponse> Handle(CreateOrderCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Order number oluştur
        var orderCount = await _dbContext.Orders
            .CountAsync(o => o.TenantId == tenantId, cancellationToken);
        var orderNumber = $"ORD-{DateTime.UtcNow:yyyyMMdd}-{orderCount + 1:D6}";

        var order = new Order
        {
            TenantId = tenantId,
            OrderNumber = orderNumber,
            Status = "Pending",
            CustomerEmail = request.CustomerEmail,
            CustomerPhone = request.CustomerPhone,
            CustomerFirstName = request.CustomerFirstName,
            CustomerLastName = request.CustomerLastName,
            ShippingAddressLine1 = request.ShippingAddressLine1,
            ShippingAddressLine2 = request.ShippingAddressLine2,
            ShippingCity = request.ShippingCity,
            ShippingState = request.ShippingState,
            ShippingPostalCode = request.ShippingPostalCode,
            ShippingCountry = request.ShippingCountry,
            ShippingMethod = request.ShippingMethod,
            PaymentStatus = "Pending",
            TotalsJson = JsonSerializer.Serialize(new
            {
                subtotal = request.Subtotal,
                tax = request.Tax,
                shipping = request.Shipping,
                discount = request.Discount,
                total = request.Total
            })
        };

        _dbContext.Orders.Add(order);

        // Order Items
        foreach (var itemDto in request.Items)
        {
            var orderItem = new OrderItem
            {
                OrderId = order.Id,
                ProductId = itemDto.ProductId,
                ProductVariantId = itemDto.ProductVariantId,
                Quantity = itemDto.Quantity,
                UnitPrice = itemDto.UnitPrice,
                TotalPrice = itemDto.Quantity * itemDto.UnitPrice,
                Title = $"Product {itemDto.ProductId}" // Products API'den çekilebilir
            };
            _dbContext.OrderItems.Add(orderItem);
        }

        await _dbContext.SaveChangesAsync(cancellationToken);

        // Event publish
        await _eventBus.PublishAsync(new OrderCreatedEvent
        {
            OrderId = order.Id,
            TenantId = tenantId,
            OrderNumber = order.OrderNumber,
            TotalAmount = request.Total
        }, cancellationToken);

        _logger.LogInformation("Order created: {OrderNumber} - {Total}", order.OrderNumber, request.Total);

        return new CreateOrderResponse
        {
            OrderId = order.Id,
            OrderNumber = order.OrderNumber,
            Total = request.Total
        };
    }
}



