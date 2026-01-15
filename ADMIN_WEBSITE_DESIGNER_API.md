# TENANT ADMIN - WEBSITE BUILDER API (FULL REFERENCE)

Bu doküman, Tenant Admin Panelindeki "Website Builder" modülünün tüm yeteneklerini kapsar.
Buradaki endpoint'ler ile **Shopify benzeri** tam kapsamlı bir site yönetim paneli oluşturulabilir.

**Base URL:** `http://localhost:8000/api/v1`  
**Auth:** `Authorization: Bearer {tenant_token}`

---

## 🎨 1. GENEL GÖRÜNÜM & TEMA (Theme Settings)

Sitenin logosu, renkleri, fontları ve genel ayarları.

### 📍 Mevcut Ayarları Getir
`GET /tenant/website/template/`

### 📍 Ayarları Güncelle
`PUT /tenant/website/template/`

**Request Body (Örnekler):**

#### A. Logo ve Favicon
```json
{
  "site_logo_url": "https://cdn.../logo.png",
  "favicon_url": "https://cdn.../favicon.ico",
  "site_name": "Avrupa Mutfak"
}
```

#### B. Renk Paleti
```json
{
  "theme_config": {
    "colors": {
      "primary": "#FF0000",    // Ana renk (butonlar vs)
      "secondary": "#000000",  // İkincil renk
      "accent": "#FFD700",     // Vurgu rengi
      "background": "#FFFFFF", // Arka plan
      "text": "#1F2937"        // Yazı rengi
    },
    "typography": {
      "fontFamily": "'Inter', sans-serif"
    }
  }
}
```

#### C. Sosyal Medya Linkleri
```json
{
  "social_links": {
    "instagram": "https://instagram.com/...",
    "facebook": "https://facebook.com/...",
    "twitter": "https://twitter.com/...",
    "youtube": "https://youtube.com/...",
    "whatsapp": "+90555..."
  }
}
```

#### D. PWA (Mobil Uygulama) Ayarları
```json
{
  "pwa_config": {
    "enabled": true,
    "app_name": "Mutfak Sepeti",
    "theme_color": "#FF0000",
    "background_color": "#FFFFFF"
  }
}
```

#### E. Özel Kod (Custom CSS/JS)
```json
{
  "custom_css": "body { background: #f0f0f0; }",
  "custom_js": "console.log('Takip kodu');"
}
```

---

## 🏠 2. ANA SAYFA DÜZENİ (Homepage Builder)

Sürükle-bırak yapılabilecek component bazlı anasayfa yönetimi.

### 📍 Kaydet
`PUT /tenant/website/template/`

**Request Body:**
```json
{
  "homepage_config": {
    "sections": [
      // 1. Hero Slider
      {
        "id": "hero-1",
        "type": "hero-slider",
        "slides": [
          {
            "image": "https://cdn.../slide1.jpg",
            "title": "Büyük İndirim",
            "buttonText": "İncele",
            "link": "/kampanyalar"
          }
        ]
      },
      // 2. Öne Çıkanlar
      {
        "id": "featured",
        "type": "product-grid",
        "title": "Çok Satanlar",
        "limit": 8,
        "columns": 4
      },
      // 3. Banner
      {
        "id": "banner-1",
        "type": "image-banner",
        "image": "https://cdn.../banner.jpg"
      }
    ]
  }
}
```

---

## 🔗 3. MENÜ YÖNETİMİ (Navigation)

Header (üst) ve Sidebar menülerinin yönetimi. Nested (iç içe) yapı destekler.

### 📍 Kaydet
`PUT /tenant/website/template/`

**Request Body:**
```json
{
  "navigation_menus": {
    "header": {
      "items": [
        {"label": "Ana Sayfa", "url": "/", "icon": "home"},
        {
          "label": "Ürünler",
          "url": "/urunler",
          "children": [
            {"label": "Mutfak", "url": "/mutfak"},
            {"label": "Banyo", "url": "/banyo"}
          ]
        },
        {"label": "İletişim", "url": "/iletisim"}
      ]
    }
  }
}
```

---

## 🦶 4. FOOTER YÖNETİMİ

Site alt kısmının yönetimi. Kolonlar, linkler ve telif hakkı yazısı.

### 📍 Kaydet
`PUT /tenant/website/template/`

**Request Body:**
```json
{
  "footer_config": {
    "columns": [
      {
        "title": "Kurumsal",
        "links": [
          {"text": "Hakkımızda", "url": "/hakkimizda"},
          {"text": "Gizlilik", "url": "/gizlilik"}
        ]
      },
      {
        "title": "Yardım",
        "links": [
          {"text": "SSS", "url": "/sss"},
          {"text": "İade", "url": "/iade"}
        ]
      }
    ],
    "bottom_text": "© 2024 Tüm hakları saklıdır.",
    "payment_icons": ["visa", "mastercard", "amex"]
  }
}
```

---

## 📢 5. DUYURU BARI (Announcement Bar)

