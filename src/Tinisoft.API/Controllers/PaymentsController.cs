using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.API.Controllers;
using Tinisoft.Application.Payments.Commands.ProcessPayment;
using Tinisoft.Application.Payments.Commands.VerifyPayment;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class PaymentsController : BaseController
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
        // PayTR callback handler
        var hash = data.GetValueOrDefault("hash", "");
        var merchantOid = data.GetValueOrDefault("merchant_oid", "");
        
        // OrderId'yi merchant_oid'den bul (order.OrderNumber ile eşleşir)
        // Bu kısım order lookup ile tamamlanacak
        
        return Ok();
    }
}

