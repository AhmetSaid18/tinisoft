using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Notifications.API.Attributes;
using Tinisoft.Application.Notifications.Commands.CreateEmailProvider;
using Tinisoft.Application.Notifications.Commands.CreateEmailTemplate;
using Tinisoft.Application.Notifications.Commands.SendEmail;
using Tinisoft.Application.Notifications.Queries.GetEmailTemplates;

namespace Tinisoft.Notifications.API.Controllers;

[ApiController]
[Route("api/notifications")]
[RequireRole("TenantAdmin", "SystemAdmin")]
public class NotificationsController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<NotificationsController> _logger;

    public NotificationsController(IMediator mediator, ILogger<NotificationsController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Email provider oluştur (SMTP ayarları)
    /// </summary>
    [HttpPost("email-providers")]
    public async Task<ActionResult<CreateEmailProviderResponse>> CreateEmailProvider([FromBody] CreateEmailProviderCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(CreateEmailProvider), new { }, result);
    }

    /// <summary>
    /// Email template oluştur
    /// </summary>
    [HttpPost("email-templates")]
    public async Task<ActionResult<CreateEmailTemplateResponse>> CreateEmailTemplate([FromBody] CreateEmailTemplateCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(CreateEmailTemplate), new { }, result);
    }

    /// <summary>
    /// Email template'leri listele
    /// </summary>
    [HttpGet("email-templates")]
    public async Task<ActionResult<GetEmailTemplatesResponse>> GetEmailTemplates([FromQuery] GetEmailTemplatesQuery query)
    {
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Email gönder
    /// </summary>
    [HttpPost("send-email")]
    public async Task<ActionResult<SendEmailResponse>> SendEmail([FromBody] SendEmailCommand command)
    {
        var result = await _mediator.Send(command);
        if (result.Success)
        {
            return Ok(result);
        }
        return BadRequest(result);
    }
}

