using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Application.Tenant.Commands.AddCustomDomain;
using Tinisoft.Application.Tenant.Commands.VerifyDomain;
using Tinisoft.Application.Tenant.Commands.RemoveDomain;
using Tinisoft.Application.Tenant.Queries.GetDomains;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/domains")]
public class DomainsController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<DomainsController> _logger;

    public DomainsController(IMediator mediator, ILogger<DomainsController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Tenant'ın domain listesini getirir
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<GetDomainsResponse>> GetDomains()
    {
        var result = await _mediator.Send(new GetDomainsQuery());
        return Ok(result);
    }

    /// <summary>
    /// Yeni custom domain ekler
    /// </summary>
    [HttpPost]
    public async Task<ActionResult<AddCustomDomainResponse>> AddDomain([FromBody] AddCustomDomainCommand command)
    {
        var result = await _mediator.Send(command);
        
        if (!result.Success)
        {
            return BadRequest(result);
        }
        
        return Ok(result);
    }

    /// <summary>
    /// Domain DNS verification yapar
    /// </summary>
    [HttpPost("{domainId}/verify")]
    public async Task<ActionResult<VerifyDomainResponse>> VerifyDomain(Guid domainId)
    {
        var result = await _mediator.Send(new VerifyDomainCommand { DomainId = domainId });
        
        if (!result.Success)
        {
            return BadRequest(result);
        }
        
        return Ok(result);
    }

    /// <summary>
    /// Domain'i kaldırır
    /// </summary>
    [HttpDelete("{domainId}")]
    public async Task<ActionResult<RemoveDomainResponse>> RemoveDomain(Guid domainId)
    {
        var result = await _mediator.Send(new RemoveDomainCommand { DomainId = domainId });
        
        if (!result.Success)
        {
            return BadRequest(result);
        }
        
        return Ok(result);
    }
}

