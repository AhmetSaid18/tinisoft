using Tinisoft.Application.Payments.Services;
using Microsoft.Extensions.Logging;

namespace Tinisoft.Infrastructure.Services;

public class PaymentServiceFactory : IPaymentServiceFactory
{
    private readonly Dictionary<string, IPaymentService> _services;
    private readonly ILogger<PaymentServiceFactory> _logger;

    public PaymentServiceFactory(
        PayTRPaymentService payTRService,
        KuveytTurkPaymentService kuveytTurkService,
        ILogger<PaymentServiceFactory> logger)
    {
        _logger = logger;
        _services = new Dictionary<string, IPaymentService>
        {
            { "PAYTR", payTRService },
            { "KUVEYTTURK", kuveytTurkService }
        };
    }

    public IPaymentService GetService(string providerCode)
    {
        var normalizedCode = providerCode.ToUpper();
        
        if (!_services.TryGetValue(normalizedCode, out var service))
        {
            throw new NotSupportedException($"Payment provider not supported: {providerCode}");
        }

        return service;
    }

    public bool IsProviderSupported(string providerCode)
    {
        var normalizedCode = providerCode.ToUpper();
        return _services.ContainsKey(normalizedCode);
    }
}

