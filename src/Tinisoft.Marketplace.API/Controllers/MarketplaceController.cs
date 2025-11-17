using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Application.Marketplace.Commands.SyncProducts;

namespace Tinisoft.Marketplace.API.Controllers;

[ApiController]
[Route("api/marketplace")]
public class MarketplaceController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<MarketplaceController> _logger;

    public MarketplaceController(IMediator mediator, ILogger<MarketplaceController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpPost("sync/products")]
    public async Task<ActionResult<SyncProductsResponse>> SyncProducts([FromBody] SyncProductsCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }
}

