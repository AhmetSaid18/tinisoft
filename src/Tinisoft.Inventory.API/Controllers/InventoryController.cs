using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Application.Inventory.Commands.AdjustStock;
using Tinisoft.Application.Inventory.Queries.GetStockLevel;

namespace Tinisoft.Inventory.API.Controllers;

[ApiController]
[Route("api/inventory")]
public class InventoryController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<InventoryController> _logger;

    public InventoryController(IMediator mediator, ILogger<InventoryController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpGet("products/{productId}")]
    public async Task<ActionResult<GetStockLevelResponse>> GetStockLevel(
        Guid productId, 
        [FromQuery] Guid? variantId = null)
    {
        var query = new GetStockLevelQuery 
        { 
            ProductId = productId, 
            VariantId = variantId 
        };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    [HttpPost("adjust")]
    public async Task<ActionResult<AdjustStockResponse>> AdjustStock([FromBody] AdjustStockCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }
}

