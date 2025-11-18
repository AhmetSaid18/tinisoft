using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Shipping.Services;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Shipping.Commands.CreateShipment;

public class CreateShipmentCommandHandler : IRequestHandler<CreateShipmentCommand, CreateShipmentResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IShippingServiceFactory _shippingServiceFactory;
    private readonly ILogger<CreateShipmentCommandHandler> _logger;

    public CreateShipmentCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IShippingServiceFactory shippingServiceFactory,
        ILogger<CreateShipmentCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _shippingServiceFactory = shippingServiceFactory;
        _logger = logger;
    }

    public async Task<CreateShipmentResponse> Handle(CreateShipmentCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // ShippingProvider'ı kontrol et
        var provider = await _dbContext.ShippingProviders
            .FirstOrDefaultAsync(sp => 
                sp.Id == request.ShippingProviderId && 
                sp.TenantId == tenantId && 
                sp.IsActive, cancellationToken);

        if (provider == null)
        {
            throw new NotFoundException("ShippingProvider", request.ShippingProviderId);
        }

        if (string.IsNullOrEmpty(provider.ApiKey))
        {
            return new CreateShipmentResponse
            {
                Success = false,
                ErrorMessage = "Kargo firması için API key tanımlanmamış"
            };
        }

        // Order'ı kontrol et
        var order = await _dbContext.Orders
            .AsNoTracking()
            .FirstOrDefaultAsync(o => o.Id == request.OrderId && o.TenantId == tenantId, cancellationToken);

        if (order == null)
        {
            throw new NotFoundException("Order", request.OrderId);
        }

        if (!_shippingServiceFactory.IsProviderSupported(provider.ProviderCode))
        {
            return new CreateShipmentResponse
            {
                Success = false,
                ErrorMessage = $"Kargo firması desteklenmiyor: {provider.ProviderCode}"
            };
        }

        try
        {
            var shippingService = _shippingServiceFactory.GetService(provider.ProviderCode);
            
            var shipmentRequest = new CreateShipmentRequest
            {
                RecipientName = request.RecipientName,
                RecipientPhone = request.RecipientPhone,
                AddressLine1 = request.AddressLine1,
                AddressLine2 = request.AddressLine2,
                City = request.City,
                State = request.State,
                PostalCode = request.PostalCode,
                Country = request.Country,
                Weight = request.Weight,
                Width = request.Width,
                Height = request.Height,
                Depth = request.Depth,
                PackageCount = request.PackageCount,
                OrderNumber = order.OrderNumber
            };

            var shipmentResult = await shippingService.CreateShipmentAsync(
                provider.ProviderCode,
                shipmentRequest,
                cancellationToken);

            if (!shipmentResult.Success)
            {
                return new CreateShipmentResponse
                {
                    Success = false,
                    ErrorMessage = shipmentResult.ErrorMessage ?? "Gönderi oluşturulamadı"
                };
            }

            // Shipment kaydı oluştur
            var shipment = new Domain.Entities.Shipment
            {
                TenantId = tenantId,
                OrderId = request.OrderId,
                ShippingProviderId = request.ShippingProviderId,
                TrackingNumber = shipmentResult.TrackingNumber,
                LabelUrl = shipmentResult.LabelUrl,
                Status = "Created",
                Weight = request.Weight,
                Width = request.Width,
                Height = request.Height,
                Depth = request.Depth,
                PackageCount = request.PackageCount,
                ShippingCost = shipmentResult.ShippingCost,
                Currency = "TRY",
                RecipientName = request.RecipientName,
                RecipientPhone = request.RecipientPhone,
                AddressLine1 = request.AddressLine1,
                AddressLine2 = request.AddressLine2,
                City = request.City,
                State = request.State,
                PostalCode = request.PostalCode,
                Country = request.Country,
                ProviderResponseJson = shipmentResult.ProviderResponseJson,
                ShippedAt = DateTime.UtcNow
            };

            _dbContext.Shipments.Add(shipment);
            await _dbContext.SaveChangesAsync(cancellationToken);

            _logger.LogInformation("Shipment created: {TrackingNumber} for order {OrderId}", 
                shipmentResult.TrackingNumber, request.OrderId);

            return new CreateShipmentResponse
            {
                ShipmentId = shipment.Id,
                TrackingNumber = shipmentResult.TrackingNumber,
                LabelUrl = shipmentResult.LabelUrl,
                ShippingCost = shipmentResult.ShippingCost,
                Success = true
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating shipment for order {OrderId}", request.OrderId);
            return new CreateShipmentResponse
            {
                Success = false,
                ErrorMessage = $"Gönderi oluşturulurken hata oluştu: {ex.Message}"
            };
        }
    }
}

