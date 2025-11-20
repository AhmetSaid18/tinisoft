using MediatR;

namespace Tinisoft.Application.Auth.Commands.Register;

public class RegisterCommand : IRequest<RegisterResponse>
{
    public string Email { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public string? FirstName { get; set; }
    public string? LastName { get; set; }
    public string SystemRole { get; set; } = "Customer"; // SystemAdmin, TenantAdmin, Customer
    
    // TenantAdmin için gerekli bilgiler
    public string? TenantName { get; set; }
    public string? TenantSlug { get; set; }
    public string? Domain { get; set; } // Domain doğrulaması için (şimdilik sadece kayıt)
}

public class RegisterResponse
{
    public Guid UserId { get; set; }
    public string Email { get; set; } = string.Empty;
    public string Token { get; set; } = string.Empty;
    public Guid? TenantId { get; set; }
    public string SystemRole { get; set; } = string.Empty;
}



