# Tinisoft - Multi-Tenant E-Commerce Platform

Django tabanlı multi-tenant e-commerce SaaS platformu.

## 🏗️ Mimari

### Tek PostgreSQL Veritabanı
- **Tek veritabanı**: Tüm modüller tek PostgreSQL instance'ında
- **Schema-based multi-tenancy**: Her tenant için ayrı schema
- **Public schema**: Sistem tabloları ve tenant yönetimi
- **Tenant schemas**: `tenant_{tenant_id}` formatında (örn: `tenant_abc123`)

### Modüler Yapı
```
tinisoft/
├── apps/                    # Ana Django app
│   ├── models/             # Modeller (domain, build, tenant, vb.)
│   ├── views/              # API view'ları
│   ├── serializers/        # DRF serializers
│   ├── services/           # Business logic servisleri
│   ├── tasks/              # Celery background tasks
│   └── utils/              # Utility fonksiyonları
├── core/                   # Core utilities
│   ├── models.py          # BaseModel (UUID, timestamps, soft delete)
│   ├── db_router.py       # Multi-tenant database router
│   ├── middleware.py      # Tenant middleware
│   └── db_utils.py        # Schema yönetim fonksiyonları
└── tinisoft/              # Django project config
    ├── settings.py        # Ana ayarlar
    ├── urls.py            # URL routing
    └── celery.py          # Celery config
```

## 🚀 Kurulum

### 1. Environment Variables

`.env` dosyasını düzenle:
```bash
# Database
DB_NAME=tinisoft
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432
DB_SCHEMA=public
```

### 2. Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

### 3. Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Migration

```bash
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Run Server

```bash
python manage.py runserver
```

## 📊 Database Yapısı

### Schema Yönetimi

**Public Schema** (Sistem tabloları):
- `domains` - Tenant domain kayıtları
- `tenants` - Tenant bilgileri
- `builds` - Frontend build kayıtları
- Django sistem tabloları (auth, admin, vb.)

**Tenant Schemas** (Her tenant için):
- `tenant_{tenant_id}` - Tenant'a özel tüm tablolar
- Products, Orders, Customers, vb.

### Schema Oluşturma

```python
from core.db_utils import create_tenant_schema

# Yeni tenant için schema oluştur
create_tenant_schema('tenant_abc123')
```

## 🔧 Multi-Tenant Çalışma Mantığı

1. **Request geldiğinde**: `TenantMiddleware` domain'den tenant'ı bulur
2. **Schema ayarlanır**: `set_tenant_schema('tenant_abc123')` ile thread-local'a yazılır
3. **Database router**: Tenant-specific modeller doğru schema'ya yönlendirilir
4. **Response dönmeden önce**: Schema temizlenir

### Tenant Tespiti

- **Subdomain**: `tenant1.domains.tinisoft.com.tr` → `tenant_tenant1`
- **Custom domain**: `example.com` → Domain kaydından tenant bulunur
- **Header**: `X-Tenant-ID` header'ından tenant ID alınır

## 📦 Modüller

Tüm modüller `apps/` altında modüler yapıda:

- **models/**: Database modelleri
- **views/**: API endpoints
- **serializers/**: Request/Response serialization
- **services/**: Business logic
- **tasks/**: Celery background tasks
- **utils/**: Helper fonksiyonlar

## ✨ Özellikler

### E-Ticaret Özellikleri
- ✅ **Ürün Yönetimi**: Ürünler, kategoriler, varyantlar, görseller
- ✅ **Excel Import**: Excel'den toplu ürün yükleme, template indirme, otomatik mapping
- ✅ **Email Sistemi**: SMTP ile email gönderme, otomatik sipariş email'leri, email test
- ✅ **Sepet Sistemi**: Guest ve müşteri sepetleri
- ✅ **Sipariş Yönetimi**: Sipariş oluşturma, takip, durum güncelleme
- ✅ **Ödeme Entegrasyonları**: Kuveyt API, İyzico, PayTR (genişletilebilir)
- ✅ **Kupon Sistemi**: Kupon oluşturma, doğrulama, sepete uygulama
- ✅ **Müşteri Yönetimi**: Müşteri profilleri, adresler, sipariş geçmişi
- ✅ **Stok Yönetimi**: Stok takibi, stok hareketleri, uyarılar
- ✅ **Kargo Yönetimi**: Kargo yöntemleri, bölgeler, ücret hesaplama
- ✅ **Yorumlar**: Ürün yorumları ve puanlama
- ✅ **Favoriler**: Wishlist sistemi
- ✅ **Sadakat Programı**: Puan sistemi, işlem geçmişi
- ✅ **Hediye Kartları**: Hediye kartı yönetimi
- ✅ **Ürün Paketleri**: Bundle/ürün paketleri
- ✅ **Analytics**: Satış raporları, ürün analitikleri

### Entegrasyonlar
- ✅ **Integration API Keys**: Tüm entegrasyonlar için merkezi API key yönetimi
  - Şifreli saklama (Fernet encryption)
  - Test modu desteği
  - Desteklenen entegrasyonlar:
    - **Ödeme**: Kuveyt, İyzico, PayTR, Vakıf, Garanti, Akbank
    - **Kargo**: Aras, Yurtiçi, MNG, Sendex, Trendyol Express
    - **Marketplace**: Trendyol, Hepsiburada, N11, GittiGidiyor
    - **Diğer**: SMS, Email, Analytics

### Multi-Tenant Özellikleri
- ✅ **Tam İzolasyon**: Her tenant'ın kendi schema'sı, verileri, müşterileri
- ✅ **Domain Yönetimi**: Subdomain ve custom domain desteği
- ✅ **SSL Yönetimi**: Otomatik SSL sertifikası
- ✅ **Frontend Deployment**: Otomatik frontend build ve deployment

## 🔐 Güvenlik

- JWT authentication
- CORS yapılandırması
- Tenant izolasyonu (schema-based)
- Soft delete (is_deleted flag)
- **API Key Şifreleme**: Tüm entegrasyon API key'leri şifreli saklanır
- **Tenant İzolasyonu**: Her tenant sadece kendi verilerine erişebilir

## 📝 Notlar

- Tüm modeller `BaseModel`'den türetilir (UUID, timestamps, soft delete)
- Tenant-specific modeller `tenant` ForeignKey'ine sahiptir
- Schema'lar otomatik oluşturulur ve yönetilir
- Her tenant kendi işlemlerinden, müşterilerinden ve siparişlerinden sorumludur

## 📚 Dokümantasyon

- **[API Dokümantasyonu](README_API.md)** - API endpoint'leri ve kullanımı (Excel Import dahil)
- **[Özellikler Özeti](FEATURES_SUMMARY.md)** - Tüm özellikler ve kullanım senaryoları
- **[Integration API Keys](INTEGRATION_API_KEYS.md)** - Entegrasyon API key yönetimi
- **[Ödeme Akışı](PAYMENT_FLOW.md)** - Ödeme ve sipariş takip akışı
- **[Database Mimari](DATABASE_ARCHITECTURE.md)** - Multi-tenant database yapısı

