using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Application.Orders.Commands.CreateOrder;
using Tinisoft.Application.Orders.Commands.UpdateOrderStatus;
using Tinisoft.Application.Orders.Queries.GetOrder;

namespace Tinisoft.Orders.API.Controllers;

[ApiController]
[Route("api/orders")]
public class OrdersController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<OrdersController> _logger;

    public OrdersController(IMediator mediator, ILogger<OrdersController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpPost]
    public async Task<ActionResult<CreateOrderResponse>> CreateOrder([FromBody] CreateOrderCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(GetOrder), new { id = result.OrderId }, result);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<GetOrderResponse>> GetOrder(Guid id)
    {
        var query = new GetOrderQuery { OrderId = id };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    [HttpPut("{id}/status")]
    public async Task<ActionResult<UpdateOrderStatusResponse>> UpdateOrderStatus(
        Guid id, 
        [FromBody] UpdateOrderStatusCommand command)
    {
        command.OrderId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }
}

