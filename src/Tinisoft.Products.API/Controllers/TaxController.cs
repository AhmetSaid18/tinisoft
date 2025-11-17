using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Application.Tax.Commands.CalculateTax;
using Tinisoft.Application.Tax.Commands.CreateTaxRate;
using Tinisoft.Application.Tax.Commands.UpdateTaxRate;
using Tinisoft.Application.Tax.Commands.DeleteTaxRate;
using Tinisoft.Application.Tax.Queries.GetTaxRates;

namespace Tinisoft.Products.API.Controllers;

[ApiController]
[Route("api/tax")]
public class TaxController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<TaxController> _logger;

    public TaxController(IMediator mediator, ILogger<TaxController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpPost("calculate")]
    public async Task<ActionResult<CalculateTaxResponse>> CalculateTax([FromBody] CalculateTaxCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    [HttpGet("rates")]
    public async Task<ActionResult<List<TaxRateDto>>> GetTaxRates([FromQuery] bool? isActive = null)
    {
        var query = new GetTaxRatesQuery { IsActive = isActive };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    [HttpPost("rates")]
    public async Task<ActionResult<CreateTaxRateResponse>> CreateTaxRate([FromBody] CreateTaxRateCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(GetTaxRates), new { id = result.TaxRateId }, result);
    }

    [HttpPut("rates/{id}")]
    public async Task<ActionResult<UpdateTaxRateResponse>> UpdateTaxRate(Guid id, [FromBody] UpdateTaxRateCommand command)
    {
        command.TaxRateId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    [HttpDelete("rates/{id}")]
    public async Task<IActionResult> DeleteTaxRate(Guid id)
    {
        var command = new DeleteTaxRateCommand { TaxRateId = id };
        await _mediator.Send(command);
        return NoContent();
    }
}

