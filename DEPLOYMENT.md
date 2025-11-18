# Tinisoft Deployment Guide

## Port Yapılandırması

Sunucudaki mevcut portlarla çakışmayı önlemek için portlar değiştirilmiştir:

### API Portları
- **Gateway**: 5000
- **Products API**: 5001
- **Inventory API**: 5002
- **Payments API**: 5003
- **Orders API**: 5004
- **Marketplace API**: 5005
- **Customers API**: 5006
- **Shipping API**: 5007
- **Notifications API**: 5008

### Database Portları (Host)
- **Products DB**: 6000
- **Inventory DB**: 6001
- **Payments DB**: 6002
- **Orders DB**: 6003
- **Marketplace DB**: 6004
- **Customers DB**: 6005
- **Shipping DB**: 6006
- **Notifications DB**: 6007

### Infrastructure Portları
- **Redis**: 6380
- **RabbitMQ**: 5672
- **RabbitMQ Management**: 15672
- **Kafka**: 9092
- **Zookeeper**: 2181

## Kurulum

### 1. Environment Variables Ayarlama

`.env.example` dosyasını `.env` olarak kopyalayın:

```bash
cp .env.example .env
```

`.env` dosyasını düzenleyin ve tüm değerleri doldurun:

```bash
# Önemli: Bu dosya asla Git'e commit edilmemeli!
# .gitignore'da zaten var
```

### 2. Docker Compose ile Başlatma

```bash
docker-compose up -d
```

### 3. Health Check

Tüm servislerin çalıştığını kontrol edin:

```bash
docker-compose ps
```

### 4. Logları İzleme

```bash
# Tüm servisler
docker-compose logs -f

# Belirli bir servis
docker-compose logs -f gateway
docker-compose logs -f products-api
```

## Environment Variables Açıklamaları

### Zorunlu Değişkenler

1. **POSTGRES_PASSWORD**: Tüm database'ler için şifre
2. **JWT_SECRET_KEY**: JWT token imzalama için (min 32 karakter)
3. **RABBITMQ_PASSWORD**: RabbitMQ şifresi

### Email (SMTP) Ayarları

Email bildirimleri için SMTP ayarları:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_ENABLE_SSL=true
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=noreply@tinisoft.com
SMTP_FROM_NAME=Tinisoft
```

**Not**: Gmail kullanıyorsanız, "App Password" oluşturmanız gerekir.

### Kargo Firması API Key'leri

Kargo entegrasyonları için API key'ler:

```env
# Aras Kargo
ARAS_API_KEY=your_aras_api_key
ARAS_API_SECRET=your_aras_api_secret

# MNG Kargo
MNG_API_KEY=your_mng_api_key
MNG_API_SECRET=your_mng_api_secret

# Yurtiçi Kargo
YURTICI_API_KEY=your_yurtici_api_key
YURTICI_API_SECRET=your_yurtici_api_secret
```

### Ödeme Gateway (PayTR)

```env
PAYTR_MERCHANT_ID=your_merchant_id
PAYTR_MERCHANT_KEY=your_merchant_key
PAYTR_MERCHANT_SALT=your_merchant_salt
```

## Port Çakışması Durumunda

Eğer herhangi bir port çakışması varsa, `.env` dosyasında ilgili port değişkenini değiştirin:

```env
# Örnek: Products API portunu 5011 yapmak istiyorsanız
PRODUCTS_API_PORT=5011

# Örnek: Products DB portunu 6011 yapmak istiyorsanız
PRODUCTS_DB_PORT=6011
```

## Production Checklist

- [ ] `.env` dosyası oluşturuldu ve dolduruldu
- [ ] Tüm API key'ler ve şifreler güvenli
- [ ] JWT_SECRET_KEY en az 32 karakter
- [ ] Database şifreleri güçlü
- [ ] SMTP ayarları test edildi
- [ ] Port çakışmaları kontrol edildi
- [ ] `.env` dosyası `.gitignore`'da
- [ ] Docker volumes yedekleme stratejisi hazır

## Troubleshooting

### Port Already in Use

```bash
# Hangi process portu kullanıyor?
sudo lsof -i :5000

# Process'i durdur
sudo kill -9 <PID>
```

### Database Connection Error

```bash
# Database container'ının loglarını kontrol et
docker-compose logs products-db

# Database'e bağlanmayı test et
docker-compose exec products-db psql -U postgres -d products_db
```

### RabbitMQ Connection Error

```bash
# RabbitMQ loglarını kontrol et
docker-compose logs rabbitmq

# RabbitMQ Management UI'ya eriş
# http://localhost:15672
# Username: guest (veya .env'deki RABBITMQ_USERNAME)
# Password: .env'deki RABBITMQ_PASSWORD
```

## Backup

### Database Backup

```bash
# Products DB backup
docker-compose exec products-db pg_dump -U postgres products_db > backup_products_$(date +%Y%m%d).sql

# Tüm database'leri backup
for db in products inventory payments orders marketplace customers shipping notifications; do
  docker-compose exec ${db}-db pg_dump -U postgres ${db}_db > backup_${db}_$(date +%Y%m%d).sql
done
```

### Restore

```bash
# Products DB restore
docker-compose exec -T products-db psql -U postgres products_db < backup_products_20240101.sql
```

