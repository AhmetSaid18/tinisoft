using MediatR;

namespace Tinisoft.Application.Payments.Commands.ProcessPayment;

public class ProcessPaymentCommand : IRequest<ProcessPaymentResponse>
{
    public Guid OrderId { get; set; }
    public string PaymentProvider { get; set; } = "PayTR"; // PayTR, Stripe, Iyzico, etc.
    public decimal Amount { get; set; }
    public string Currency { get; set; } = "TRY";
    public Dictionary<string, string>? ProviderSpecificData { get; set; }
}

public class ProcessPaymentResponse
{
    public bool Success { get; set; }
    public string? PaymentToken { get; set; } // iFrame için token
    public string? PaymentReference { get; set; } // Transaction ID
    public string? ErrorMessage { get; set; }
    public string? RedirectUrl { get; set; }
}



