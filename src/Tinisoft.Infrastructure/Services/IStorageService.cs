namespace Tinisoft.Infrastructure.Services;

public interface IStorageService
{
    Task<string> UploadFileAsync(Stream fileStream, string fileName, string contentType, CancellationToken cancellationToken = default);
    Task<string> GetPresignedUploadUrlAsync(string fileName, string contentType, CancellationToken cancellationToken = default);
    Task<bool> DeleteFileAsync(string fileUrl, CancellationToken cancellationToken = default);
}

