using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.API.Attributes;
using Tinisoft.Application.Tenant.Commands.UpdateTenantSettings;
using Tinisoft.Application.Tenant.Commands.UpdateLayoutSettings;
using Tinisoft.Application.Tenant.Queries.GetTenantSettings;
using Tinisoft.Application.Tenant.Queries.GetTenantPublicInfo;
using Tinisoft.Application.Tenant.Queries.GetLayoutSettings;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/tenant")]
public class TenantController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<TenantController> _logger;

    public TenantController(IMediator mediator, ILogger<TenantController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpGet("public")]
    [Public] // Public - site footer/header'da sosyal medya linklerini göstermek için
    public async Task<ActionResult<GetTenantPublicInfoResponse>> GetPublicInfo([FromQuery] string? slug = null)
    {
        var query = new GetTenantPublicInfoQuery { Slug = slug };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    [HttpGet("settings")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<GetTenantSettingsResponse>> GetSettings()
    {
        var result = await _mediator.Send(new GetTenantSettingsQuery());
        return Ok(result);
    }

    [HttpPut("settings")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<UpdateTenantSettingsResponse>> UpdateSettings([FromBody] UpdateTenantSettingsCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    [HttpGet("layout")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<GetLayoutSettingsResponse>> GetLayoutSettings()
    {
        var result = await _mediator.Send(new GetLayoutSettingsQuery());
        return Ok(result);
    }

    [HttpPut("layout")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<UpdateLayoutSettingsResponse>> UpdateLayoutSettings([FromBody] UpdateLayoutSettingsCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }
}

