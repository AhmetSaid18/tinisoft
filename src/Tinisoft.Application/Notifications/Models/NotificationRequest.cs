using Tinisoft.Domain.Enums;

namespace Tinisoft.Application.Notifications.Models;

public class NotificationRequest
{
    public required NotificationType Type { get; set; }
    public required NotificationChannel Channel { get; set; }
    
    // Recipient
    public required string Recipient { get; set; } // Email or phone
    public string? RecipientName { get; set; }
    public Guid? CustomerId { get; set; }
    
    // Content (if not using template)
    public string? Subject { get; set; }
    public string? Body { get; set; }
    
    // Template variables
    public Dictionary<string, string>? Variables { get; set; }
    
    // Reference
    public Guid? OrderId { get; set; }
    public Guid? ProductId { get; set; }
    
    // Options
    public bool SendImmediately { get; set; } = true;
    public DateTime? ScheduledFor { get; set; }
}

public class EmailRequest
{
    public required string To { get; set; }
    public string? ToName { get; set; }
    public required string Subject { get; set; }
    public required string HtmlBody { get; set; }
    public string? TextBody { get; set; }
    public List<EmailAttachment>? Attachments { get; set; }
}

public class EmailAttachment
{
    public required string FileName { get; set; }
    public required byte[] Content { get; set; }
    public required string ContentType { get; set; }
}

public class SmsRequest
{
    public required string PhoneNumber { get; set; }
    public required string Message { get; set; }
}

public class NotificationResult
{
    public bool Success { get; set; }
    public string? MessageId { get; set; }
    public string? ErrorMessage { get; set; }
    public DateTime SentAt { get; set; }
}

