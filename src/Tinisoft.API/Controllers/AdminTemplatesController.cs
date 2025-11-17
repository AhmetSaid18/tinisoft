using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.API.Attributes;
using Tinisoft.Application.Admin.Templates.Commands.CreateTemplate;
using Tinisoft.Application.Admin.Templates.Commands.UpdateTemplate;
using Tinisoft.Application.Admin.Templates.Commands.DeleteTemplate;
using Tinisoft.Application.Admin.Templates.Commands.ToggleTemplateActive;
using Tinisoft.Application.Admin.Templates.Queries.GetAllTemplates;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/admin/templates")]
[RequireRole("SystemAdmin")]
public class AdminTemplatesController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<AdminTemplatesController> _logger;

    public AdminTemplatesController(IMediator mediator, ILogger<AdminTemplatesController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<GetAllTemplatesResponse>> GetAllTemplates()
    {
        var result = await _mediator.Send(new GetAllTemplatesQuery());
        return Ok(result);
    }

    [HttpPost]
    public async Task<ActionResult<CreateTemplateResponse>> CreateTemplate([FromBody] CreateTemplateCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(CreateTemplate), new { id = result.TemplateId }, result);
    }

    [HttpPut("{id}")]
    public async Task<ActionResult<UpdateTemplateResponse>> UpdateTemplate(Guid id, [FromBody] UpdateTemplateCommand command)
    {
        command.TemplateId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    [HttpDelete("{id}")]
    public async Task<ActionResult<DeleteTemplateResponse>> DeleteTemplate(Guid id)
    {
        var command = new DeleteTemplateCommand { TemplateId = id };
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    [HttpPatch("{id}/toggle-active")]
    public async Task<ActionResult<ToggleTemplateActiveResponse>> ToggleTemplateActive(Guid id, [FromBody] ToggleTemplateActiveCommand command)
    {
        command.TemplateId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }
}

