using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Application.Payments.Commands.CreatePaymentProvider;
using Tinisoft.Application.Payments.Commands.UpdatePaymentProvider;
using Tinisoft.Application.Payments.Queries.GetPaymentProviders;

namespace Tinisoft.Payments.API.Controllers;

[ApiController]
[Route("api/payments/providers")]
public class PaymentProvidersController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<PaymentProvidersController> _logger;

    public PaymentProvidersController(IMediator mediator, ILogger<PaymentProvidersController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Ödeme sağlayıcılarını listele
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<GetPaymentProvidersResponse>> GetPaymentProviders([FromQuery] GetPaymentProvidersQuery query)
    {
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Yeni ödeme sağlayıcı ekle
    /// </summary>
    [HttpPost]
    public async Task<ActionResult<CreatePaymentProviderResponse>> CreatePaymentProvider([FromBody] CreatePaymentProviderCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(GetPaymentProviders), new { }, result);
    }

    /// <summary>
    /// Ödeme sağlayıcı güncelle (API key, ayarlar, vb.)
    /// </summary>
    [HttpPut("{id}")]
    public async Task<ActionResult<UpdatePaymentProviderResponse>> UpdatePaymentProvider(Guid id, [FromBody] UpdatePaymentProviderCommand command)
    {
        command.PaymentProviderId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }
}

