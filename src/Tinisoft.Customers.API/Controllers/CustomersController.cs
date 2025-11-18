using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Customers.API.Attributes;
using Tinisoft.Application.Customers.Commands.RegisterCustomer;
using Tinisoft.Application.Customers.Commands.LoginCustomer;
using Tinisoft.Application.Customers.Queries.GetCustomerProfile;
using Tinisoft.Application.Customers.Commands.UpdateCustomerProfile;
using Tinisoft.Application.Customers.Commands.AddCustomerAddress;
using Tinisoft.Application.Customers.Queries.GetCustomerAddresses;
using Tinisoft.Application.Customers.Models;
using Tinisoft.Application.Customers.Queries.GetCart;
using Tinisoft.Application.Customers.Commands.AddCartItem;
using Tinisoft.Application.Customers.Commands.UpdateCartItem;
using Tinisoft.Application.Customers.Commands.RemoveCartItem;
using Tinisoft.Application.Customers.Commands.ClearCart;
using Tinisoft.Application.Customers.Commands.CheckoutFromCart;
using Tinisoft.Application.Customers.Queries.GetCustomerOrders;
using Tinisoft.Application.Customers.Queries.GetCustomerOrder;
using Tinisoft.Application.Customers.Commands.ApplyCouponToCart;
using Tinisoft.Application.Customers.Commands.RemoveCouponFromCart;

namespace Tinisoft.Customers.API.Controllers;

[ApiController]
[Route("api/customers")]
public class CustomersController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<CustomersController> _logger;

    public CustomersController(IMediator mediator, ILogger<CustomersController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpPost("register")]
    [Public]
    public async Task<ActionResult<CustomerAuthResponse>> Register([FromBody] RegisterCustomerCommand command)
    {
        var response = await _mediator.Send(command);
        return Ok(response);
    }

    [HttpPost("login")]
    [Public]
    public async Task<ActionResult<CustomerLoginResponse>> Login([FromBody] LoginCustomerCommand command)
    {
        var response = await _mediator.Send(command);
        return Ok(response);
    }

    [HttpGet("profile")]
    [RequireRole("Customer")]
    public async Task<ActionResult<CustomerDto>> GetProfile()
    {
        var response = await _mediator.Send(new GetCustomerProfileQuery());
        return Ok(response);
    }

    [HttpPut("profile")]
    [RequireRole("Customer")]
    public async Task<ActionResult<CustomerDto>> UpdateProfile([FromBody] UpdateCustomerProfileCommand command)
    {
        var response = await _mediator.Send(command);
        return Ok(response);
    }

    [HttpPost("addresses")]
    [RequireRole("Customer")]
    public async Task<ActionResult<CustomerAddressDto>> AddAddress([FromBody] AddCustomerAddressCommand command)
    {
        var response = await _mediator.Send(command);
        return Ok(response);
    }

    [HttpGet("addresses")]
    [RequireRole("Customer")]
    public async Task<ActionResult<List<CustomerAddressDto>>> GetAddresses()
    {
        var response = await _mediator.Send(new GetCustomerAddressesQuery());
        return Ok(response);
    }

    /// <summary>
    /// Müşteri sepeti
    /// </summary>
    [HttpGet("cart")]
    [RequireRole("Customer")]
    public async Task<ActionResult<GetCartResponse>> GetCart()
    {
        var response = await _mediator.Send(new GetCartQuery());
        return Ok(response);
    }

    /// <summary>
    /// Sepete ürün ekle
    /// </summary>
    [HttpPost("cart/items")]
    [RequireRole("Customer")]
    public async Task<ActionResult<AddCartItemResponse>> AddCartItem([FromBody] AddCartItemCommand command)
    {
        var response = await _mediator.Send(command);
        return Ok(response);
    }

    /// <summary>
    /// Sepet öğesini güncelle
    /// </summary>
    [HttpPut("cart/items/{id}")]
    [RequireRole("Customer")]
    public async Task<ActionResult<UpdateCartItemResponse>> UpdateCartItem(Guid id, [FromBody] UpdateCartItemCommand command)
    {
        command.CartItemId = id;
        var response = await _mediator.Send(command);
        return Ok(response);
    }

    /// <summary>
    /// Sepet öğesini kaldır
    /// </summary>
    [HttpDelete("cart/items/{id}")]
    [RequireRole("Customer")]
    public async Task<ActionResult<RemoveCartItemResponse>> RemoveCartItem(Guid id)
    {
        var command = new RemoveCartItemCommand { CartItemId = id };
        var response = await _mediator.Send(command);
        return Ok(response);
    }

    /// <summary>
    /// Sepeti temizle
    /// </summary>
    [HttpDelete("cart")]
    [RequireRole("Customer")]
    public async Task<ActionResult<ClearCartResponse>> ClearCart()
    {
        var command = new ClearCartCommand();
        var response = await _mediator.Send(command);
        return Ok(response);
    }

    /// <summary>
    /// Cart'tan sipariş oluştur (Checkout)
    /// </summary>
    [HttpPost("orders/checkout")]
    [RequireRole("Customer")]
    public async Task<ActionResult<CheckoutFromCartResponse>> CheckoutFromCart([FromBody] CheckoutFromCartCommand command)
    {
        var response = await _mediator.Send(command);
        return Ok(response);
    }

    /// <summary>
    /// Müşterinin siparişlerini listele
    /// </summary>
    [HttpGet("orders")]
    [RequireRole("Customer")]
    public async Task<ActionResult<GetCustomerOrdersResponse>> GetOrders([FromQuery] GetCustomerOrdersQuery query)
    {
        var response = await _mediator.Send(query);
        return Ok(response);
    }

    /// <summary>
    /// Müşterinin sipariş detayı
    /// </summary>
    [HttpGet("orders/{id}")]
    [RequireRole("Customer")]
    public async Task<ActionResult<GetCustomerOrderResponse>> GetOrder(Guid id)
    {
        var query = new GetCustomerOrderQuery { OrderId = id };
        var response = await _mediator.Send(query);
        return Ok(response);
    }

    /// <summary>
    /// Sepete kupon uygula
    /// </summary>
    [HttpPost("cart/apply-coupon")]
    [RequireRole("Customer")]
    public async Task<ActionResult<ApplyCouponToCartResponse>> ApplyCouponToCart([FromBody] ApplyCouponToCartCommand command)
    {
        var response = await _mediator.Send(command);
        return Ok(response);
    }

    /// <summary>
    /// Sepetten kuponu kaldır
    /// </summary>
    [HttpDelete("cart/coupon")]
    [RequireRole("Customer")]
    public async Task<ActionResult<RemoveCouponFromCartResponse>> RemoveCouponFromCart()
    {
        var command = new RemoveCouponFromCartCommand();
        var response = await _mediator.Send(command);
        return Ok(response);
    }
}


