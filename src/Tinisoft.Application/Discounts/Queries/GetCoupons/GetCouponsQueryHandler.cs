using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Discounts.Queries.GetCoupons;

public class GetCouponsQueryHandler : IRequestHandler<GetCouponsQuery, GetCouponsResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetCouponsQueryHandler> _logger;

    public GetCouponsQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetCouponsQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetCouponsResponse> Handle(GetCouponsQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var query = _dbContext.Coupons
            .AsNoTracking()
            .Where(c => c.TenantId == tenantId);

        // Filter by IsActive
        if (request.IsActive.HasValue)
        {
            query = query.Where(c => c.IsActive == request.IsActive.Value);
        }

        // Search
        if (!string.IsNullOrEmpty(request.Search))
        {
            var searchLower = request.Search.ToLower();
            query = query.Where(c =>
                c.Code.ToLower().Contains(searchLower) ||
                c.Name.ToLower().Contains(searchLower) ||
                (c.Description != null && c.Description.ToLower().Contains(searchLower)));
        }

        // Sorting (en yeni önce)
        query = query.OrderByDescending(c => c.CreatedAt);

        // Pagination
        var validatedPageSize = request.PageSize > 100 ? 100 : (request.PageSize < 1 ? 20 : request.PageSize);
        var validatedPage = request.Page < 1 ? 1 : request.Page;

        var totalCount = await query.CountAsync(cancellationToken);

        var coupons = await query
            .Skip((validatedPage - 1) * validatedPageSize)
            .Take(validatedPageSize)
            .ToListAsync(cancellationToken);

        var couponDtos = coupons.Select(c => new CouponDto
        {
            Id = c.Id,
            Code = c.Code,
            Name = c.Name,
            Description = c.Description,
            DiscountType = c.DiscountType,
            DiscountValue = c.DiscountValue,
            Currency = c.Currency,
            MinOrderAmount = c.MinOrderAmount,
            MaxDiscountAmount = c.MaxDiscountAmount,
            MaxUsageCount = c.MaxUsageCount,
            MaxUsagePerCustomer = c.MaxUsagePerCustomer,
            ValidFrom = c.ValidFrom,
            ValidTo = c.ValidTo,
            IsActive = c.IsActive,
            UsageCount = c.UsageCount,
            CreatedAt = c.CreatedAt
        }).ToList();

        return new GetCouponsResponse
        {
            Coupons = couponDtos,
            TotalCount = totalCount,
            Page = validatedPage,
            PageSize = validatedPageSize
        };
    }
}



