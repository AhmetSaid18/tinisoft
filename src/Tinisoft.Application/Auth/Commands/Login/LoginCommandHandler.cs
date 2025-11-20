using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Auth.Commands.Login;

public class LoginCommandHandler : IRequestHandler<LoginCommand, LoginResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IPasswordHasher _passwordHasher;
    private readonly IJwtTokenService _jwtTokenService;
    private readonly ILogger<LoginCommandHandler> _logger;

    public LoginCommandHandler(
        IApplicationDbContext dbContext,
        IPasswordHasher passwordHasher,
        IJwtTokenService jwtTokenService,
        ILogger<LoginCommandHandler> logger)
    {
        _dbContext = dbContext;
        _passwordHasher = passwordHasher;
        _jwtTokenService = jwtTokenService;
        _logger = logger;
    }

    public async Task<LoginResponse> Handle(LoginCommand request, CancellationToken cancellationToken)
    {
        // User bul
        var user = await _dbContext.Set<User>()
            .FirstOrDefaultAsync(u => u.Email == request.Email, cancellationToken);

        if (user == null)
        {
            throw new UnauthorizedException("Email veya şifre hatalı.");
        }

        if (!user.IsActive)
        {
            throw new UnauthorizedException("Hesabınız aktif değil.");
        }

        // Password kontrolü
        if (!_passwordHasher.VerifyPassword(request.Password, user.PasswordHash))
        {
            throw new UnauthorizedException("Email veya şifre hatalı.");
        }

        Guid? tenantId = null;
        string? tenantRole = null;

        // TenantAdmin ise tenant bilgilerini al
        if (user.SystemRole == "TenantAdmin")
        {
            var userTenantRole = await _dbContext.Set<UserTenantRole>()
                .Include(utr => utr.Tenant)
                .Where(utr => utr.UserId == user.Id)
                .FirstOrDefaultAsync(cancellationToken);

            if (userTenantRole != null)
            {
                tenantId = userTenantRole.TenantId;
                tenantRole = userTenantRole.Role;

                // Tenant aktif mi kontrol et
                if (userTenantRole.Tenant != null && !userTenantRole.Tenant.IsActive)
                {
                    throw new UnauthorizedException("Tenant'ınız aktif değil.");
                }
            }
        }
        else if (request.TenantId.HasValue)
        {
            // Customer ise ve tenantId verilmişse, o tenant'a erişimi var mı kontrol et
            var userTenantRole = await _dbContext.Set<UserTenantRole>()
                .FirstOrDefaultAsync(utr => utr.UserId == user.Id && utr.TenantId == request.TenantId.Value, cancellationToken);

            if (userTenantRole != null)
            {
                tenantId = userTenantRole.TenantId;
                tenantRole = userTenantRole.Role;
            }
        }

        _logger.LogInformation("User logged in: {Email} - Role: {Role}", user.Email, user.SystemRole);

        // Token oluştur
        var token = _jwtTokenService.GenerateToken(user.Id, user.Email, user.SystemRole, tenantId, tenantRole);

        return new LoginResponse
        {
            UserId = user.Id,
            Email = user.Email,
            Token = token,
            TenantId = tenantId,
            SystemRole = user.SystemRole,
            TenantRole = tenantRole
        };
    }
}



