namespace Tinisoft.Application.Customers.Models;

public class CustomerAddressDto
{
    public Guid AddressId { get; set; }
    public string AddressLine1 { get; set; } = string.Empty;
    public string? AddressLine2 { get; set; }
    public string City { get; set; } = string.Empty;
    public string? State { get; set; }
    public string PostalCode { get; set; } = string.Empty;
    public string Country { get; set; } = "TR";
    public string? Phone { get; set; }
    public string? AddressTitle { get; set; }
    public bool IsDefaultShipping { get; set; }
    public bool IsDefaultBilling { get; set; }
}


