using MediatR;

namespace Tinisoft.Application.Notifications.Commands.SendEmail;

public class SendEmailCommand : IRequest<SendEmailResponse>
{
    public string ToEmail { get; set; } = string.Empty;
    public string? ToName { get; set; }
    public string? CcEmail { get; set; }
    public string? BccEmail { get; set; }
    public string Subject { get; set; } = string.Empty;
    public string BodyHtml { get; set; } = string.Empty;
    public string? BodyText { get; set; }
    public Guid? EmailTemplateId { get; set; } // Template kullanılacaksa
    public Guid? ReferenceId { get; set; } // OrderId, ProductId, vb.
    public string? ReferenceType { get; set; } // "Order", "Product", vb.
}

public class SendEmailResponse
{
    public Guid EmailNotificationId { get; set; }
    public bool Success { get; set; }
    public string? ErrorMessage { get; set; }
}



