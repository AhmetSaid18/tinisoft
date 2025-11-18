using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Invoices.Queries.GetInvoices;

public class GetInvoicesQueryHandler : IRequestHandler<GetInvoicesQuery, GetInvoicesResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;

    public GetInvoicesQueryHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
    }

    public async Task<GetInvoicesResponse> Handle(GetInvoicesQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Base query
        var query = _dbContext.Invoices
            .Include(i => i.Order)
            .Where(i => i.TenantId == tenantId)
            .AsQueryable();

        // Filters
        if (!string.IsNullOrEmpty(request.Status))
        {
            query = query.Where(i => i.Status == request.Status);
        }

        if (!string.IsNullOrEmpty(request.InvoiceType))
        {
            query = query.Where(i => i.InvoiceType == request.InvoiceType);
        }

        if (request.OrderId.HasValue)
        {
            query = query.Where(i => i.OrderId == request.OrderId.Value);
        }

        if (request.StartDate.HasValue)
        {
            query = query.Where(i => i.InvoiceDate >= request.StartDate.Value);
        }

        if (request.EndDate.HasValue)
        {
            query = query.Where(i => i.InvoiceDate <= request.EndDate.Value);
        }

        if (!string.IsNullOrEmpty(request.CustomerName))
        {
            query = query.Where(i => i.CustomerName.Contains(request.CustomerName));
        }

        if (!string.IsNullOrEmpty(request.InvoiceNumber))
        {
            query = query.Where(i => i.InvoiceNumber.Contains(request.InvoiceNumber));
        }

        // Total count
        var totalCount = await query.CountAsync(cancellationToken);

        // Sorting
        var sortBy = request.SortBy?.ToLower() ?? "invoicedate";
        var sortOrder = request.SortOrder?.ToUpper() ?? "DESC";

        query = sortBy switch
        {
            "invoicedate" => sortOrder == "ASC"
                ? query.OrderBy(i => i.InvoiceDate)
                : query.OrderByDescending(i => i.InvoiceDate),
            "invoicenumber" => sortOrder == "ASC"
                ? query.OrderBy(i => i.InvoiceNumber)
                : query.OrderByDescending(i => i.InvoiceNumber),
            "total" => sortOrder == "ASC"
                ? query.OrderBy(i => i.Total)
                : query.OrderByDescending(i => i.Total),
            "status" => sortOrder == "ASC"
                ? query.OrderBy(i => i.Status)
                : query.OrderByDescending(i => i.Status),
            _ => query.OrderByDescending(i => i.InvoiceDate)
        };

        // Pagination
        var invoices = await query
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
            .Select(i => new InvoiceListItemDto
            {
                InvoiceId = i.Id,
                InvoiceNumber = i.InvoiceNumber,
                InvoiceSerial = i.InvoiceSerial,
                InvoiceDate = i.InvoiceDate,
                InvoiceType = i.InvoiceType,
                Status = i.Status,
                StatusMessage = i.StatusMessage,
                OrderId = i.OrderId,
                OrderNumber = i.Order != null ? i.Order.OrderNumber : null,
                CustomerName = i.CustomerName,
                CustomerEmail = i.CustomerEmail,
                Total = i.Total,
                Currency = i.Currency,
                GIBInvoiceId = i.GIBInvoiceId,
                GIBInvoiceNumber = i.GIBInvoiceNumber,
                GIBSentAt = i.GIBSentAt,
                GIBApprovalStatus = i.GIBApprovalStatus,
                IsCancelled = i.IsCancelled,
                CancelledAt = i.CancelledAt,
                CreatedAt = i.CreatedAt
            })
            .ToListAsync(cancellationToken);

        return new GetInvoicesResponse
        {
            Invoices = invoices,
            TotalCount = totalCount,
            Page = request.Page,
            PageSize = request.PageSize
        };
    }
}

