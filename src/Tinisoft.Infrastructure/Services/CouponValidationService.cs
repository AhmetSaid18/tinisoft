using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Discounts.Services;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Infrastructure.Services;

public class CouponValidationService : ICouponValidationService
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CouponValidationService> _logger;

    public CouponValidationService(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CouponValidationService> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CouponValidationResult> ValidateCouponAsync(
        string couponCode,
        Guid? customerId,
        decimal cartSubtotal,
        List<Guid> productIds,
        List<Guid> categoryIds,
        CancellationToken cancellationToken = default)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Kuponu bul (navigation property'lerle birlikte)
        var coupon = await _dbContext.Coupons
            .Include(c => c.ApplicableProducts)
            .Include(c => c.ApplicableCategories)
            .Include(c => c.ExcludedProducts)
            .Include(c => c.ApplicableCustomers)
            .AsSplitQuery()
            .AsNoTracking()
            .FirstOrDefaultAsync(c => c.TenantId == tenantId && 
                c.Code.ToUpper() == couponCode.ToUpper(), cancellationToken);

        if (coupon == null)
        {
            return new CouponValidationResult
            {
                IsValid = false,
                ErrorMessage = "Kupon kodu bulunamadı"
            };
        }

        // Aktif mi?
        if (!coupon.IsActive)
        {
            return new CouponValidationResult
            {
                IsValid = false,
                ErrorMessage = "Bu kupon aktif değil"
            };
        }

        // Tarih kontrolü
        var now = DateTime.UtcNow;
        if (coupon.ValidFrom.HasValue && now < coupon.ValidFrom.Value)
        {
            return new CouponValidationResult
            {
                IsValid = false,
                ErrorMessage = "Bu kupon henüz geçerli değil"
            };
        }

        if (coupon.ValidTo.HasValue && now > coupon.ValidTo.Value)
        {
            return new CouponValidationResult
            {
                IsValid = false,
                ErrorMessage = "Bu kuponun süresi dolmuş"
            };
        }

        // Minimum sipariş tutarı kontrolü
        if (coupon.MinOrderAmount.HasValue && cartSubtotal < coupon.MinOrderAmount.Value)
        {
            return new CouponValidationResult
            {
                IsValid = false,
                ErrorMessage = $"Bu kupon için minimum sipariş tutarı {coupon.MinOrderAmount.Value:C} olmalıdır"
            };
        }

        // Toplam kullanım limiti kontrolü
        if (coupon.MaxUsageCount.HasValue)
        {
            var usageCount = await _dbContext.CouponUsages
                .CountAsync(cu => cu.CouponId == coupon.Id, cancellationToken);

            if (usageCount >= coupon.MaxUsageCount.Value)
            {
                return new CouponValidationResult
                {
                    IsValid = false,
                    ErrorMessage = "Bu kuponun kullanım limiti dolmuş"
                };
            }
        }

        // Müşteri başına kullanım limiti kontrolü
        if (customerId.HasValue && coupon.MaxUsagePerCustomer.HasValue)
        {
            var customerUsageCount = await _dbContext.CouponUsages
                .CountAsync(cu => cu.CouponId == coupon.Id && cu.CustomerId == customerId.Value, cancellationToken);

            if (customerUsageCount >= coupon.MaxUsagePerCustomer.Value)
            {
                return new CouponValidationResult
                {
                    IsValid = false,
                    ErrorMessage = "Bu kuponu daha önce kullandınız"
                };
            }
        }

        // Müşteri kısıtlaması kontrolü
        if (!coupon.AppliesToAllCustomers && customerId.HasValue)
        {
            var isCustomerAllowed = await _dbContext.CouponCustomers
                .AnyAsync(cc => cc.CouponId == coupon.Id && cc.CustomerId == customerId.Value, cancellationToken);

            if (!isCustomerAllowed)
            {
                return new CouponValidationResult
                {
                    IsValid = false,
                    ErrorMessage = "Bu kupon sizin için geçerli değil"
                };
            }
        }

        // Ürün/Kategori kısıtlaması kontrolü
        if (!coupon.AppliesToAllProducts)
        {
            bool isApplicable = false;

            // Belirli ürünlere uygulanabilir mi?
            if (coupon.ApplicableProducts.Any() && productIds.Any())
            {
                var applicableProductIds = coupon.ApplicableProducts.Select(cp => cp.ProductId).ToList();
                isApplicable = productIds.Any(pid => applicableProductIds.Contains(pid));
            }

            // Belirli kategorilere uygulanabilir mi?
            if (!isApplicable && coupon.ApplicableCategories.Any() && categoryIds.Any())
            {
                var applicableCategoryIds = coupon.ApplicableCategories.Select(cc => cc.CategoryId).ToList();
                isApplicable = categoryIds.Any(cid => applicableCategoryIds.Contains(cid));
            }

            if (!isApplicable)
            {
                return new CouponValidationResult
                {
                    IsValid = false,
                    ErrorMessage = "Bu kupon sepetinizdeki ürünlere uygulanamaz"
                };
            }
        }

        // Hariç tutulan ürünler kontrolü
        if (coupon.ExcludedProducts.Any() && productIds.Any())
        {
            var excludedProductIds = coupon.ExcludedProducts.Select(cep => cep.ProductId).ToList();
            if (productIds.Any(pid => excludedProductIds.Contains(pid)))
            {
                return new CouponValidationResult
                {
                    IsValid = false,
                    ErrorMessage = "Bu kupon sepetinizdeki bazı ürünlere uygulanamaz"
                };
            }
        }

        // İndirim tutarını hesapla (şimdilik basit hesaplama, cart items validation'dan sonra hesaplanacak)
        // Bu metod sadece validation için, gerçek hesaplama ApplyCouponToCartCommandHandler'da yapılacak
        var discountAmount = 0m; // Validation'da sadece kontrol yapıyoruz, hesaplama cart items ile yapılacak

        return new CouponValidationResult
        {
            IsValid = true,
            Coupon = coupon,
            DiscountAmount = discountAmount
        };
    }

    public decimal CalculateDiscount(
        Domain.Entities.Coupon coupon,
        List<Tinisoft.Application.Discounts.Services.CartItemForDiscount> cartItems)
    {
        // Uygulanabilir ürünlerin toplamını hesapla
        decimal applicableSubtotal = 0;

        if (coupon.AppliesToAllProducts)
        {
            // Tüm ürünlere uygulanıyorsa, tüm cart items'ın toplamı
            applicableSubtotal = cartItems.Sum(ci => ci.TotalPrice);
        }
        else
        {
            // Belirli ürünlere/kategorilere uygulanıyorsa, sadece o ürünlerin toplamını al
            var applicableProductIds = coupon.ApplicableProducts.Select(cp => cp.ProductId).ToList();
            var applicableCategoryIds = coupon.ApplicableCategories.Select(cc => cc.CategoryId).ToList();
            var excludedProductIds = coupon.ExcludedProducts.Select(cep => cep.ProductId).ToList();

            foreach (var cartItem in cartItems)
            {
                // Hariç tutulan ürünler kontrolü
                if (excludedProductIds.Contains(cartItem.ProductId))
                {
                    continue; // Bu ürün hariç tutulmuş
                }

                bool isApplicable = false;

                // Belirli ürünlere uygulanıyorsa
                if (applicableProductIds.Any() && applicableProductIds.Contains(cartItem.ProductId))
                {
                    isApplicable = true;
                }

                // Belirli kategorilere uygulanıyorsa
                if (!isApplicable && applicableCategoryIds.Any() && 
                    cartItem.CategoryIds.Any(cid => applicableCategoryIds.Contains(cid)))
                {
                    isApplicable = true;
                }

                if (isApplicable)
                {
                    applicableSubtotal += cartItem.TotalPrice;
                }
            }
        }

        decimal discount = 0;

        switch (coupon.DiscountType.ToLower())
        {
            case "percentage":
                discount = applicableSubtotal * (coupon.DiscountValue / 100);
                // Maksimum indirim tutarı kontrolü
                if (coupon.MaxDiscountAmount.HasValue && discount > coupon.MaxDiscountAmount.Value)
                {
                    discount = coupon.MaxDiscountAmount.Value;
                }
                break;

            case "fixedamount":
                discount = coupon.DiscountValue;
                // İndirim, uygulanabilir sepet tutarından fazla olamaz
                if (discount > applicableSubtotal)
                {
                    discount = applicableSubtotal;
                }
                break;

            case "freeshipping":
                // Ücretsiz kargo - shipping cost'u 0 yapılacak (burada 0 döndürüyoruz, cart'ta shipping hesaplanırken uygulanacak)
                discount = 0;
                break;

            default:
                discount = 0;
                break;
        }

        return Math.Round(discount, 2, MidpointRounding.AwayFromZero);
    }
}

