using MediatR;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Payments.Commands.ProcessPayment;
using Tinisoft.Application.Payments.Commands.VerifyPayment;
using Tinisoft.Application.Common.Interfaces;
using Finbuckle.MultiTenant;
using Tinisoft.Infrastructure.MultiTenant;

namespace Tinisoft.Payments.API.Controllers;

[ApiController]
[Route("api/payments")]
public class PaymentsController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<PaymentsController> _logger;

    public PaymentsController(
        IMediator mediator,
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<PaymentsController> logger)
    {
        _mediator = mediator;
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
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
        try
        {
            var hash = data.GetValueOrDefault("hash", "");
            var merchantOid = data.GetValueOrDefault("merchant_oid", "");
            var status = data.GetValueOrDefault("status", "");
            var totalAmount = data.GetValueOrDefault("total_amount", "");

            if (string.IsNullOrEmpty(merchantOid))
            {
                _logger.LogWarning("PayTR callback: merchant_oid is missing");
                return BadRequest("merchant_oid is required");
            }

            // Order'ı OrderNumber ile bul (merchant_oid = order.OrderNumber)
            var order = await _dbContext.Orders
                .FirstOrDefaultAsync(o => o.OrderNumber == merchantOid);

            if (order == null)
            {
                _logger.LogWarning("PayTR callback: Order not found for merchant_oid: {MerchantOid}", merchantOid);
                return BadRequest("Order not found");
            }

            // Tenant context'i set et (multi-tenant için)
            var tenantInfo = new TenantInfo
            {
                Id = order.TenantId.ToString(),
                Identifier = order.TenantId.ToString()
            };
            _tenantAccessor.MultiTenantContext = new MultiTenantContext<TenantInfo>
            {
                TenantInfo = tenantInfo
            };

            // Verify payment
            var verifyCommand = new VerifyPaymentCommand
            {
                OrderId = order.Id,
                Hash = hash,
                PaymentReference = data.GetValueOrDefault("merchant_oid", ""),
                CallbackData = data
            };

            var verifyResult = await _mediator.Send(verifyCommand);

            if (verifyResult.IsValid && verifyResult.IsPaid)
            {
                _logger.LogInformation("PayTR callback: Payment verified successfully for order: {OrderId}", order.Id);
                return Ok("OK");
            }
            else
            {
                _logger.LogWarning("PayTR callback: Payment verification failed for order: {OrderId}", order.Id);
                return BadRequest("Payment verification failed");
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "PayTR callback error");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPost("callback/kuveytturk")]
    public async Task<IActionResult> KuveytTurkCallback([FromForm] Dictionary<string, string> data)
    {
        try
        {
            var orderId = data.GetValueOrDefault("OrderId", "");
            var status = data.GetValueOrDefault("Status", "");
            var hash = data.GetValueOrDefault("Hash", "");

            if (string.IsNullOrEmpty(orderId))
            {
                _logger.LogWarning("Kuveyt Türk callback: OrderId is missing");
                return BadRequest("OrderId is required");
            }

            // Order'ı OrderNumber ile bul
            var order = await _dbContext.Orders
                .FirstOrDefaultAsync(o => o.OrderNumber == orderId);

            if (order == null)
            {
                _logger.LogWarning("Kuveyt Türk callback: Order not found for OrderId: {OrderId}", orderId);
                return BadRequest("Order not found");
            }

            // Tenant context'i set et
            var tenantInfo = new MultiTenant.TenantInfo
            {
                Id = order.TenantId.ToString(),
                Identifier = order.TenantId.ToString()
            };
            _tenantAccessor.MultiTenantContext = new MultiTenantContext<MultiTenant.TenantInfo>
            {
                TenantInfo = tenantInfo
            };

            // Verify payment
            var verifyCommand = new VerifyPaymentCommand
            {
                OrderId = order.Id,
                Hash = hash,
                PaymentReference = data.GetValueOrDefault("TransactionId", ""),
                CallbackData = data
            };

            var verifyResult = await _mediator.Send(verifyCommand);

            if (verifyResult.IsValid && verifyResult.IsPaid)
            {
                _logger.LogInformation("Kuveyt Türk callback: Payment verified successfully for order: {OrderId}", order.Id);
                return Ok("OK");
            }
            else
            {
                _logger.LogWarning("Kuveyt Türk callback: Payment verification failed for order: {OrderId}", order.Id);
                return BadRequest("Payment verification failed");
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Kuveyt Türk callback error");
            return StatusCode(500, "Internal server error");
        }
    }
}

