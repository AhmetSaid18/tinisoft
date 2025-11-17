using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.API.Attributes;
using Tinisoft.Application.Admin.Queries.GetSystemStatistics;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/admin")]
[RequireRole("SystemAdmin")]
public class AdminController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<AdminController> _logger;

    public AdminController(IMediator mediator, ILogger<AdminController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpGet("statistics")]
    public async Task<ActionResult<GetSystemStatisticsResponse>> GetSystemStatistics()
    {
        var result = await _mediator.Send(new GetSystemStatisticsQuery());
        return Ok(result);
    }
}