Sitenin en tepesindeki ince bant (örn: "Kargo Bedava!").

### 📍 Kaydet
`PUT /tenant/website/template/`

**Request Body:**
```json
{
  "announcement_bar": {
    "enabled": true,
    "text": "🎉 500TL üzeri kargo bedava!",
    "link": "/kampanyalar",
    "backgroundColor": "#000000",
    "textColor": "#FFFFFF",
    "position": "top"
  }
}
```

---

## 📄 6. SAYFA YÖNETİMİ (Page Builder)

Özel sayfalar (Hakkımızda, SSS, Landing Page).

### 📍 Sayfaları Listele
`GET /tenant/website/pages/`

### 📍 Yeni Sayfa Ekle
`POST /tenant/website/pages/`
```json
{
  "title": "Hakkımızda",
  "slug": "hakkimizda",
  "page_config": { "sections": [...] }, // Homepage gibi
  "is_active": true,
  "show_in_menu": true
}
```

### 📍 Düzenle
`PUT /tenant/website/pages/{id}/`

### 📍 Sil
`DELETE /tenant/website/pages/{id}/`

---

## 📝 7. FORM BUILDER

Müşterilerden bilgi toplamak için formlar (İletişim, Başvuru).

### 📍 Formları Listele
`GET /tenant/website/forms/`

### 📍 Yeni Form Ekle
`POST /tenant/website/forms/`
```json
{
  "name": "İletişim Formu",
  "slug": "iletisim",
  "form_config": {
    "fields": [
      {"type": "text", "name": "ad_soyad", "label": "Adınız", "required": true},
      {"type": "email", "name": "email", "label": "E-posta", "required": true}
    ],
    "submit_action": {
      "type": "email",
      "email_to": "info@site.com"
    }
  }
}
```

### 📍 Gelen Mesajları Gör (Submissions)
`GET /tenant/website/forms/{id}/submissions/`

---

## 🔔 8. POPUP YÖNETİMİ

Kampanya, Newsletter veya Uyarı popup'ları.

### 📍 Listele
`GET /tenant/website/popups/`

### 📍 Ekle
`POST /tenant/website/popups/`
```json
{
  "name": "Bülten Aboneliği",
  "type": "newsletter",
  "content": {
    "title": "İndirim Kazan",
    "description": "Abone ol %10 kazan"
  },
  "trigger": {
    "type": "exit_intent" // Çıkarken göster
  },
  "is_active": true
}
```

---

## 🖼️ 9. MEDYA KÜTÜPHANESİ

Resim ve video yükleme alanı. (Cloudflare R2 entegreli)

### 📍 Dosya Yükle
`POST /tenant/website/media/upload/`
(Multipart Form Data: file, type='image')

**Response:**
```json
{"url": "https://cdn.../resim.jpg"}
```

### 📍 Dosyaları Gör
`GET /tenant/website/media/list/`

### 📍 Sil
`DELETE /tenant/website/media/delete/`

---

## 🔀 10. SEO & YÖNLENDİRMELER

Eski linkleri yeniye yönlendirme (301 Redirect).

### 📍 Listele
`GET /tenant/website/redirects/`

### 📍 Ekle
`POST /tenant/website/redirects/`
```json
{
  "from_url": "/eski-sayfa",
  "to_url": "/yeni-sayfa",
  "redirect_type": "301"
}
```

---

## 📊 11. ANALYTICS (Takip Kodları)

Google ve Facebook pikselleri.

### 📍 Kaydet
`PUT /tenant/website/template/`
```json
{
  "analytics_config": {
    "google_analytics": { "enabled": true, "tracking_id": "UA-XXXX" },
    "facebook_pixel": { "enabled": true, "pixel_id": "123456" }
  }
}
```

---

## ⏳ 12. VERSİYON GEÇMİŞİ & UNDO

Yanlışlıkla yapılan değişiklikleri geri alma.

### 📍 Geçmişi Gör
`GET /tenant/website/template/revisions/`

### 📍 Geri Yükle (Restore)
`POST /tenant/website/template/revisions/{id}/restore/`

---

## 👁️ 13. ÖNİZLEME (Preview Mode)

Değişiklikleri müşterilere göstermeden önce görme.

### 📍 Preview Aç
`POST /tenant/website/template/preview/enable/`
**Response:** `preview_url` (Bunu yeni sekmede açtır)

### 📍 Preview Kapat (Yayınla)
`POST /tenant/website/template/preview/disable/`

---

## 📦 14. HAZIR ŞABLONLAR (Template Store)

Tek tıkla site tasarımını değiştirme.

### 📍 Şablonları Gör
`GET /tenant/website/templates/available/`

### 📍 Şablonu Uygula
`POST /tenant/website/templates/apply/`
```json
{ "template_key": "modern-minimalist" }
```

---
**Toplam Endpoint Sayısı:** 29+
**Kapsam:** %100 Full Site Yönetimi
