using MediatR;

namespace Tinisoft.Application.Tenant.Commands.UpdateLayoutSettings;

public class UpdateLayoutSettingsCommand : IRequest<UpdateLayoutSettingsResponse>
{
    // Layout Ayarları (JSON - esnek yapı için)
    // Örnek: 
    // {
    //   "headerStyle": "sticky",
    //   "footerStyle": "fixed",
    //   "productGridColumns": 4,
    //   "showBreadcrumbs": true,
    //   "showRelatedProducts": true,
    //   "sidebarPosition": "left",
    //   "layoutType": "grid"
    // }
    public Dictionary<string, object> LayoutSettings { get; set; } = new();
}

public class UpdateLayoutSettingsResponse
{
    public Guid TenantId { get; set; }
    public Dictionary<string, object> LayoutSettings { get; set; } = new();
    public string Message { get; set; } = "Layout ayarları başarıyla güncellendi.";
}



