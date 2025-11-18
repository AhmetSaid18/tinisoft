using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Application.Invoices.Commands.CreateInvoice;
using Tinisoft.Application.Invoices.Commands.CancelInvoice;
using Tinisoft.Application.Invoices.Commands.SendInvoiceToGIB;
using Tinisoft.Application.Invoices.Commands.UpdateInvoiceSettings;
using Tinisoft.Application.Invoices.Queries.GetInvoice;
using Tinisoft.Application.Invoices.Queries.GetInvoices;
using Tinisoft.Application.Invoices.Queries.GetInvoiceSettings;
using Tinisoft.Application.Invoices.Queries.GetInvoiceStatusFromGIB;
using Tinisoft.Application.Invoices.Queries.GetInboxInvoices;

namespace Tinisoft.Invoices.API.Controllers;

[ApiController]
[Route("api/invoices")]
public class InvoicesController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<InvoicesController> _logger;

    public InvoicesController(IMediator mediator, ILogger<InvoicesController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Faturaları listele (filtreleme, sayfalama)
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<GetInvoicesResponse>> GetInvoices([FromQuery] GetInvoicesQuery query)
    {
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Fatura detayını getir
    /// </summary>
    [HttpGet("{id}")]
    public async Task<ActionResult<GetInvoiceResponse>> GetInvoice(
        Guid id,
        [FromQuery] bool includePdf = false)
    {
        var query = new GetInvoiceQuery 
        { 
            InvoiceId = id,
            IncludePDF = includePdf
        };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Siparişten fatura oluştur
    /// </summary>
    [HttpPost]
    public async Task<ActionResult<CreateInvoiceResponse>> CreateInvoice([FromBody] CreateInvoiceCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(GetInvoice), new { id = result.InvoiceId }, result);
    }

    /// <summary>
    /// Faturayı iptal et
    /// </summary>
    [HttpPost("{id}/cancel")]
    public async Task<ActionResult<CancelInvoiceResponse>> CancelInvoice(
        Guid id,
        [FromBody] CancelInvoiceCommand command)
    {
        command.InvoiceId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Faturayı GİB'e gönder
    /// </summary>
    [HttpPost("{id}/send-to-gib")]
    public async Task<ActionResult<SendInvoiceToGIBResponse>> SendInvoiceToGIB(Guid id)
    {
        var command = new SendInvoiceToGIBCommand { InvoiceId = id };
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Fatura ayarlarını getir
    /// </summary>
    [HttpGet("settings")]
    public async Task<ActionResult<GetInvoiceSettingsResponse>> GetInvoiceSettings()
    {
        var query = new GetInvoiceSettingsQuery();
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Fatura ayarlarını güncelle
    /// </summary>
    [HttpPut("settings")]
    public async Task<ActionResult<UpdateInvoiceSettingsResponse>> UpdateInvoiceSettings(
        [FromBody] UpdateInvoiceSettingsCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Fatura durumunu GİB'den sorgula
    /// </summary>
    [HttpGet("{id}/gib-status")]
    public async Task<ActionResult<GetInvoiceStatusFromGIBResponse>> GetInvoiceStatusFromGIB(Guid id)
    {
        var query = new GetInvoiceStatusFromGIBQuery { InvoiceId = id };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Gelen faturaları GİB'den al (inbox)
    /// </summary>
    [HttpGet("inbox")]
    public async Task<ActionResult<GetInboxInvoicesResponse>> GetInboxInvoices(
        [FromQuery] DateTime? startDate = null,
        [FromQuery] DateTime? endDate = null,
        [FromQuery] string? senderVKN = null)
    {
        var query = new GetInboxInvoicesQuery
        {
            StartDate = startDate,
            EndDate = endDate,
            SenderVKN = senderVKN
        };
        var result = await _mediator.Send(query);
        return Ok(result);
    }
}

