using SixLabors.ImageSharp;
using SixLabors.ImageSharp.Processing;
using SixLabors.ImageSharp.PixelFormats;
using Tinisoft.Infrastructure.Services;
using Tinisoft.Application.Common.Interfaces;
using Microsoft.Extensions.Logging;

namespace Tinisoft.Infrastructure.Services;

public class ImageProcessingService : IImageProcessingService
{
    private readonly IStorageService _storageService;
    private readonly ILogger<ImageProcessingService> _logger;

    public ImageProcessingService(
        IStorageService storageService,
        ILogger<ImageProcessingService> logger)
    {
        _storageService = storageService;
        _logger = logger;
    }

    public async Task<ProcessedImageResult> ProcessImageAsync(
        Stream imageStream, 
        string fileName, 
        CancellationToken cancellationToken = default)
    {
        using var image = await Image.LoadAsync(imageStream, cancellationToken);
        
        var originalWidth = image.Width;
        var originalHeight = image.Height;
        var originalSize = imageStream.Length;

        // Original image upload
        imageStream.Position = 0;
        var originalUrl = await _storageService.UploadFileAsync(
            imageStream, 
            $"products/original/{fileName}", 
            "image/jpeg", 
            cancellationToken);

        var result = new ProcessedImageResult
        {
            OriginalUrl = originalUrl,
            OriginalSizeBytes = originalSize,
            OriginalWidth = originalWidth,
            OriginalHeight = originalHeight
        };

        // Generate sizes
        result.ThumbnailUrl = await GenerateSizeAsync(image, fileName, 150, 150, "thumbnail", cancellationToken);
        result.SmallUrl = await GenerateSizeAsync(image, fileName, 300, 300, "small", cancellationToken);
        result.MediumUrl = await GenerateSizeAsync(image, fileName, 600, 600, "medium", cancellationToken);
        result.LargeUrl = await GenerateSizeAsync(image, fileName, 1200, 1200, "large", cancellationToken);

        return result;
    }

    public async Task<ProcessedImageResult> ProcessImageFromUrlAsync(
        string imageUrl, 
        string fileName, 
        CancellationToken cancellationToken = default)
    {
        using var httpClient = new HttpClient();
        var response = await httpClient.GetAsync(imageUrl, cancellationToken);
        response.EnsureSuccessStatusCode();
        
        using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        return await ProcessImageAsync(stream, fileName, cancellationToken);
    }

    private async Task<string?> GenerateSizeAsync(
        Image image, 
        string fileName, 
        int maxWidth, 
        int maxHeight, 
        string sizeName, 
        CancellationToken cancellationToken)
    {
        try
        {
            // Resize maintaining aspect ratio - CloneAs kullan (ImageSharp 3.x)
            using var clone = image.CloneAs<Rgba32>();
            
            clone.Mutate(x => x.Resize(new ResizeOptions
            {
                Size = new Size(maxWidth, maxHeight),
                Mode = ResizeMode.Max
            }));

            using var outputStream = new MemoryStream();
            await clone.SaveAsJpegAsync(outputStream, cancellationToken);
            outputStream.Position = 0;

            var url = await _storageService.UploadFileAsync(
                outputStream, 
                $"products/{sizeName}/{fileName}", 
                "image/jpeg", 
                cancellationToken);

            return url;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating {SizeName} image for {FileName}", sizeName, fileName);
            return null;
        }
    }
}

