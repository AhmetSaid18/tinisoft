using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Tinisoft.Application.Common.Interfaces;

namespace Tinisoft.Infrastructure.Services;

public class TraefikDomainService : ITraefikDomainService
{
    private readonly ILogger<TraefikDomainService> _logger;
    private readonly string _dynamicConfigPath;

    public TraefikDomainService(
        ILogger<TraefikDomainService> logger,
        IConfiguration configuration)
    {
        _logger = logger;
        _dynamicConfigPath = configuration["Traefik:DynamicConfigPath"] ?? "/etc/traefik/dynamic";
        
        // Docker dışında çalışıyorsa local path kullan
        if (!Directory.Exists(_dynamicConfigPath))
        {
            _dynamicConfigPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "traefik", "dynamic");
            
            // Hala yoksa proje root'a göre ayarla
            if (!Directory.Exists(_dynamicConfigPath))
            {
                _dynamicConfigPath = "traefik/dynamic";
            }
        }
        
        // Klasör yoksa oluştur
        if (!Directory.Exists(_dynamicConfigPath))
        {
            Directory.CreateDirectory(_dynamicConfigPath);
        }
    }

    public async Task AddDomainAsync(string host, CancellationToken cancellationToken = default)
    {
        try
        {
            var safeName = host.Replace(".", "-").Replace(":", "-");
            var configFileName = $"custom-domain-{safeName}.yaml";
            var configPath = Path.Combine(_dynamicConfigPath, configFileName);

            // Traefik YAML config oluştur
            var traefikConfig = $@"# Auto-generated config for {host}
# Created: {DateTime.UtcNow:yyyy-MM-dd HH:mm:ss} UTC

http:
  routers:
    custom-domain-{safeName}:
      rule: ""Host(`{host}`)""
      entryPoints:
        - web
      service: api-gateway
      priority: 100
      middlewares:
        - secure-headers

  # Not: Service tanımı base-routing.yaml'da
";

            await File.WriteAllTextAsync(configPath, traefikConfig, cancellationToken);

            _logger.LogInformation("Traefik config created for domain {Host} at {Path}", host, configPath);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating Traefik config for domain {Host}", host);
            throw;
        }
    }

    public async Task RemoveDomainAsync(string host, CancellationToken cancellationToken = default)
    {
        try
        {
            var safeName = host.Replace(".", "-").Replace(":", "-");
            var configFileName = $"custom-domain-{safeName}.yaml";
            var configPath = Path.Combine(_dynamicConfigPath, configFileName);

            if (File.Exists(configPath))
            {
                File.Delete(configPath);
                _logger.LogInformation("Traefik config removed for domain {Host}", host);
            }
            else
            {
                _logger.LogWarning("Traefik config not found for domain {Host}", host);
            }

            await Task.CompletedTask;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error removing Traefik config for domain {Host}", host);
            throw;
        }
    }

    public bool DomainConfigExists(string host)
    {
        var safeName = host.Replace(".", "-").Replace(":", "-");
        var configFileName = $"custom-domain-{safeName}.yaml";
        var configPath = Path.Combine(_dynamicConfigPath, configFileName);
        return File.Exists(configPath);
    }
}

