namespace Tinisoft.Application.Discounts.Services;

/// <summary>
/// Kupon doğrulama servisi
/// </summary>
public interface ICouponValidationService
{
    /// <summary>
    /// Kupon kodunu doğrula ve uygulanabilirliğini kontrol et
    /// </summary>
    Task<CouponValidationResult> ValidateCouponAsync(
        string couponCode,
        Guid? customerId,
        decimal cartSubtotal,
        List<Guid> productIds,
        List<Guid> categoryIds,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Kupon indirim tutarını hesapla (cart items bazlı - ürün/kategori bazlı indirim için)
    /// </summary>
    decimal CalculateDiscount(
        Domain.Entities.Coupon coupon,
        List<CartItemForDiscount> cartItems);
}

public class CouponValidationResult
{
    public bool IsValid { get; set; }
    public string? ErrorMessage { get; set; }
    public Domain.Entities.Coupon? Coupon { get; set; }
    public decimal DiscountAmount { get; set; }
}



