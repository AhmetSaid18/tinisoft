# 🌐 Domain Bağlama ve Deployment Stratejisi

## 📊 Mevcut Durum Analizi

### ✅ **MEVCUT** (Zaten var)

```csharp
// 1. Domain Entity ✅
public class Domain : BaseEntity
{
    public string Host { get; set; }           // www.marka.com
    public bool IsPrimary { get; set; }        // Ana domain mi?
    public bool IsVerified { get; set; }       // DNS doğrulandı mı?
    public string VerificationToken { get; set; } // TXT record tokeni
    public bool SslEnabled { get; set; }       // SSL aktif mi?
    public DateTime? SslExpiresAt { get; set; }
}

// 2. Multi-Tenant Routing ✅
services.AddMultiTenant<TenantInfo>()
    .WithHeaderStrategy("X-Tenant-Id")
    .WithHostStrategy() // ← Domain/Host'tan tenant bulur
    .WithEFCoreStore<TenantStoreDbContext, TenantInfo>();

// 3. Tenant Entity ✅
public class Tenant : BaseEntity
{
    public string Slug { get; set; }  // ornek-magaza (subdomain için)
    public ICollection<Domain> Domains { get; set; }
}

// 4. Plan Entity ✅
public class Plan : BaseEntity
{
    public bool CustomDomainEnabled { get; set; } // Plan limiti
}
```

**Altyapı HAZIR! 🎉** Sadece API endpoints ve deployment mekanizması eklenecek.

---

## ❌ **EKSİK OLANLAR**

### 1. **Domain Management API** ❌
- Domain ekleme/silme endpoints
- DNS verification kontrolü
- SSL sertifikası yönetimi

### 2. **Frontend Deployment** ❌
- Tema build & deploy mekanizması
- Static file serving (S3/CDN)
- Next.js/React SSR deployment

