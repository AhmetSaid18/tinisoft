using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Domain.Common;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Auth.Commands.Register;

public class RegisterCommandHandler : IRequestHandler<RegisterCommand, RegisterResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly ITenantStoreService _tenantStoreService;
    private readonly IPasswordHasher _passwordHasher;
    private readonly IJwtTokenService _jwtTokenService;
    private readonly ILogger<RegisterCommandHandler> _logger;

    public RegisterCommandHandler(
        IApplicationDbContext dbContext,
        ITenantStoreService tenantStoreService,
        IPasswordHasher passwordHasher,
        IJwtTokenService jwtTokenService,
        ILogger<RegisterCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantStoreService = tenantStoreService;
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
            var existingTenant = await _dbContext.Set<Entities.Tenant>()
                .FirstOrDefaultAsync(t => t.Slug == request.TenantSlug, cancellationToken);

            if (existingTenant != null)
            {
                throw new BadRequestException("Bu slug zaten kullanılıyor.");
            }

            // Plan bul (Free Plan - aktif planları al, ilkini kullan)
            var defaultPlan = await _dbContext.Set<Plan>()
                .Where(p => p.IsActive)
                .OrderBy(p => p.MonthlyPrice) // En ucuz plan (Free Plan)
                .FirstOrDefaultAsync(cancellationToken);

            if (defaultPlan == null)
            {
                throw new BadRequestException("Sistemde aktif plan bulunamadı.");
            }

            var tenant = new Entities.Tenant
            {
                Name = request.TenantName,
                Slug = request.TenantSlug,
                PlanId = defaultPlan.Id,
                IsActive = true,
                SubscriptionStartDate = DateTime.UtcNow
            };

            _dbContext.Set<Entities.Tenant>().Add(tenant);
            await _dbContext.SaveChangesAsync(cancellationToken); // Tenant ID için

            tenantId = tenant.Id;

            // TenantStoreService'e de yaz (Finbuckle.MultiTenant için gerekli)
            await _tenantStoreService.AddTenantAsync(
                tenant.Id.ToString(),
                tenant.Slug, // Host strategy için slug kullanılacak
                tenant.Name,
                cancellationToken);

            // Domain ekle (eğer verilmişse)
            if (!string.IsNullOrWhiteSpace(request.Domain))
            {
                var domain = new Entities.Domain
                {
                    TenantId = tenant.Id,
                    Host = request.Domain,
                    IsPrimary = true,
                    IsVerified = false // Domain doğrulaması yapılacak
                };
                _dbContext.Set<Entities.Domain>().Add(domain);
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



