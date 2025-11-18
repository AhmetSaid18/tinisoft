using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Application.Resellers.Commands.CreateReseller;
using Tinisoft.Application.Resellers.Commands.CreateResellerPrice;
using Tinisoft.Application.Resellers.Queries.GetResellers;
using Tinisoft.API.Attributes;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/[controller]")]
[RequireRole("TenantAdmin", "SystemAdmin")]
public class ResellersController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<ResellersController> _logger;

    public ResellersController(IMediator mediator, ILogger<ResellersController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Yeni bayi oluştur
    /// </summary>
    [HttpPost]
    public async Task<ActionResult<CreateResellerResponse>> CreateReseller([FromBody] CreateResellerCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Bayi listesi
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<GetResellersResponse>> GetResellers([FromQuery] GetResellersQuery query)
    {
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Bayi için özel fiyat oluştur
    /// </summary>
    [HttpPost("{resellerId}/prices")]
    public async Task<ActionResult<CreateResellerPriceResponse>> CreateResellerPrice(
        Guid resellerId,
        [FromBody] CreateResellerPriceCommand command)
    {
        command.ResellerId = resellerId;
        var result = await _mediator.Send(command);
        return Ok(result);
    }
}

