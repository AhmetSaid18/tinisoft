using MediatR;

namespace Tinisoft.Application.Customers.Commands.CheckoutFromCart;

/// <summary>
/// Cart'tan sipariş oluştur (müşteri için)
/// </summary>
public class CheckoutFromCartCommand : IRequest<CheckoutFromCartResponse>
{
    // Shipping Address (CustomerAddressId veya manuel adres)
    public Guid? ShippingAddressId { get; set; } // Müşterinin kayıtlı adresi
    public string? ShippingAddressLine1 { get; set; } // Manuel adres
    public string? ShippingAddressLine2 { get; set; }
    public string? ShippingCity { get; set; }
    public string? ShippingState { get; set; }
    public string? ShippingPostalCode { get; set; }
    public string? ShippingCountry { get; set; }
    
    // Shipping Method
    public string? ShippingMethod { get; set; }
    
    // Payment (ileride payment provider entegrasyonu için)
    public string? PaymentProvider { get; set; }
    
    // Notes
    public string? OrderNotes { get; set; }
}

public class CheckoutFromCartResponse
{
    public Guid OrderId { get; set; }
    public string OrderNumber { get; set; } = string.Empty;
    public decimal Total { get; set; }
    public string Status { get; set; } = "Pending";
    public string? PaymentUrl { get; set; } // Payment provider'dan dönecek (ileride)
}

