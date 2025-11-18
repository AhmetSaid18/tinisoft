using System.Xml.Linq;
using Microsoft.Extensions.Logging;
using Tinisoft.Application.ExchangeRates.Services;

namespace Tinisoft.Infrastructure.Services;

/// <summary>
/// TCMB XML feed'inden döviz kurlarını çeken servis
/// </summary>
public class TcmbExchangeService : ITcmbExchangeService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<TcmbExchangeService> _logger;
    private const string TCMB_XML_URL = "https://www.tcmb.gov.tr/kurlar/today.xml";

    // TCMB XML'deki currency code mapping
    private static readonly Dictionary<string, string> CurrencyCodeMap = new()
    {
        { "USD", "USD" },
        { "EUR", "EUR" },
        { "GBP", "GBP" },
        { "JPY", "JPY" },
        { "CHF", "CHF" },
        { "AUD", "AUD" },
        { "CAD", "CAD" },
        { "RUB", "RUB" },
        { "CNY", "CNY" },
        { "SAR", "SAR" },
        { "AED", "AED" }
    };

    public TcmbExchangeService(HttpClient httpClient, ILogger<TcmbExchangeService> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
    }

    public async Task<Dictionary<string, decimal>> GetLatestRatesAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            _logger.LogInformation("Fetching exchange rates from TCMB: {Url}", TCMB_XML_URL);

            var response = await _httpClient.GetStringAsync(TCMB_XML_URL, cancellationToken);
            var xmlDoc = XDocument.Parse(response);

            var rates = new Dictionary<string, decimal>();

            // TCMB XML yapısı: <Currency CurrencyCode="USD"> ... <BanknoteSelling>...</BanknoteSelling> ...
            var currencies = xmlDoc.Descendants("Currency");

            foreach (var currency in currencies)
            {
                var currencyCode = currency.Attribute("CurrencyCode")?.Value;
                if (string.IsNullOrEmpty(currencyCode) || !CurrencyCodeMap.ContainsKey(currencyCode))
                    continue;

                // BanknoteSelling = Efektif satış kuru (bunu kullanıyoruz)
                var banknoteSelling = currency.Element("BanknoteSelling")?.Value;
                if (string.IsNullOrEmpty(banknoteSelling))
                    continue;

                if (decimal.TryParse(banknoteSelling, out var rate))
                {
                    // TCMB kurları 1 USD = X TRY formatında, bizim ihtiyacımız olan bu
                    rates[currencyCode] = rate;
                    _logger.LogDebug("Fetched rate: {Currency} = {Rate} TRY", currencyCode, rate);
                }
            }

            _logger.LogInformation("Successfully fetched {Count} exchange rates from TCMB", rates.Count);
            return rates;
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "Error fetching exchange rates from TCMB");
            throw;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unexpected error parsing TCMB XML");
            throw;
        }
    }

    public async Task<decimal?> GetRateAsync(string targetCurrency, CancellationToken cancellationToken = default)
    {
        var rates = await GetLatestRatesAsync(cancellationToken);
        return rates.TryGetValue(targetCurrency.ToUpper(), out var rate) ? rate : null;
    }
}

