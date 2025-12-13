namespace Tinisoft.Application.Common.Interfaces;

/// <summary>
/// Traefik dynamic config yönetimi
/// Yeni domain eklendiğinde/silindiğinde config dosyası oluşturur/siler
/// </summary>
public interface ITraefikDomainService
{
    Task AddDomainAsync(string host, CancellationToken cancellationToken = default);
    Task RemoveDomainAsync(string host, CancellationToken cancellationToken = default);
    bool DomainConfigExists(string host);
}

