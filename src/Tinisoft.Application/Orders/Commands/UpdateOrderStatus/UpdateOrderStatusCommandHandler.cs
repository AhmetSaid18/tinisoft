using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Orders.Commands.UpdateOrderStatus;

public class UpdateOrderStatusCommandHandler : IRequestHandler<UpdateOrderStatusCommand, UpdateOrderStatusResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IEventBus _eventBus;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<UpdateOrderStatusCommandHandler> _logger;

    public UpdateOrderStatusCommandHandler(
        IApplicationDbContext dbContext,
        IEventBus eventBus,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<UpdateOrderStatusCommandHandler> logger)
    {
        _dbContext = dbContext;
        _eventBus = eventBus;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<UpdateOrderStatusResponse> Handle(UpdateOrderStatusCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var order = await _dbContext.Orders
            .FirstOrDefaultAsync(o => o.Id == request.OrderId && o.TenantId == tenantId, cancellationToken);

        if (order == null)
        {
            throw new KeyNotFoundException($"Sipariş bulunamadı: {request.OrderId}");
        }

        var oldStatus = order.Status;
        order.Status = request.Status;

        if (request.Status == "Shipped" && !string.IsNullOrEmpty(request.TrackingNumber))
        {
            order.TrackingNumber = request.TrackingNumber;
            order.ShippedAt = DateTime.UtcNow;
        }

        order.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        // Event publish
        await _eventBus.PublishAsync(new OrderStatusChangedEvent
        {
            OrderId = order.Id,
            TenantId = tenantId,
            OldStatus = oldStatus,
            NewStatus = request.Status
        }, cancellationToken);

        _logger.LogInformation("Order status updated: {OrderId} - {OldStatus} -> {NewStatus}", 
            order.Id, oldStatus, request.Status);

        return new UpdateOrderStatusResponse
        {
            OrderId = order.Id,
            Status = order.Status
        };
    }
}



