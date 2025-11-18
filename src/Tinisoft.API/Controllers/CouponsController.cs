using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Application.Discounts.Commands.CreateCoupon;
using Tinisoft.Application.Discounts.Commands.UpdateCoupon;
using Tinisoft.Application.Discounts.Commands.DeleteCoupon;
using Tinisoft.Application.Discounts.Queries.GetCoupons;
using Tinisoft.Application.Discounts.Queries.GetCoupon;
using Tinisoft.Application.Discounts.Queries.GetCouponStatistics;
using Tinisoft.API.Attributes;

namespace Tinisoft.API.Controllers;

/// <summary>
/// Kupon yönetimi (TenantAdmin için)
/// </summary>
[ApiController]
[Route("api/coupons")]
[RequireRole("TenantAdmin", "SystemAdmin")]
public class CouponsController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<CouponsController> _logger;

    public CouponsController(IMediator mediator, ILogger<CouponsController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Kupon listesi
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<GetCouponsResponse>> GetCoupons([FromQuery] GetCouponsQuery query)
    {
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Yeni kupon oluştur
    /// </summary>
    [HttpPost]
    public async Task<ActionResult<CreateCouponResponse>> CreateCoupon([FromBody] CreateCouponCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(GetCoupons), new { }, result);
    }

    /// <summary>
    /// Kupon güncelle
    /// </summary>
    [HttpPut("{id}")]
    public async Task<ActionResult<UpdateCouponResponse>> UpdateCoupon(Guid id, [FromBody] UpdateCouponCommand command)
    {
        command.CouponId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Kupon detayı
    /// </summary>
    [HttpGet("{id}")]
    public async Task<ActionResult<GetCouponResponse>> GetCoupon(Guid id)
    {
        var query = new GetCouponQuery { CouponId = id };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Kupon istatistikleri (kullanım sayısı, toplam indirim, vs.)
    /// </summary>
    [HttpGet("{id}/statistics")]
    public async Task<ActionResult<GetCouponStatisticsResponse>> GetCouponStatistics(Guid id)
    {
        var query = new GetCouponStatisticsQuery { CouponId = id };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Kupon sil (kullanılmışsa pasif yapılır)
    /// </summary>
    [HttpDelete("{id}")]
    public async Task<ActionResult<DeleteCouponResponse>> DeleteCoupon(Guid id)
    {
        var command = new DeleteCouponCommand { CouponId = id };
        var result = await _mediator.Send(command);
        return Ok(result);
    }
}

