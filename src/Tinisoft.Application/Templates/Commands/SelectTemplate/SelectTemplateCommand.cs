using MediatR;

namespace Tinisoft.Application.Templates.Commands.SelectTemplate;

public class SelectTemplateCommand : IRequest<SelectTemplateResponse>
{
    public string TemplateCode { get; set; } = string.Empty; // "minimal", "fashion", etc.
    public int? TemplateVersion { get; set; } // Opsiyonel, null ise en son versiyon kullanılır
}

public class SelectTemplateResponse
{
    public Guid TenantId { get; set; }
    public string TemplateCode { get; set; } = string.Empty;
    public int TemplateVersion { get; set; }
    public string Message { get; set; } = "Template başarıyla seçildi. Site hazırlanıyor...";
    public bool SetupStarted { get; set; } // Background job'lar başlatıldı mı?
}

