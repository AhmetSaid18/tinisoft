using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.API.Attributes;
using Tinisoft.Application.Templates.Commands.SelectTemplate;
using Tinisoft.Application.Templates.Queries.GetAvailableTemplates;
using Tinisoft.Application.Templates.Queries.GetSelectedTemplate;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/templates")]
public class TemplatesController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<TemplatesController> _logger;

    public TemplatesController(IMediator mediator, ILogger<TemplatesController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpGet("available")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<GetAvailableTemplatesResponse>> GetAvailableTemplates()
    {
        var result = await _mediator.Send(new GetAvailableTemplatesQuery());
        return Ok(result);
    }

    [HttpGet("selected")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<GetSelectedTemplateResponse>> GetSelectedTemplate()
    {
        var result = await _mediator.Send(new GetSelectedTemplateQuery());
        return Ok(result);
    }

    [HttpPost("select")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<SelectTemplateResponse>> SelectTemplate([FromBody] SelectTemplateCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }
}

