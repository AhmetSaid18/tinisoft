using MediatR;

namespace Tinisoft.Application.Resellers.Queries.GetResellers;

public class GetResellersQuery : IRequest<GetResellersResponse>
{
    public bool? IsActive { get; set; }
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 20;
}

public class GetResellersResponse
{
    public List<ResellerDto> Resellers { get; set; } = new();
    public int TotalCount { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
}

public class ResellerDto
{
    public Guid Id { get; set; }
    public string CompanyName { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string? Phone { get; set; }
    public string? City { get; set; }
    public bool IsActive { get; set; }
    public decimal CreditLimit { get; set; }
    public decimal UsedCredit { get; set; }
    public int PaymentTermDays { get; set; }
    public decimal DefaultDiscountPercent { get; set; }
    public DateTime CreatedAt { get; set; }
}



