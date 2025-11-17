using Amazon.S3;
using Amazon.S3.Model;
using Microsoft.Extensions.Configuration;

namespace Tinisoft.Infrastructure.Services;

public class R2StorageService : IStorageService
{
    private readonly IAmazonS3 _s3Client;
    private readonly string _bucketName;
    private readonly IConfiguration _configuration;

    public R2StorageService(IConfiguration configuration)
    {
        _configuration = configuration;
        var r2Config = configuration.GetSection("Storage:R2");
        
        _bucketName = r2Config["BucketName"] ?? throw new InvalidOperationException("R2 BucketName not configured");

        var config = new AmazonS3Config
        {
            ServiceURL = $"https://{r2Config["AccountId"]}.r2.cloudflarestorage.com",
            ForcePathStyle = true
        };

        _s3Client = new AmazonS3Client(
            r2Config["AccessKeyId"],
            r2Config["SecretAccessKey"],
            config
        );
    }

    public async Task<string> UploadFileAsync(Stream fileStream, string fileName, string contentType, CancellationToken cancellationToken = default)
    {
        var request = new PutObjectRequest
        {
            BucketName = _bucketName,
            Key = fileName,
            InputStream = fileStream,
            ContentType = contentType
        };

        await _s3Client.PutObjectAsync(request, cancellationToken);
        return $"https://{_bucketName}/{fileName}";
    }

    public async Task<string> GetPresignedUploadUrlAsync(string fileName, string contentType, CancellationToken cancellationToken = default)
    {
        var request = new GetPreSignedUrlRequest
        {
            BucketName = _bucketName,
            Key = fileName,
            Verb = HttpVerb.PUT,
            ContentType = contentType,
            Expires = DateTime.UtcNow.AddMinutes(15)
        };

        return await _s3Client.GetPreSignedURLAsync(request);
    }

    public async Task<bool> DeleteFileAsync(string fileUrl, CancellationToken cancellationToken = default)
    {
        var key = fileUrl.Split('/').Last();
        var request = new DeleteObjectRequest
        {
            BucketName = _bucketName,
            Key = key
        };

        await _s3Client.DeleteObjectAsync(request, cancellationToken);
        return true;
    }
}

