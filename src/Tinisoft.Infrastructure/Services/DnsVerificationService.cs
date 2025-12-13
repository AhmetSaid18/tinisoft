using System.Net;
using DnsClient;
using Microsoft.Extensions.Logging;
using Tinisoft.Application.Common.Interfaces;

namespace Tinisoft.Infrastructure.Services;

public class DnsVerificationService : IDnsVerificationService
{
    private readonly ILogger<DnsVerificationService> _logger;
    private readonly ILookupClient _dnsClient;

    public DnsVerificationService(ILogger<DnsVerificationService> logger)
    {
        _logger = logger;
        // Google DNS ve Cloudflare DNS kullan
        _dnsClient = new LookupClient(
            new IPEndPoint(IPAddress.Parse("8.8.8.8"), 53),
            new IPEndPoint(IPAddress.Parse("1.1.1.1"), 53)
        );
    }

    public async Task<bool> VerifyTxtRecordAsync(string domain, string expectedToken, CancellationToken cancellationToken = default)
    {
        try
        {
            // _tinisoft-verification.ornekmagaza.com için TXT record sorgula
            var verificationDomain = $"_tinisoft-verification.{domain}";
            
            _logger.LogInformation("Checking TXT record for {Domain}", verificationDomain);

            var result = await _dnsClient.QueryAsync(verificationDomain, QueryType.TXT, cancellationToken: cancellationToken);

            if (result.HasError)
            {
                _logger.LogWarning("DNS query failed for {Domain}: {Error}", verificationDomain, result.ErrorMessage);
                return false;
            }

            var txtRecords = result.Answers.TxtRecords();
            
            foreach (var record in txtRecords)
            {
                var txtValue = string.Join("", record.Text);
                _logger.LogDebug("Found TXT record: {Value}", txtValue);
                
                if (txtValue.Contains(expectedToken))
                {
                    _logger.LogInformation("TXT verification successful for {Domain}", domain);
                    return true;
                }
            }

            _logger.LogWarning("TXT record not found or doesn't match for {Domain}", domain);
            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error verifying TXT record for {Domain}", domain);
            return false;
        }
    }

    public async Task<bool> VerifyCnameRecordAsync(string domain, string expectedTarget, CancellationToken cancellationToken = default)
    {
        try
        {
            _logger.LogInformation("Checking CNAME record for {Domain}", domain);

            var result = await _dnsClient.QueryAsync(domain, QueryType.CNAME, cancellationToken: cancellationToken);

            if (result.HasError)
            {
                // CNAME olmayabilir, A record da kabul edilebilir
                _logger.LogDebug("No CNAME record for {Domain}, checking if domain resolves", domain);
                
                // Domain'in çözülüp çözülmediğini kontrol et
                var aResult = await _dnsClient.QueryAsync(domain, QueryType.A, cancellationToken: cancellationToken);
                return !aResult.HasError && aResult.Answers.ARecords().Any();
            }

            var cnameRecords = result.Answers.CnameRecords();
            
            foreach (var record in cnameRecords)
            {
                var canonicalName = record.CanonicalName.Value.TrimEnd('.');
                _logger.LogDebug("Found CNAME record: {Value}", canonicalName);
                
                if (canonicalName.Equals(expectedTarget.TrimEnd('.'), StringComparison.OrdinalIgnoreCase))
                {
                    _logger.LogInformation("CNAME verification successful for {Domain}", domain);
                    return true;
                }
            }

            _logger.LogWarning("CNAME record not found or doesn't match for {Domain}", domain);
            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error verifying CNAME record for {Domain}", domain);
            return false;
        }
    }

    public async Task<Application.Common.Interfaces.DnsVerificationResult> FullVerificationAsync(string domain, string txtToken, string cnameTarget, CancellationToken cancellationToken = default)
    {
        var result = new Application.Common.Interfaces.DnsVerificationResult
        {
            Domain = domain
        };

        // TXT verification
        result.TxtVerified = await VerifyTxtRecordAsync(domain, txtToken, cancellationToken);

        // CNAME verification
        result.CnameVerified = await VerifyCnameRecordAsync(domain, cnameTarget, cancellationToken);

        result.FullyVerified = result.TxtVerified && result.CnameVerified;

        if (!result.TxtVerified)
        {
            result.Errors.Add("TXT record not found or doesn't match. Please add: _tinisoft-verification TXT " + txtToken);
        }

        if (!result.CnameVerified)
        {
            result.Errors.Add($"CNAME record not found. Please add: CNAME → {cnameTarget}");
        }

        return result;
    }
}

