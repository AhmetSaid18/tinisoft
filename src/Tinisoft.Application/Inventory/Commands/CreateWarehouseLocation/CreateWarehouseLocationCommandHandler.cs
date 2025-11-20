using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Application.Inventory.Commands.CreateWarehouseLocation;

public class CreateWarehouseLocationCommandHandler : IRequestHandler<CreateWarehouseLocationCommand, CreateWarehouseLocationResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CreateWarehouseLocationCommandHandler> _logger;

    public CreateWarehouseLocationCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CreateWarehouseLocationCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CreateWarehouseLocationResponse> Handle(CreateWarehouseLocationCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Warehouse kontrolü
        var warehouse = await _dbContext.Set<Warehouse>()
            .FirstOrDefaultAsync(w => w.Id == request.WarehouseId && w.TenantId == tenantId, cancellationToken);

        if (warehouse == null)
        {
            throw new NotFoundException("Warehouse", request.WarehouseId);
        }

        // Location code oluştur
        var locationCode = BuildLocationCode(request.Zone, request.Aisle, request.Rack, request.Shelf, request.Level);

        // Aynı location code var mı kontrol et
        var existingLocation = await _dbContext.Set<WarehouseLocation>()
            .FirstOrDefaultAsync(l => 
                l.WarehouseId == request.WarehouseId &&
                l.LocationCode == locationCode &&
                l.TenantId == tenantId, cancellationToken);

        if (existingLocation != null)
        {
            throw new BadRequestException($"Bu lokasyon kodu zaten kullanılıyor: {locationCode}");
        }

        // Yeni lokasyon oluştur
        var location = new WarehouseLocation
        {
            TenantId = tenantId,
            WarehouseId = request.WarehouseId,
            Zone = request.Zone,
            Aisle = request.Aisle,
            Rack = request.Rack,
            Shelf = request.Shelf,
            Level = request.Level,
            LocationCode = locationCode,
            Name = request.Name,
            Description = request.Description,
            Width = request.Width,
            Height = request.Height,
            Depth = request.Depth,
            MaxWeight = request.MaxWeight,
            IsActive = true
        };

        _dbContext.Set<WarehouseLocation>().Add(location);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Warehouse location created: {LocationCode} - Warehouse: {WarehouseId}", 
            locationCode, request.WarehouseId);

        return new CreateWarehouseLocationResponse
        {
            LocationId = location.Id,
            LocationCode = locationCode,
            Message = "Lokasyon başarıyla oluşturuldu."
        };
    }

    private static string BuildLocationCode(string? zone, string? aisle, string? rack, string? shelf, string? level)
    {
        var parts = new List<string>();
        
        if (!string.IsNullOrWhiteSpace(zone))
            parts.Add(zone.Trim());
        if (!string.IsNullOrWhiteSpace(aisle))
            parts.Add(aisle.Trim());
        if (!string.IsNullOrWhiteSpace(rack))
            parts.Add(rack.Trim());
        if (!string.IsNullOrWhiteSpace(shelf))
            parts.Add(shelf.Trim());
        if (!string.IsNullOrWhiteSpace(level))
            parts.Add(level.Trim());

        return parts.Count > 0 ? string.Join("-", parts) : "UNKNOWN";
    }
}



