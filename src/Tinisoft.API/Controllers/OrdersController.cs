using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.API.Attributes;
using Tinisoft.Application.Orders.Commands.CreateOrder;
using Tinisoft.Application.Orders.Commands.UpdateOrderStatus;
using Tinisoft.Application.Orders.Queries.GetOrder;
using Tinisoft.Application.Orders.Queries.GetOrders;
using Tinisoft.Application.Orders.Queries.GetOrderStats;

namespace Tinisoft.API.Controllers;

/// <summary>
/// Sipariş yönetimi API'si
/// </summary>
    [RequireRole("TenantAdmin", "Customer")]
public class OrdersController : BaseController
{
    private readonly IMediator _mediator;

    public OrdersController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Yeni sipariş oluştur
    /// </summary>
    [HttpPost]
    public async Task<ActionResult<CreateOrderResponse>> CreateOrder([FromBody] CreateOrderCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(GetOrder), new { id = result.OrderId }, result);
    }

    /// <summary>
    /// Sipariş detaylarını getir
    /// </summary>
    [HttpGet("{id:guid}")]
    public async Task<ActionResult<GetOrderResponse>> GetOrder(Guid id)
    {
        var result = await _mediator.Send(new GetOrderQuery { OrderId = id });
        if (result == null)
            return NotFound();
        return Ok(result);
    }

    /// <summary>
    /// Sipariş durumunu güncelle
    /// </summary>
    [HttpPut("{id:guid}/status")]
    public async Task<ActionResult> UpdateOrderStatus(Guid id, [FromBody] UpdateOrderStatusRequest request)
    {
        await _mediator.Send(new UpdateOrderStatusCommand 
        { 
            OrderId = id, 
            Status = request.Status,
            TrackingNumber = null // TrackingNumber request'te yok, null olarak gönder
        });
        return NoContent();
    }

    /// <summary>
    /// Tüm siparişleri listele (sayfalı)
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<PagedOrdersResponse>> GetOrders(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        [FromQuery] string? status = null,
        [FromQuery] string? search = null,
        [FromQuery] DateTime? startDate = null,
        [FromQuery] DateTime? endDate = null)
    {
        var result = await _mediator.Send(new GetOrdersQuery
        {
            Page = page,
            PageSize = pageSize,
            Status = status,
            Search = search,
            StartDate = startDate,
            EndDate = endDate
        });
        return Ok(result);
    }

    /// <summary>
    /// Sipariş istatistiklerini getir
    /// </summary>
    [HttpGet("stats")]
    public async Task<ActionResult<OrderStatsResponse>> GetOrderStats(
        [FromQuery] DateTime? startDate = null,
        [FromQuery] DateTime? endDate = null)
    {
        var result = await _mediator.Send(new GetOrderStatsQuery
        {
            StartDate = startDate ?? DateTime.UtcNow.AddDays(-30),
            EndDate = endDate ?? DateTime.UtcNow
        });
        return Ok(result);
    }
}

public class UpdateOrderStatusRequest
{
    public string Status { get; set; } = string.Empty;
    public string? Notes { get; set; }
}

