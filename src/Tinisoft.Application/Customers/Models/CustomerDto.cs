namespace Tinisoft.Application.Customers.Models;

public class CustomerDto
{
    public Guid Id { get; set; }
    public string Email { get; set; } = string.Empty;
    public string? FirstName { get; set; }
    public string? LastName { get; set; }
    public string? Phone { get; set; }
    public bool EmailVerified { get; set; }
    public DateTime CreatedAt { get; set; }
}