### 3. **Reverse Proxy Configuration** ❌
- Nginx/Traefik wildcard domain routing
- SSL/TLS certificate automation (Let's Encrypt)
- Load balancing

### 4. **DNS Management** ❌
- DNS record verification (TXT, CNAME)
- Cloudflare/AWS Route53 entegrasyonu

---

## 🎯 İKAS Benzeri Çalışma Akışı

### **Adım 1: Tenant Oluşturma**

```bash
POST /api/tenants/register
{
  "companyName": "Örnek Mağaza",
  "slug": "ornek-magaza",  # ornek-magaza.tinisoft.com
  "email": "info@ornekmagaza.com",
  "plan": "professional"
}

Response:
{
  "tenantId": "guid-here",
  "slug": "ornek-magaza",
  "subdomain": "https://ornek-magaza.tinisoft.com",
  "status": "active"
}
```

**Şu anda:** ✅ Tenant oluşturma zaten var  
**Eksik:** ❌ Subdomain otomatik aktif edilmesi

---

### **Adım 2: Tema Seçimi ve Özelleştirme**

```bash
POST /api/tenants/{tenantId}/template
{
  "templateCode": "fashion-modern",
  "primaryColor": "#FF5733",
  "logoUrl": "https://cdn.tinisoft.com/uploads/logo.png"
}

Response:
{
  "previewUrl": "https://ornek-magaza.tinisoft.com",
  "status": "building"
}
```

**Şu anda:** ✅ Tema seçimi var  
**Eksik:** ❌ Frontend build & deploy mekanizması

---

### **Adım 3: Custom Domain Bağlama**

```bash
POST /api/domains
{
  "host": "www.ornekmagaza.com"
}

Response:
{
  "domainId": "guid-here",
  "host": "www.ornekmagaza.com",
  "status": "pending_verification",
  "verificationMethod": "txt_record",
  "verificationToken": "tinisoft-verify=abc123xyz",
  "instructions": {
    "step1": "DNS yöneticinize gidin",
    "step2": "TXT record ekleyin:",
    "record": {
      "type": "TXT",
      "name": "_tinisoft-verification",
      "value": "tinisoft-verify=abc123xyz",
      "ttl": 3600
    },
    "step3": "CNAME record ekleyin:",
    "cname": {
      "type": "CNAME",
      "name": "www",
      "value": "ornek-magaza.tinisoft.com",
      "ttl": 3600
    }
  }
}
```

**Şu anda:** ❌ API YOK  
**Yapılacak:** Domain ekleme endpoint'i oluşturulacak

---

### **Adım 4: DNS Verification**

```bash
POST /api/domains/{domainId}/verify

Response:
{
  "domainId": "guid-here",
  "host": "www.ornekmagaza.com",
  "status": "verified",
  "verifiedAt": "2025-01-15T10:30:00Z",
  "sslStatus": "pending"
}
```

**Şu anda:** ❌ API YOK  
**Yapılacak:** DNS verification servisi

---

### **Adım 5: SSL Certificate (Let's Encrypt)**

```bash
POST /api/domains/{domainId}/ssl

Response:
{
  "domainId": "guid-here",
  "sslEnabled": true,
  "sslIssuedAt": "2025-01-15T10:35:00Z",
  "sslExpiresAt": "2025-04-15T10:35:00Z",
  "issuer": "Let's Encrypt"
}
```

**Şu anda:** ❌ Otomatik SSL YOK  
**Yapılacak:** Let's Encrypt entegrasyonu (Certbot/ACME)

---

## 🚀 DEPLOYMENT STRATEJİLERİ

### **Seçenek 1: Subdomain Routing (Başlangıç)**

#### Avantajları:
- ✅ En basit ve hızlı çözüm
- ✅ Wildcard SSL sertifikası yeterli (*.tinisoft.com)
- ✅ Nginx/Traefik ile kolay routing

#### Mimari:

```
Nginx Reverse Proxy
  ↓
  ├─ ornek-magaza.tinisoft.com → Tenant ID: xxx (WithHostStrategy ile bulunur)
  ├─ diger-magaza.tinisoft.com → Tenant ID: yyy
  └─ www.ornekmagaza.com → CNAME → ornek-magaza.tinisoft.com
```

#### Nginx Configuration:

```nginx
# /etc/nginx/conf.d/tinisoft.conf
server {
    listen 443 ssl http2;
    server_name *.tinisoft.com;

    ssl_certificate /etc/letsencrypt/live/tinisoft.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tinisoft.com/privkey.pem;

    # Subdomain'den tenant'ı bul
    location / {
        proxy_pass http://tinisoft-api:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Custom domain routing
server {
    listen 443 ssl http2;
    server_name www.ornekmagaza.com ornekmagaza.com;

    # Let's Encrypt SSL (her domain için ayrı)
    ssl_certificate /etc/letsencrypt/live/ornekmagaza.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ornekmagaza.com/privkey.pem;

    location / {
        # Custom domain'i subdomain'e redirect
        proxy_pass http://tinisoft-api:5000;
        proxy_set_header Host www.ornekmagaza.com;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

### **Seçenek 2: Traefik (Modern & Otomatik SSL)**

#### Avantajları:
- ✅ Otomatik Let's Encrypt entegrasyonu
- ✅ Dynamic routing (Docker labels ile)
- ✅ Wildcard ve custom domain desteği
- ✅ Dashboard (monitoring)

#### docker-compose.yml:

```yaml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@tinisoft.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"  # Dashboard
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"
    networks:
      - tinisoft

  api-gateway:
    image: tinisoft-api-gateway
    labels:
      # Wildcard subdomain routing
      - "traefik.enable=true"
      - "traefik.http.routers.tinisoft.rule=HostRegexp(`{subdomain:[a-z0-9-]+}.tinisoft.com`)"
      - "traefik.http.routers.tinisoft.entrypoints=websecure"
      - "traefik.http.routers.tinisoft.tls.certresolver=letsencrypt"
      - "traefik.http.routers.tinisoft.tls.domains[0].main=tinisoft.com"
      - "traefik.http.routers.tinisoft.tls.domains[0].sans=*.tinisoft.com"
      
      # Custom domain routing (database'den dinamik eklenecek)
      # Traefik API ile runtime'da eklenebilir
    networks:
      - tinisoft
```

---

### **Seçenek 3: Cloudflare + Next.js/Vercel (Enterprise)**

#### Avantajları:
- ✅ Global CDN (ultra fast)
- ✅ DDoS protection
- ✅ Otomatik SSL
- ✅ Edge functions (serverless)
- ✅ Zero-downtime deployments

#### Mimari:

```
Cloudflare CDN
  ↓
  ├─ Static Assets (S3/R2)
  │   └─ /uploads/, /themes/, /assets/
  │
  ├─ Frontend (Vercel/Next.js)
  │   └─ ornek-magaza.tinisoft.com → SSR
  │   └─ www.ornekmagaza.com → SSR
  │
  └─ Backend API (Docker/K8s)
      └─ api.tinisoft.com → REST API
```

#### Cloudflare Workers (Edge Routing):

```javascript
// Cloudflare Worker - Domain routing
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)
  const hostname = url.hostname
  
  // Custom domain → Subdomain mapping (KV Store'dan çek)
  const tenantSlug = await DOMAIN_MAPPING.get(hostname)
  
  if (tenantSlug) {
    // Custom domain'i subdomain'e route et
    url.hostname = `${tenantSlug}.tinisoft.com`
    return fetch(url, request)
  }
  
  // Default subdomain routing
  return fetch(request)
}
```

---

## 🔨 ÖNERİLEN YOLHARITASI

### **Faz 1: Subdomain Routing (1-2 Hafta)** 🟢

1. ✅ Tenant oluşturma (zaten var)
2. ❌ Subdomain otomatik aktif etme
3. ❌ WithHostStrategy test etme
4. ❌ Wildcard SSL (*.tinisoft.com)
5. ❌ Nginx/Traefik config

**Sonuç:** Müşteriler `ornek-magaza.tinisoft.com` üzerinden sitelerine erişebilir.

---

### **Faz 2: Custom Domain API (2-3 Hafta)** 🟡

1. ❌ Domain Management API (CRUD endpoints)
2. ❌ DNS Verification servisi (TXT record kontrolü)
3. ❌ CNAME validation
4. ❌ Domain status tracking (pending → verified → active)

**Sonuç:** Müşteriler kendi domain'lerini bağlayabilir (www.ornekmagaza.com).

---

### **Faz 3: SSL Automation (1-2 Hafta)** 🟡

1. ❌ Let's Encrypt entegrasyonu (Certbot/ACME)
2. ❌ Otomatik SSL sertifikası oluşturma
3. ❌ SSL renewal (90 günde bir otomatik yenileme)
4. ❌ Nginx/Traefik SSL config dinamik güncelleme

**Sonuç:** Her custom domain için otomatik HTTPS aktif olur.

---

### **Faz 4: Frontend Deployment (3-4 Hafta)** 🔴

1. ❌ Next.js/React frontend app
2. ❌ Tema build sistemi (tema seçimi → build → deploy)
3. ❌ Static file hosting (S3/R2/CDN)
4. ❌ SSR/SSG rendering
5. ❌ Preview environment (değişiklikler canlıya geçmeden önce test)

**Sonuç:** Müşteriler tema seçip customize ettiklerinde sitesi otomatik deploy olur.

---

## 🎯 HANGİ STRATEJİ DAHA İYİ?

### **MVP İçin (İlk 1000 müşteri):** Seçenek 1 (Nginx/Subdomain)
- En hızlı geliştirme
- Düşük maliyet
- Basit deployment

### **Scale İçin (10,000+ müşteri):** Seçenek 2 (Traefik)
- Otomatik SSL
- Dynamic routing
- Kolay scaling

### **Enterprise İçin (100,000+ müşteri):** Seçenek 3 (Cloudflare + Vercel)
- Global CDN
- Zero-downtime
- Ultra performance

---

## 📝 İLK ADIM: Domain Management API Oluşturma

Hemen başlayalım mı? Domain ekleme/doğrulama API'sini oluşturayım:

```csharp
// Commands:
- AddCustomDomainCommand
- VerifyDomainCommand
- RemoveDomainCommand

// Queries:
- GetDomainsQuery
- GetDomainStatusQuery

// Services:
- DnsVerificationService (TXT record kontrolü)
- SslCertificateService (Let's Encrypt)
```

---

## 🚀 HEMEN BAŞLAYALIM MI?

**Seçenekler:**
1. **Domain Management API oluştur** (Add/Verify/Remove endpoints)
2. **Nginx/Traefik config hazırla** (Wildcard subdomain routing)
3. **Frontend Deployment stratejisi planla** (Next.js/React build system)

**Hangisinden başlamak istersin?** 🎯

