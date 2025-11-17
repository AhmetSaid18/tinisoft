using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.API.Attributes;
using Tinisoft.Application.Templates.Queries.GetBootstrapData;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/public")]
public class PublicController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<PublicController> _logger;

    public PublicController(IMediator mediator, ILogger<PublicController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpGet("bootstrap")]
    [Public] // Public endpoint - multi-tenant context'ten tenant bulunur
    public async Task<ActionResult<GetBootstrapDataResponse>> Bootstrap()
    {
        var result = await _mediator.Send(new GetBootstrapDataQuery());
        return Ok(result);
    }
}

