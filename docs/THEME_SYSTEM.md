# 🎨 Tema Sistemi (Theme System)

Bu dokümantasyon, Tinisoft e-ticaret platformunda tema sisteminin nasıl çalıştığını açıklar.

---

## 📋 İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Mimari](#mimari)
3. [Frontend Ekibi İçin](#frontend-ekibi-için)
4. [Backend API'leri](#backend-apileri)
5. [Tema Ekleme Adımları](#tema-ekleme-adımları)
6. [İsimlendirme Kuralları](#isimlendirme-kuralları)
7. [Örnek Kullanım](#örnek-kullanım)

---

## Genel Bakış

Tinisoft, **Single Frontend Multi-Tenant** mimarisi kullanır. Bu demek ki:

- **Tek bir frontend uygulaması** tüm müşterilere hizmet verir
- Her müşteri **farklı tema** seçebilir
- Tema dosyaları **frontend repo'sunda** tutulur
- Tema **ayarları** (seçim, renkler, fontlar) **backend database'de** tutulur

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   TEMA DOSYALARI (HTML, CSS, JSX)    →    FRONTEND REPO            │
│   TEMA AYARLARI (Seçim, Renkler)     →    BACKEND DATABASE         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Mimari

### Akış Diyagramı

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. Müşteri sitesine girer: mustafa-giyim.com                       │
│                              ↓                                      │
│  2. Frontend yüklenir                                               │
│                              ↓                                      │
│  3. Frontend API'yi çağırır:                                        │
│     GET /api/storefront/bootstrap                                   │
│                              ↓                                      │
│  4. API Response:                                                   │
│     {                                                               │
│       "templateKey": "fashion-boutique",  ← HANGİ TEMA?            │
│       "theme": { "primaryColor": "#C9A962" },                       │
│       "settings": { "logoUrl": "..." }                              │
│     }                                                               │
│                              ↓                                      │
│  5. Frontend templateKey'e göre doğru temayı yükler                │
│                              ↓                                      │
│  6. Tema render edilir!                                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Veri Akışı

| Veri | Nereden Geliyor? | Nereye Gidiyor? |
|------|------------------|-----------------|
| `templateKey` | Backend DB (Tenant.SelectedTemplateCode) | Frontend → Hangi tema yüklenecek? |
| `theme.primaryColor` | Backend DB (Tenant.PrimaryColor) | Frontend → CSS variables |
| `settings.logoUrl` | Backend DB (Tenant.LogoUrl) | Frontend → Header component |
| Tema dosyaları | Frontend repo (`src/themes/`) | Browser → Render |

---

## Frontend Ekibi İçin

### Klasör Yapısı

```
frontend-repo/
├── src/
│   ├── themes/
│   │   ├── minimal/              ← Her tema bir klasör
│   │   │   ├── components/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   └── ProductCard.tsx
│   │   │   ├── layouts/
│   │   │   │   ├── MainLayout.tsx
│   │   │   │   └── ProductLayout.tsx
│   │   │   ├── pages/
│   │   │   │   ├── HomePage.tsx
│   │   │   │   └── ProductPage.tsx
│   │   │   ├── styles/
│   │   │   │   └── theme.css
│   │   │   └── index.tsx         ← Theme entry point
│   │   │
│   │   ├── fashion-boutique/     ← Başka bir tema
│   │   │   └── ...
│   │   │
│   │   └── tech-store/           ← Başka bir tema
│   │       └── ...
│   │
│   └── App.tsx                   ← Theme loader
```

### Theme Entry Point Örneği

```tsx
// src/themes/fashion-boutique/index.tsx

import { BootstrapData } from '@/types';
import MainLayout from './layouts/MainLayout';
import HomePage from './pages/HomePage';
import ProductPage from './pages/ProductPage';

interface ThemeProps {
  bootstrap: BootstrapData;
}

const FashionBoutiqueTheme = ({ bootstrap }: ThemeProps) => {
  return (
    <MainLayout bootstrap={bootstrap}>
      {/* Router ile sayfa yönetimi */}
    </MainLayout>
  );
};

export default FashionBoutiqueTheme;
```

### App.tsx - Tema Yükleme

```tsx
// src/App.tsx

import { useEffect, useState, lazy, Suspense } from 'react';

const App = () => {
  const [bootstrap, setBootstrap] = useState(null);
  const [ThemeComponent, setThemeComponent] = useState(null);

  useEffect(() => {
    // 1. API'den bootstrap data al
    fetch('/api/storefront/bootstrap')
      .then(res => res.json())
      .then(async (data) => {
        setBootstrap(data);
        
        // 2. templateKey'e göre doğru temayı yükle
        const theme = await import(`./themes/${data.templateKey}`);
        setThemeComponent(() => theme.default);
      });
  }, []);

  if (!ThemeComponent) return <Loading />;

  // 3. Temayı render et
  return (
    <Suspense fallback={<Loading />}>
      <ThemeComponent bootstrap={bootstrap} />
    </Suspense>
  );
};

export default App;
```

### CSS Variables Kullanımı

```css
/* src/themes/fashion-boutique/styles/theme.css */

:root {
  /* Bu değerler bootstrap.theme'den gelecek */
  --primary-color: var(--tenant-primary);
  --secondary-color: var(--tenant-secondary);
  --font-family: var(--tenant-font);
}

.header {
  background-color: var(--primary-color);
}

.button {
  background-color: var(--primary-color);
  font-family: var(--font-family);
}
```

```tsx
// CSS variables'ı set et
useEffect(() => {
  if (bootstrap?.theme) {
    document.documentElement.style.setProperty(
      '--tenant-primary', 
      bootstrap.theme.primaryColor
    );
    document.documentElement.style.setProperty(
      '--tenant-font', 
      bootstrap.theme.fontFamily
    );
  }
}, [bootstrap]);
```

---

## Backend API'leri

### Müşteri (Storefront) API'leri

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/api/storefront/bootstrap` | GET | Tema ve site ayarlarını getir |
| `/api/templates/available` | GET | Seçilebilir temaları listele |
| `/api/templates/select` | POST | Tema seç |
| `/api/templates/selected` | GET | Seçili temayı göster |

### Admin API'leri (Tema Yönetimi)

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/api/admin/templates` | GET | Tüm temaları listele |
| `/api/admin/templates` | POST | Yeni tema ekle |
| `/api/admin/templates/{id}` | PUT | Tema güncelle |
| `/api/admin/templates/{id}` | DELETE | Tema sil |
| `/api/admin/templates/{id}/toggle-active` | PATCH | Tema aktif/pasif |

### Bootstrap Response Örneği

```json
{
  "tenantId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "tenantName": "Mustafa Giyim",
  "templateKey": "fashion-boutique",
  "templateVersion": 1,
  "theme": {
    "primaryColor": "#C9A962",
    "secondaryColor": "#1A1A1A",
    "backgroundColor": "#FFFFFF",
    "textColor": "#333333",
    "linkColor": "#C9A962",
    "buttonColor": "#C9A962",
    "buttonTextColor": "#FFFFFF",
    "fontFamily": "Poppins",
    "headingFontFamily": "Playfair Display",
    "baseFontSize": 16,
    "layoutSettings": {
      "headerStyle": "sticky",
      "productGridColumns": 4
    }
  },
  "settings": {
    "logoUrl": "https://cdn.example.com/logo.png",
    "faviconUrl": "https://cdn.example.com/favicon.ico",
    "siteTitle": "Mustafa Giyim",
    "siteDescription": "En kaliteli giyim ürünleri",
    "facebookUrl": "https://facebook.com/mustafagiyim",
    "instagramUrl": "https://instagram.com/mustafagiyim",
    "email": "info@mustafagiyim.com",
    "phone": "+90 555 123 4567",
    "address": "İstanbul, Türkiye"
  }
}
```

---

## Tema Ekleme Adımları

### Adım 1: Frontend - Tema Klasörü Oluştur

```bash
# Frontend repo'sunda
mkdir -p src/themes/my-new-theme/components
mkdir -p src/themes/my-new-theme/layouts
mkdir -p src/themes/my-new-theme/pages
mkdir -p src/themes/my-new-theme/styles

# Entry point oluştur
touch src/themes/my-new-theme/index.tsx
```

### Adım 2: Backend - Tema Kaydı Ekle

```bash
# API isteği
curl -X POST https://api.tinisoft.com/api/admin/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{
    "code": "my-new-theme",
    "name": "My New Theme",
    "description": "Güzel bir tema açıklaması",
    "version": 1,
    "previewImageUrl": "/previews/my-new-theme.jpg",
    "isActive": true
  }'
```

### Adım 3: Müşteri - Tema Seç

```bash
# Müşteri dashboard'dan veya API ile
curl -X POST https://api.tinisoft.com/api/templates/select \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <USER_TOKEN>" \
  -d '{
    "templateCode": "my-new-theme"
  }'
```

---

## İsimlendirme Kuralları

### ⚠️ KRİTİK KURAL

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   FRONTEND klasör adı  ═══  BACKEND template code                  │
│                                                                     │
│   src/themes/example/   ←→   code: "example"                       │
│   src/themes/fashion/   ←→   code: "fashion"                       │
│   src/themes/minimal/   ←→   code: "minimal"                       │
│                                                                     │
│   İKİSİ BİREBİR AYNI OLMALI!                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Doğru İsimlendirme

```
✅ kebab-case kullan (küçük harf, tire ile ayır)

Örnekler:
  - fashion-boutique
  - tech-store
  - minimal
  - my-new-theme
  - kids-toys-2024
```

### Yanlış İsimlendirme

```
❌ Boşluk kullanma
   YANLIŞ: "Fashion Boutique"
   DOĞRU:  "fashion-boutique"

❌ Büyük harf kullanma
   YANLIŞ: "FashionBoutique"
   DOĞRU:  "fashion-boutique"

❌ Alt çizgi kullanma
   YANLIŞ: "fashion_boutique"
   DOĞRU:  "fashion-boutique"

❌ Özel karakter kullanma
   YANLIŞ: "fashion@boutique"
   DOĞRU:  "fashion-boutique"
```

---

## Örnek Kullanım

### Senaryo: "Luxury Gold" Teması Ekleme

**1. Frontend ekibi tema klasörünü oluşturur:**

```
src/themes/luxury-gold/
├── components/
│   ├── Header.tsx
│   ├── Footer.tsx
│   └── ProductCard.tsx
├── layouts/
│   └── MainLayout.tsx
├── pages/
│   ├── HomePage.tsx
│   └── ProductPage.tsx
├── styles/
│   └── theme.css
└── index.tsx
```

**2. Frontend ekibi backend'ciye söyler:**

> "luxury-gold adında yeni tema yaptım, backend'e ekler misin?"

**3. Backend'ci API'ye ekler:**

```bash
POST /api/admin/templates
{
  "code": "luxury-gold",        # ← Klasör adıyla aynı!
  "name": "Luxury Gold",
  "description": "Altın tonlarıyla lüks tasarım",
  "version": 1,
  "previewImageUrl": "/previews/luxury-gold.jpg"
}
```

**4. Müşteri bu temayı seçer:**

```bash
POST /api/templates/select
{
  "templateCode": "luxury-gold"
}
```

**5. Müşterinin sitesi artık luxury-gold temasıyla çalışır!**

---

## Sık Sorulan Sorular

### Tema dosyaları nerede tutulur?

Frontend repo'sunda, `src/themes/` klasörü altında.

### Tema ayarları nerede tutulur?

Backend database'de, `Tenant` tablosunda:
- `SelectedTemplateCode` - Seçilen tema
- `PrimaryColor`, `FontFamily`, vs. - Özelleştirmeler

### Müşteri tema değiştirebilir mi?

Hayır, tema seçimi tek seferliktir. `SelectTemplate` API'si zaten seçim yapılmışsa hata döner.

### Yeni tema eklenince mevcut müşteriler etkilenir mi?

Hayır. Her müşteri kendi seçtiği temayı kullanmaya devam eder.

### Tema güncellemesi nasıl yapılır?

Frontend'de tema klasörünü güncelleyin ve deploy edin. Tüm müşteriler otomatik olarak güncel temayı alır.

---

## İletişim

Sorularınız için backend ekibine ulaşın.

