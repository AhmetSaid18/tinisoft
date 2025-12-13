# Environment Variables Kurulum Rehberi

## 🚀 Hızlı Başlangıç

### 1. .env Dosyası Oluşturma

```bash
# Template dosyasını .env olarak kopyalayın
cp ENV_TEMPLATE.txt .env

# .env dosyasını düzenleyin
nano .env
# veya
code .env
```

### 2. Zorunlu Değişkenleri Doldurun

**Minimum gerekli değişkenler:**

```bash
# PostgreSQL şifresi (TÜM VERİTABANLARI İÇİN)
POSTGRES_PASSWORD=your-strong-password-here

# RabbitMQ kullanıcı adı ve şifresi
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=your-strong-rabbitmq-password

# JWT Secret Key (Minimum 32 karakter)
# Güçlü key oluşturmak için:
# Linux/Mac: openssl rand -base64 32
# Windows: [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes(32) | ForEach-Object { [System.Convert]::ToBase64String($_) }
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters-long

# Meilisearch Master Key
MEILISEARCH_MASTER_KEY=your-strong-meilisearch-master-key-here
```

### 3. Güçlü Şifre Oluşturma

**Linux/Mac:**
```bash
# PostgreSQL şifresi
openssl rand -base64 32

# JWT Secret Key
openssl rand -base64 32

# Meilisearch Master Key
openssl rand -base64 32
```

**Windows PowerShell:**
```powershell
# Rastgele şifre oluştur
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

### 4. Docker Compose ile Başlatma

```bash
# .env dosyası otomatik olarak yüklenecek
docker-compose up -d
```

## 📋 Tüm Environment Variables

### Veritabanı
- `POSTGRES_USER` - PostgreSQL kullanıcı adı (varsayılan: postgres)
- `POSTGRES_PASSWORD` - PostgreSQL şifresi (**ZORUNLU**)

### RabbitMQ
- `RABBITMQ_USER` - RabbitMQ kullanıcı adı (varsayılan: guest)
- `RABBITMQ_PASSWORD` - RabbitMQ şifresi (**ZORUNLU**)

### JWT Authentication
- `JWT_SECRET_KEY` - JWT token imzalama anahtarı (**ZORUNLU**, min 32 karakter)

### Meilisearch
- `MEILISEARCH_MASTER_KEY` - Meilisearch master key (**ZORUNLU**)

### Ödeme Gateway (Opsiyonel)
- `PAYTR_MERCHANT_ID` - PayTR merchant ID
- `PAYTR_MERCHANT_KEY` - PayTR merchant key
- `PAYTR_MERCHANT_SALT` - PayTR merchant salt

### Email Service (Opsiyonel)
- `SENDGRID_API_KEY` - SendGrid API key

### SMS Service (Opsiyonel)
- `NETGSM_USERNAME` - NetGSM kullanıcı adı
- `NETGSM_PASSWORD` - NetGSM şifresi

### Storage (Opsiyonel)
- `R2_ACCOUNT_ID` - Cloudflare R2 account ID
- `R2_ACCESS_KEY_ID` - Cloudflare R2 access key
- `R2_SECRET_ACCESS_KEY` - Cloudflare R2 secret key
- `R2_BUCKET_NAME` - Cloudflare R2 bucket adı

### Marketplace Entegrasyonları (Opsiyonel)
- `TRENDYOL_SUPPLIER_ID` - Trendyol supplier ID
- `TRENDYOL_API_KEY` - Trendyol API key
- `TRENDYOL_API_SECRET` - Trendyol API secret
- `HEPSIBURADA_MERCHANT_ID` - Hepsiburada merchant ID
- `HEPSIBURADA_USERNAME` - Hepsiburada kullanıcı adı
- `HEPSIBURADA_PASSWORD` - Hepsiburada şifresi
- `N11_API_KEY` - N11 API key
- `N11_SECRET_KEY` - N11 secret key

## ⚠️ Güvenlik Uyarıları

1. **ASLA `.env` dosyasını Git'e commit etmeyin!**
   - `.gitignore` dosyasında zaten var
   - Production'da farklı şifreler kullanın

2. **Güçlü Şifreler Kullanın:**
   - Minimum 32 karakter
   - Büyük/küçük harf, sayı ve özel karakterler
   - Rastgele oluşturulmuş

3. **Production Ortamı:**
   - Development ve Production için farklı şifreler
   - Environment variables'ı güvenli bir şekilde saklayın
   - Docker secrets veya AWS Secrets Manager kullanın

## 🔍 Kontrol

Environment variables'ın yüklendiğini kontrol etmek için:

```bash
# Docker container içinde kontrol
docker-compose exec api env | grep POSTGRES_PASSWORD
docker-compose exec api env | grep JWT_SECRET_KEY
```

## 📝 Notlar

- `.env` dosyası yoksa, docker-compose.yml varsayılan değerleri kullanır (güvensiz!)
- Production'da mutlaka `.env` dosyası oluşturun ve güçlü şifreler kullanın
- Tüm hassas bilgiler `.env` dosyasında tutulmalı

