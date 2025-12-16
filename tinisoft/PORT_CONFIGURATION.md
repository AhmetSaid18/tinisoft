# Port Configuration - Sunucu Port Kullanımı

## Mevcut Portlar (Sunucuda Kullanılan)

| Port | Servis | Durum |
|------|--------|-------|
| 3000 | roboticsan-web | Kullanılıyor |
| 3001 | nowmedya_frontend | Kullanılıyor |
| 3020 | kervansaray-v2 | Kullanılıyor |
| 4000 | roboticsan-web | Kullanılıyor |
| 4003 | cankiri_wedding_photographer | Kullanılıyor |
| 4012 | roboticsan-web-eu | Kullanılıyor |
| 4021 | darnidekor-react | Kullanılıyor |
| 5000 | **BOŞ** ✅ | Tinisoft Backend için |
| 5432 | menu_api_db (PostgreSQL) | Kullanılıyor |
| 5433 | **BOŞ** ✅ | Tinisoft PostgreSQL için |
| 5555 | now_api-now_postgre-1 (PostgreSQL) | Kullanılıyor |
| 5599 | exam-grading-api | Kullanılıyor |
| 5672 | **BOŞ** ✅ | RabbitMQ için (isteğe bağlı) |
| 6380 | **BOŞ** ✅ | Tinisoft Redis için |
| 8000 | **KULLANILMIYOR** | Ama 8008, 8010 kullanılıyor |
| 8008 | now_api-now_api | Kullanılıyor |
| 8010 | menu_api_app | Kullanılıyor |
| 9000 | sonarqube | Kullanılıyor |
| 27016 | exam-grading-mongodb | Kullanılıyor |

## Tinisoft Port Yapılandırması

### Production (Sunucu)
- **Backend API**: `127.0.0.1:5000` → Nginx üzerinden `api.tinisoft.com.tr`
- **PostgreSQL**: `127.0.0.1:5433` (Container içinde 5432)
- **Redis**: `127.0.0.1:6380` (Container içinde 6379)

### Docker Compose Port Mapping
```yaml
postgres:
  ports:
    - "127.0.0.1:5433:5432"  # Host:5433 → Container:5432

redis:
  ports:
    - "127.0.0.1:6380:6379"  # Host:6380 → Container:6379

backend:
  ports:
    - "127.0.0.1:5000:8000"  # Host:5000 → Container:8000
```

### Nginx Configuration
```nginx
proxy_pass http://127.0.0.1:5000;  # Backend port 5000'de
```

## Port Çakışması Kontrolü

```bash
# Port kullanımını kontrol et
netstat -tuln | grep -E ':(5000|5433|6380)'

# Veya
ss -tuln | grep -E ':(5000|5433|6380)'
```

## Environment Variables

`.env` dosyasında:
```env
DB_HOST=postgres
DB_PORT=5432  # Container içinde (host'ta 5433)
REDIS_HOST=redis
REDIS_PORT=6379  # Container içinde (host'ta 6380)
```

## Notlar

- ✅ Port 5000 boş → Backend için kullanılabilir
- ✅ Port 5433 boş → PostgreSQL için kullanılabilir
- ✅ Port 6380 boş → Redis için kullanılabilir
- ⚠️ Port 8000 kullanılmıyor ama 8008, 8010 kullanılıyor, güvenli olması için 5000 kullandık

