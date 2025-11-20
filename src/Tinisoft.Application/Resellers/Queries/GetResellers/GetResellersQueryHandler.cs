using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Resellers.Queries.GetResellers;

public class GetResellersQueryHandler : IRequestHandler<GetResellersQuery, GetResellersResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetResellersQueryHandler> _logger;

    public GetResellersQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetResellersQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetResellersResponse> Handle(GetResellersQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var query = _dbContext.Resellers
            .Where(r => r.TenantId == tenantId)
            .AsQueryable();

        if (request.IsActive.HasValue)
        {
            query = query.Where(r => r.IsActive == request.IsActive.Value);
        }

        var totalCount = await query.CountAsync(cancellationToken);

        var resellers = await query
            .OrderByDescending(r => r.CreatedAt)
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
            .Select(r => new ResellerDto
            {
                Id = r.Id,
                CompanyName = r.CompanyName,
                Email = r.Email,
                Phone = r.Phone,
                City = r.City,
                IsActive = r.IsActive,
                CreditLimit = r.CreditLimit,
                UsedCredit = r.UsedCredit,
                PaymentTermDays = r.PaymentTermDays,
                DefaultDiscountPercent = r.DefaultDiscountPercent,
                CreatedAt = r.CreatedAt
            })
            .ToListAsync(cancellationToken);

        return new GetResellersResponse
        {
            Resellers = resellers,
            TotalCount = totalCount,
            Page = request.Page,
            PageSize = request.PageSize
        };
    }
}



