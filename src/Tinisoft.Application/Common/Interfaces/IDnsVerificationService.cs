namespace Tinisoft.Application.Common.Interfaces;

/// <summary>
/// DNS record verification servisi
/// TXT ve CNAME record'larını kontrol eder
/// </summary>
public interface IDnsVerificationService
{
    Task<bool> VerifyTxtRecordAsync(string domain, string expectedToken, CancellationToken cancellationToken = default);
    Task<bool> VerifyCnameRecordAsync(string domain, string expectedTarget, CancellationToken cancellationToken = default);
    Task<DnsVerificationResult> FullVerificationAsync(string domain, string txtToken, string cnameTarget, CancellationToken cancellationToken = default);
}

public class DnsVerificationResult
{
    public string Domain { get; set; } = string.Empty;
    public bool TxtVerified { get; set; }
    public bool CnameVerified { get; set; }
    public bool FullyVerified { get; set; }
    public List<string> Errors { get; set; } = new();
}

