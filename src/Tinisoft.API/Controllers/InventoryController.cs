using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.API.Controllers;
using Tinisoft.Application.Inventory.Commands.AdjustStock;
using Tinisoft.Application.Inventory.Queries.GetStockLevel;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class InventoryController : BaseController
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

