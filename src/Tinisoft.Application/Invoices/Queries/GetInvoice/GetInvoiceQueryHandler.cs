using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Exceptions;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Invoices.Queries.GetInvoice;

public class GetInvoiceQueryHandler : IRequestHandler<GetInvoiceQuery, GetInvoiceResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;

    public GetInvoiceQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
    }

    public async Task<GetInvoiceResponse> Handle(GetInvoiceQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var invoice = await _dbContext.Invoices
            .Include(i => i.Order)
            .Include(i => i.Items)
            .ThenInclude(ii => ii.Product)
            .FirstOrDefaultAsync(i => i.Id == request.InvoiceId && i.TenantId == tenantId, cancellationToken);

        if (invoice == null)
        {
            throw new NotFoundException("Fatura", request.InvoiceId);
        }

        return new GetInvoiceResponse
        {
            InvoiceId = invoice.Id,
            InvoiceNumber = invoice.InvoiceNumber,
            InvoiceSerial = invoice.InvoiceSerial,
            InvoiceDate = invoice.InvoiceDate,
            InvoiceType = invoice.InvoiceType,
            ProfileId = invoice.ProfileId,
            Status = invoice.Status,
            StatusMessage = invoice.StatusMessage,
            
            OrderId = invoice.OrderId,
            OrderNumber = invoice.Order?.OrderNumber ?? string.Empty,
            
            CustomerName = invoice.CustomerName,
            CustomerEmail = invoice.CustomerEmail,
            CustomerVKN = invoice.CustomerVKN,
            
            Subtotal = invoice.Subtotal,
            TaxAmount = invoice.TaxAmount,
            DiscountAmount = invoice.DiscountAmount,
            ShippingAmount = invoice.ShippingAmount,
            Total = invoice.Total,
            Currency = invoice.Currency,
            
            GIBInvoiceId = invoice.GIBInvoiceId,
            GIBInvoiceNumber = invoice.GIBInvoiceNumber,
            GIBSentAt = invoice.GIBSentAt,
            GIBApprovedAt = invoice.GIBApprovedAt,
            GIBApprovalStatus = invoice.GIBApprovalStatus,
            
            PDFUrl = request.IncludePDF ? invoice.PDFUrl : null,
            PDFGeneratedAt = invoice.PDFGeneratedAt,
            
            Items = invoice.Items.OrderBy(ii => ii.Position).Select(ii => new InvoiceItemResponse
            {
                InvoiceItemId = ii.Id,
                ProductId = ii.ProductId,
                ProductVariantId = ii.ProductVariantId,
                ItemName = ii.ItemName,
                ItemCode = ii.ItemCode,
                Quantity = ii.Quantity,
                Unit = ii.Unit,
                UnitPrice = ii.UnitPrice,
                LineTotal = ii.LineTotal,
                TaxRatePercent = ii.TaxRatePercent,
                TaxAmount = ii.TaxAmount,
                LineTotalWithTax = ii.LineTotalWithTax,
                Position = ii.Position
            }).ToList(),
            
            CreatedAt = invoice.CreatedAt,
            UpdatedAt = invoice.UpdatedAt ?? invoice.CreatedAt
        };
    }
}



