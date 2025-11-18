using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Shipping.API.Attributes;
using Tinisoft.Application.Shipping.Commands.CreateShippingProvider;
using Tinisoft.Application.Shipping.Commands.UpdateShippingProvider;
using Tinisoft.Application.Shipping.Commands.CalculateShippingCost;
using Tinisoft.Application.Shipping.Commands.CreateShipment;
using Tinisoft.Application.Shipping.Queries.GetShippingProviders;

namespace Tinisoft.Shipping.API.Controllers;

[ApiController]
[Route("api/shipping")]
[RequireRole("TenantAdmin", "SystemAdmin")]
public class ShippingController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<ShippingController> _logger;

    public ShippingController(IMediator mediator, ILogger<ShippingController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Kargo firmalarını listele
    /// </summary>
    [HttpGet("providers")]
    public async Task<ActionResult<GetShippingProvidersResponse>> GetShippingProviders([FromQuery] GetShippingProvidersQuery query)
    {
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Yeni kargo firması ekle
    /// </summary>
    [HttpPost("providers")]
    public async Task<ActionResult<CreateShippingProviderResponse>> CreateShippingProvider([FromBody] CreateShippingProviderCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(GetShippingProviders), new { }, result);
    }

    /// <summary>
    /// Kargo firması güncelle (API key, ayarlar, vb.)
    /// </summary>
    [HttpPut("providers/{id}")]
    public async Task<ActionResult<UpdateShippingProviderResponse>> UpdateShippingProvider(Guid id, [FromBody] UpdateShippingProviderCommand command)
    {
        command.ShippingProviderId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Kargo ücreti hesapla
    /// </summary>
    [HttpPost("calculate-cost")]
    public async Task<ActionResult<CalculateShippingCostResponse>> CalculateShippingCost([FromBody] CalculateShippingCostCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Gönderi oluştur (kargo takip numarası al)
    /// </summary>
    [HttpPost("shipments")]
    public async Task<ActionResult<CreateShipmentResponse>> CreateShipment([FromBody] CreateShipmentCommand command)
    {
        var result = await _mediator.Send(command);
        if (result.Success)
        {
            return CreatedAtAction(nameof(CreateShipment), new { id = result.ShipmentId }, result);
        }
        return BadRequest(result);
    }
}

