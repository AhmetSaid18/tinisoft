using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Common.Interfaces;
using Finbuckle.MultiTenant;
using System.Text.Json;

namespace Tinisoft.Application.Customers.Queries.GetCustomerOrders;

public class GetCustomerOrdersQueryHandler : IRequestHandler<GetCustomerOrdersQuery, GetCustomerOrdersResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ICurrentCustomerService _currentCustomerService;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetCustomerOrdersQueryHandler> _logger;

    public GetCustomerOrdersQueryHandler(
        ApplicationDbContext dbContext,
        ICurrentCustomerService currentCustomerService,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetCustomerOrdersQueryHandler> logger)
    {
        _dbContext = dbContext;
        _currentCustomerService = currentCustomerService;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetCustomerOrdersResponse> Handle(GetCustomerOrdersQuery request, CancellationToken cancellationToken)
    {
        var customerId = _currentCustomerService.GetCurrentCustomerId();
        if (!customerId.HasValue)
        {
            throw new UnauthorizedAccessException("Müşteri bilgisi bulunamadı");
        }

        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Sadece bu müşterinin siparişlerini getir
        var query = _dbContext.Orders
            .AsNoTracking()
            .Where(o => o.TenantId == tenantId && o.CustomerId == customerId.Value);

        // Status filter
        if (!string.IsNullOrEmpty(request.Status))
        {
            query = query.Where(o => o.Status == request.Status);
        }

        // Sorting (en yeni önce)
        query = query.OrderByDescending(o => o.CreatedAt);

        // Pagination
        var validatedPageSize = request.PageSize > 100 ? 100 : (request.PageSize < 1 ? 20 : request.PageSize);
        var validatedPage = request.Page < 1 ? 1 : request.Page;

        var totalCount = await query.CountAsync(cancellationToken);

        var orders = await query
            .Include(o => o.OrderItems)
            .Skip((validatedPage - 1) * validatedPageSize)
            .Take(validatedPageSize)
            .ToListAsync(cancellationToken);

        var orderDtos = new List<CustomerOrderDto>();
        foreach (var order in orders)
        {
            var totals = JsonSerializer.Deserialize<OrderTotalsDto>(order.TotalsJson) ?? new OrderTotalsDto();

            orderDtos.Add(new CustomerOrderDto
            {
                Id = order.Id,
                OrderNumber = order.OrderNumber,
                Status = order.Status,
                Total = totals.Total,
                Currency = "TRY", // İleride order'dan alınabilir
                PaymentStatus = order.PaymentStatus,
                ShippingMethod = order.ShippingMethod,
                TrackingNumber = order.TrackingNumber,
                CreatedAt = order.CreatedAt,
                ItemCount = order.OrderItems.Sum(oi => oi.Quantity)
            });
        }

        return new GetCustomerOrdersResponse
        {
            Orders = orderDtos,
            TotalCount = totalCount,
            Page = validatedPage,
            PageSize = validatedPageSize
        };
    }

    private class OrderTotalsDto
    {
        public decimal Subtotal { get; set; }
        public decimal Tax { get; set; }
        public decimal Shipping { get; set; }
        public decimal Discount { get; set; }
        public decimal Total { get; set; }
    }
}

