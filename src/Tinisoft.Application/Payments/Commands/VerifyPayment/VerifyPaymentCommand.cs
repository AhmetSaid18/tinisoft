using MediatR;

namespace Tinisoft.Application.Payments.Commands.VerifyPayment;

public class VerifyPaymentCommand : IRequest<VerifyPaymentResponse>
{
    public Guid OrderId { get; set; }
    public string PaymentReference { get; set; } = string.Empty;
    public string Hash { get; set; } = string.Empty;
    public Dictionary<string, string> CallbackData { get; set; } = new();
}

public class VerifyPaymentResponse
{
    public bool IsValid { get; set; }
    public bool IsPaid { get; set; }
    public string? ErrorMessage { get; set; }
}



