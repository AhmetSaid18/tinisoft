using MediatR;

namespace Tinisoft.Application.Auth.Commands.Login;

public class LoginCommand : IRequest<LoginResponse>
{
    public string Email { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public Guid? TenantId { get; set; } // Multi-tenant için (opsiyonel)
}

public class LoginResponse
{
    public Guid UserId { get; set; }
    public string Email { get; set; } = string.Empty;
    public string Token { get; set; } = string.Empty;
    public Guid? TenantId { get; set; }
    public string SystemRole { get; set; } = string.Empty;
    public string? TenantRole { get; set; }
}



