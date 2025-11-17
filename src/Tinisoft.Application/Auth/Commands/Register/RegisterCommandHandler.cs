using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Domain.Common;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Infrastructure.Services;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Auth.Commands.Register;

public class RegisterCommandHandler : IRequestHandler<RegisterCommand, RegisterResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IPasswordHasher _passwordHasher;
    private readonly IJwtTokenService _jwtTokenService;
    private readonly ILogger<RegisterCommandHandler> _logger;

    public RegisterCommandHandler(
        ApplicationDbContext dbContext,
        IPasswordHasher passwordHasher,
        IJwtTokenService jwtTokenService,
        ILogger<RegisterCommandHandler> logger)
    {
        _dbContext = dbContext;
        _passwordHasher = passwordHasher;
        _jwtTokenService = jwtTokenService;
        _logger = logger;
    }

    public async Task<RegisterResponse> Handle(RegisterCommand request, CancellationToken cancellationToken)
    {
        // Email kontrolü
        var existingUser = await _dbContext.Set<User>()
            .FirstOrDefaultAsync(u => u.Email == request.Email, cancellationToken);

        if (existingUser != null)
        {
            throw new BadRequestException("Bu email adresi zaten kullanılıyor.");
        }

        // Password hash
        var passwordHash = _passwordHasher.HashPassword(request.Password);

        // User oluştur
        var user = new User
        {
            Email = request.Email,
            PasswordHash = passwordHash,
            FirstName = request.FirstName,
            LastName = request.LastName,
            SystemRole = request.SystemRole,
            IsActive = true,
            EmailVerified = false // Email doğrulama sonrası true olacak
        };

        _dbContext.Set<User>().Add(user);
        Guid? tenantId = null;

        // TenantAdmin ise Tenant oluştur
        if (request.SystemRole == Roles.TenantAdmin)
        {
            if (string.IsNullOrWhiteSpace(request.TenantName) || string.IsNullOrWhiteSpace(request.TenantSlug))
            {
                throw new BadRequestException("TenantAdmin için TenantName ve TenantSlug gereklidir.");
            }

            // Slug kontrolü
            var existingTenant = await _dbContext.Set<Tenant>()
                .FirstOrDefaultAsync(t => t.Slug == request.TenantSlug, cancellationToken);

            if (existingTenant != null)
            {
                throw new BadRequestException("Bu slug zaten kullanılıyor.");
            }

            // Plan bul (default plan - şimdilik ilk planı al)
            var defaultPlan = await _dbContext.Set<Plan>()
                .FirstOrDefaultAsync(cancellationToken);

            if (defaultPlan == null)
            {
                throw new BadRequestException("Sistemde aktif plan bulunamadı.");
            }

            var tenant = new Tenant
            {
                Name = request.TenantName,
                Slug = request.TenantSlug,
                PlanId = defaultPlan.Id,
                IsActive = true,
                SubscriptionStartDate = DateTime.UtcNow
            };

            _dbContext.Set<Tenant>().Add(tenant);
            await _dbContext.SaveChangesAsync(cancellationToken); // Tenant ID için

            tenantId = tenant.Id;

            // Domain ekle (eğer verilmişse)
            if (!string.IsNullOrWhiteSpace(request.Domain))
            {
                var domain = new Domain
                {
                    TenantId = tenant.Id,
                    Host = request.Domain,
                    IsPrimary = true,
                    IsVerified = false // Domain doğrulaması yapılacak
                };
                _dbContext.Set<Domain>().Add(domain);
            }

            // UserTenantRole oluştur (Owner)
            var userTenantRole = new UserTenantRole
            {
                UserId = user.Id,
                TenantId = tenant.Id,
                Role = Roles.Owner
            };
            _dbContext.Set<UserTenantRole>().Add(userTenantRole);
        }

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("User registered: {Email} - Role: {Role}", user.Email, user.SystemRole);

        // Token oluştur
        var tenantRole = request.SystemRole == Roles.TenantAdmin ? Roles.Owner : null;
        var token = _jwtTokenService.GenerateToken(user.Id, user.Email, user.SystemRole, tenantId, tenantRole);

        return new RegisterResponse
        {
            UserId = user.Id,
            Email = user.Email,
            Token = token,
            TenantId = tenantId,
            SystemRole = user.SystemRole
        };
    }
}

