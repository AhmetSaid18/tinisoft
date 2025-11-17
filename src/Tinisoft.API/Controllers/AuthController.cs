using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Application.Auth.Commands.Register;
using Tinisoft.Application.Auth.Commands.Login;
using Tinisoft.API.Attributes;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/auth")]
public class AuthController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<AuthController> _logger;

    public AuthController(IMediator mediator, ILogger<AuthController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpPost("register")]
    [Public]
    public async Task<ActionResult<RegisterResponse>> Register([FromBody] RegisterCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    [HttpPost("login")]
    [Public]
    public async Task<ActionResult<LoginResponse>> Login([FromBody] LoginCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }
}

