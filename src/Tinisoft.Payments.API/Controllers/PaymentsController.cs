using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Application.Payments.Commands.ProcessPayment;
using Tinisoft.Application.Payments.Commands.VerifyPayment;

namespace Tinisoft.Payments.API.Controllers;

[ApiController]
[Route("api/payments")]
public class PaymentsController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<PaymentsController> _logger;

    public PaymentsController(IMediator mediator, ILogger<PaymentsController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpPost("process")]
    public async Task<ActionResult<ProcessPaymentResponse>> ProcessPayment([FromBody] ProcessPaymentCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    [HttpPost("verify")]
    public async Task<ActionResult<VerifyPaymentResponse>> VerifyPayment([FromBody] VerifyPaymentCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    [HttpPost("callback/paytr")]
    public async Task<IActionResult> PayTRCallback([FromForm] Dictionary<string, string> data)
    {
        var hash = data.GetValueOrDefault("hash", "");
        var merchantOid = data.GetValueOrDefault("merchant_oid", "");
        
        // OrderId'yi merchant_oid'den bul ve verify et
        return Ok();
    }
}

