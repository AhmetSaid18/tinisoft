# Cloudflare R2 Storage Setup

Ürün görsellerini Cloudflare R2'de saklama rehberi.

## Neden Cloudflare R2?

✅ **S3 Uyumlu API** - Kolay entegrasyon  
✅ **CDN Desteği** - Cloudflare CDN ile hızlı görsel servisi  
✅ **Düşük Maliyet** - Egress ücreti yok  
✅ **Ölçeklenebilir** - Sınırsız depolama  
✅ **Hızlı** - Global CDN ağı  

## 1. Cloudflare R2 Bucket Oluşturma

1. Cloudflare Dashboard'a git: https://dash.cloudflare.com
2. **R2** sekmesine git
3. **Create bucket** butonuna tıkla
4. Bucket adı ver (örn: `tinisoft-products`)
5. **Create bucket** ile oluştur

## 2. R2 API Token Oluşturma

1. Cloudflare Dashboard → **R2** → **Manage R2 API Tokens**
2. **Create API token** butonuna tıkla
3. Token adı ver (örn: `tinisoft-r2-token`)
4. **Permissions**: 
   - **Object Read & Write** seç
5. **Bucket Access**: 
   - Oluşturduğun bucket'ı seç
6. **Create API Token** ile oluştur
7. **Access Key ID** ve **Secret Access Key**'i kopyala (bir daha gösterilmez!)

## 3. R2 Custom Domain (Opsiyonel - Önerilir)

CDN için custom domain kullan:

1. Cloudflare Dashboard → **R2** → Bucket'ını seç
2. **Settings** → **Public Access** → **Connect Domain**
3. Custom domain ekle (örn: `cdn.tinisoft.com.tr`)
4. DNS kaydını ekle (Cloudflare otomatik oluşturur)

**Not:** Custom domain kullanmazsan, R2 endpoint URL'i kullanılır (daha yavaş olabilir).

## 4. Environment Variables

`.env` dosyasına ekle:

```env
# Cloudflare R2 Settings
USE_R2=True
R2_ACCESS_KEY_ID=your-access-key-id
R2_SECRET_ACCESS_KEY=your-secret-access-key
R2_BUCKET_NAME=tinisoft-products
R2_ENDPOINT_URL=https://xxx.r2.cloudflarestorage.com
R2_REGION=auto
R2_CUSTOM_DOMAIN=cdn.tinisoft.com.tr  # Opsiyonel, CDN için
R2_ACCOUNT_ID=your-account-id  # Opsiyonel, Cloudflare Account ID
```

**R2 Endpoint URL'i bulma:**
1. Cloudflare Dashboard → **R2** → Bucket'ını seç
2. **Settings** → **S3 API** bölümünde endpoint URL'i görürsün

## 5. Django Settings

Settings zaten yapılandırıldı. Sadece environment variables'ı ayarla.

## 6. Test

```python
# Python shell'de test et
python manage.py shell

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Test dosyası yükle
file = ContentFile(b"Hello World", name="test.txt")
default_storage.save("test/test.txt", file)

# Dosyayı oku
url = default_storage.url("test/test.txt")
print(url)  # R2 URL'i görmeli
```

## 7. Ürün Görselleri

Ürün görselleri otomatik olarak R2'ye yüklenir:

```python
# ProductImage model'inde
product_image = ProductImage.objects.create(
    product=product,
    image_url="https://cdn.tinisoft.com.tr/media/products/image.jpg"
)
```

## 8. Frontend'de Kullanım

Görseller R2'den CDN üzerinden servis edilir:

```html
<!-- Product image -->
<img src="{{ product.primary_image.image_url }}" alt="{{ product.name }}" />

<!-- R2 URL formatı -->
<!-- Custom domain varsa: https://cdn.tinisoft.com.tr/media/products/image.jpg -->
<!-- Custom domain yoksa: https://xxx.r2.cloudflarestorage.com/media/products/image.jpg -->
```

## 9. Maliyet

Cloudflare R2 fiyatlandırması (2024):
- **Depolama**: $0.015 / GB / ay
- **Class A Operations** (Write): $4.50 / 1M requests
- **Class B Operations** (Read): $0.36 / 1M requests
- **Egress**: **ÜCRETSİZ** (Cloudflare CDN üzerinden)

**Örnek:**
- 100 GB görsel
- 1M yazma işlemi
- 10M okuma işlemi
- **Aylık maliyet**: ~$5-10

## 10. Alternatif: AWS S3

Eğer AWS S3 kullanmak istersen:

```env
USE_R2=False
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=eu-central-1
AWS_S3_CUSTOM_DOMAIN=cdn.tinisoft.com.tr  # CloudFront domain
```

Settings'te `USE_R2=False` yap ve AWS credentials ekle.

## Troubleshooting

### Görseller yüklenmiyor
- R2 credentials kontrol et
- Bucket permissions kontrol et
- `USE_R2=True` olduğundan emin ol

### Görseller yavaş yükleniyor
- Custom domain kullan (CDN için)
- Cloudflare CDN cache ayarlarını kontrol et

### CORS hatası
- R2 bucket settings → CORS ayarlarını kontrol et
- Frontend domain'ini allow list'e ekle

## Kaynaklar

- [Cloudflare R2 Docs](https://developers.cloudflare.com/r2/)
- [django-storages Docs](https://django-storages.readthedocs.io/)

