# STOREFRONT API ENDPOINTS

**Base URL:** `http://localhost:8000/api/v1`

---

## 🎨 SİTE YÖNETİMİ

### 1. Site Konfigürasyonu (ANA ENDPOINT)
```
GET /storefront/config/?domain={domain}
```
**Amaç:** Tüm site ayarları (tema, menü, footer, analytics, popups)  
**Auth:** Public  
**Response:** Homepage, theme, navigation, footer, social links, announcement bar, analytics, PWA config

### 2. Preview Mode
```
GET /preview/{token}/
```
**Amaç:** Admin değişiklikleri yayınlamadan önce önizleme  
**Auth:** Public (token)

### 3. Aktif Popups
```
GET /public/popups/
Header: X-Tenant-Slug
```
**Amaç:** Newsletter, indirim, duyuru popup'ları

### 4. Form Gönder
```
POST /public/forms/{slug}/submit/
Header: X-Tenant-Slug
```
**Amaç:** İletişim, başvuru formları

---

## 👤 KULLANICI İŞLEMLERİ

### 5. Doğrulama Kodu Gönder
```
POST /tenant/{tenant_slug}/users/send-code/
Body: { phone, email }
```
**Amaç:** SMS/email doğrulama kodu gönder

### 6. Kayıt Ol
```
POST /tenant/{tenant_slug}/users/register/
Body: { phone, email, password, first_name, last_name }
```
**Amaç:** Yeni kullanıcı kaydı

### 7. Doğrulama Kodu Onayla
```
POST /tenant/{tenant_slug}/users/verify/
Body: { phone/email, code }
```
**Amaç:** Hesap aktivasyonu

### 8. Giriş Yap
```
POST /tenant/{tenant_slug}/users/login/
Body: { phone/email, password }
```
**Amaç:** Kullanıcı girişi  
**Response:** access_token, refresh_token

---

## 🛍️ ÜRÜNLER & KATEGORİLER

### 9. Ürün Listesi
```
GET /public/products/
Header: X-Tenant-Slug
Params: page, limit, category, brand, min_price, max_price, sort, search
```
**Amaç:** Ürün listeleme, filtreleme, arama

### 10. Ürün Detayı
```
GET /public/products/urun/{slug}/
Header: X-Tenant-Slug
```
**Amaç:** Ürün detay sayfası

### 11. Kategori Listesi
```
GET /public/categories/
Header: X-Tenant-Slug
```
**Amaç:** Kategoriler ve alt kategoriler

### 12. Marka Listesi
```
GET /public/brands/
Header: X-Tenant-Slug
```
**Amaç:** Markalar

### 13. Marka Detayı
```
GET /public/brands/{slug}/
Header: X-Tenant-Slug
```
**Amaç:** Marka sayfası ve ürünleri

### 14. Arama Önerileri
```
GET /search/suggestions/?q={query}
Header: X-Tenant-Slug
```
**Amaç:** Autocomplete arama

### 15. Filtre Seçenekleri
```
GET /search/filter-options/
Header: X-Tenant-Slug
```
**Amaç:** Dinamik filtre seçenekleri (fiyat aralığı, markalar)

---

## 🛒 SEPET İŞLEMLERİ

### 16. Sepeti Görüntüle
```
GET /basket/
Header: X-Tenant-Slug, Authorization: Bearer {token}
```
**Amaç:** Kullanıcı sepeti

### 17. Sepete Ekle
```
POST /basket/
Header: X-Tenant-Slug, Authorization: Bearer {token}
Body: { product_id, variant_id, quantity, currency: "TRY" }
```
**Amaç:** Ürün sepete ekleme

### 18. Sepet Güncelle
```
PATCH /basket/{item_id}/
Header: Authorization: Bearer {token}
Body: { quantity }
```
**Amaç:** Sepetteki ürün miktarını değiştir

### 19. Sepetten Çıkar
```
DELETE /basket/{item_id}/
Header: Authorization: Bearer {token}
```
**Amaç:** Ürünü sepetten sil

---

## 📍 ADRES YÖNETİMİ

### 20. Adres Listesi
```
GET /shipping/addresses/
Header: X-Tenant-Slug, Authorization: Bearer {token}
```
**Amaç:** Kullanıcının kayıtlı adresleri

### 21. Adres Ekle
```
POST /shipping/addresses/
Header: Authorization: Bearer {token}
Body: { type, title, first_name, last_name, phone, city, district, address, postal_code }
```
**Amaç:** Yeni adres ekle (billing/shipping)

### 22. Adres Güncelle
```
PATCH /shipping/addresses/{id}/
Header: Authorization: Bearer {token}
```
**Amaç:** Adres düzenle

### 23. Adres Sil
```
DELETE /shipping/addresses/{id}/
Header: Authorization: Bearer {token}
```
**Amaç:** Adres sil

---

## 🚚 KARGO & ÖDEME YÖNTEMLERİ

### 24. Kargo Ücretini Hesapla
```
POST /shipping/calculate/
Header: X-Tenant-Slug, Authorization: Bearer {token}
Body: { shipping_address_id, cart_items }
```
**Amaç:** Kargo ücreti hesaplama

### 25. Kargo Yöntemleri
```
GET /shipping/methods/
Header: X-Tenant-Slug
```
**Amaç:** Mevcut kargo seçenekleri

---

## 💳 SİPARİŞ & ÖDEME

### 26. Sipariş Oluştur
```
POST /orders/
Header: X-Tenant-Slug, Authorization: Bearer {token}
Body: {
  selected_cart_item_ids,
  shipping_address_id,
  billing_address_id,
  shipping_method_id,
  payment_method,
  coupon_code (optional)
}
```
**Amaç:** Sipariş oluşturma  
**Response:** order_id, total_amount

### 27. Ödeme Başlat
```
POST /payments/create/
Header: Authorization: Bearer {token}
Body: {
  order_id,
  payment_provider: "kuveyt_turk",
  card_holder_name,
  card_number,
  expire_month,
  expire_year,
  cvv
}
```
**Amaç:** 3D Secure ödeme başlat  
**Response:** redirect_url (3D Secure sayfası)

### 28. Ödeme Doğrula
```
POST /payments/verify/
Body: { /* 3D Secure callback data */ }
```
**Amaç:** 3D Secure sonrası ödeme doğrulama

### 29. Sipariş Takibi
```
GET /orders/track/{order_number}/
```
**Amaç:** Sipariş durumu sorgulama (public)

### 30. Siparişlerim
```
GET /orders/
Header: Authorization: Bearer {token}
Params: page, limit, status
```
**Amaç:** Kullanıcının tüm siparişleri

### 31. Sipariş Detayı
```
GET /orders/{order_id}/
Header: Authorization: Bearer {token}
```
**Amaç:** Sipariş detayları

---

## 💰 KUPON & İNDİRİMLER

### 32. Kupon Doğrula
```
POST /coupons/validate/
Header: X-Tenant-Slug, Authorization: Bearer {token}
Body: { code, cart_items }
```
**Amaç:** Kupon kodu kontrolü  
**Response:** discount_amount, is_valid

### 33. Aktif Kuponlar
```
GET /public/coupons/
Header: X-Tenant-Slug
```
**Amaç:** Public kuponlar (görünür olanlar)

---

## ❤️ FAVORİLER & KARŞILAŞTIRMA

### 34. Favori Listesi
```
GET /wishlists/
Header: Authorization: Bearer {token}
```
**Amaç:** Kullanıcının favori listeleri

### 35. Favorilere Ekle
```
POST /wishlists/{wishlist_id}/items/
Header: Authorization: Bearer {token}
Body: { product_id }
```
**Amaç:** Ürün favoriye ekle

### 36. Favoriden Çıkar
```
DELETE /wishlists/items/remove/
Header: Authorization: Bearer {token}
Body: { product_id }
```
**Amaç:** Ürün favoriden sil

### 37. Karşılaştırma Listesi
```
GET /compare/
Header: X-Tenant-Slug
```
**Amaç:** Karşılaştırma listesi (session-based)

### 38. Karşılaştırmaya Ekle
```
POST /compare/add/
Header: X-Tenant-Slug
Body: { product_id }
```
**Amaç:** Ürün karşılaştırmaya ekle

### 39. Karşılaştırma Detayları
```
GET /compare/products/
Header: X-Tenant-Slug
```
**Amaç:** Karşılaştırılan ürünlerin detaylı bilgileri

---

## ⭐ ÜRÜN YORUMLARI

### 40. Ürün Yorumları
```
GET /products/{product_id}/reviews/
Params: page, limit, sort
```
**Amaç:** Ürün yorumları (public)

### 41. Yorum Yaz
```
POST /products/{product_id}/reviews/create/
Header: Authorization: Bearer {token}
Body: { rating, title, comment }
```
**Amaç:** Yorum ekleme (satın alan kullanıcılar)

### 42. Yorum Faydalı
```
POST /reviews/{review_id}/helpful/
Body: { helpful: true/false }
```
**Amaç:** Yorumu beğen/beğenme

---

## 🎁 SADAKAT PUANLARI

### 43. Puanlarım
```
GET /loyalty/my-points/
Header: Authorization: Bearer {token}
```
**Amaç:** Kullanıcı puan bakiyesi

### 44. Puan Hareketleri
```
GET /loyalty/transactions/
Header: Authorization: Bearer {token}
```
**Amaç:** Puan geçmişi

---

## 📊 ANALYTİCS (Opsiyonel)

### 45. Event Kaydet
```
POST /analytics/events/
Header: X-Tenant-Slug
Body: { event_type, product_id, category, metadata }
```
**Amaç:** Kullanıcı davranışları (view, add_to_cart, purchase)

---

## 💱 PARA BİRİMİ

### 46. Para Birimleri
```
GET /public/currencies/
```
**Amaç:** Aktif para birimleri (TRY, USD, EUR)

### 47. Güncel Kurlar
```
GET /public/currency/exchange-rates/
```
**Amaç:** TCMB döviz kurları

---

## 🔔 KULLANICI PROFİLİ

### 48. Profil Bilgilerim
```
GET /customers/{customer_id}/
Header: Authorization: Bearer {token}
```
**Amaç:** Kullanıcı profili

### 49. Profil Güncelle
```
PATCH /customers/{customer_id}/
Header: Authorization: Bearer {token}
Body: { first_name, last_name, phone, email }
```
**Amaç:** Profil düzenleme

---

## 📋 ÖZEL SAYFALAR (Dinamik)

### 50. Sayfa İçeriği
```
/public/{page_slug}/
```
**Amaç:** Hakkımızda, İletişim, SSS gibi sayfalar  
**Not:** Config API'den alınan `pages` array'inden render edilir

---

## 🎯 KULLANIM ÖNCELİĞİ

### **İlk Yüklenişte (Required):**
1. `/storefront/config/` - Site config
2. `/public/currencies/` - Para birimleri
3. `/public/popups/` - Aktif popups

### **Homepage:**
4. `/public/products/` - Ürünler (featured)
5. `/public/categories/` - Kategoriler

### **Ürün Detay:**
6. `/public/products/urun/{slug}/` - Ürün detayı
7. `/products/{id}/reviews/` - Yorumlar

### **Sepet & Checkout:**
8. `/basket/` - Sepet
9. `/shipping/addresses/` - Adresler
10. `/shipping/calculate/` - Kargo ücreti
11. `/coupons/validate/` - Kupon
12. `/orders/` - Sipariş oluştur
13. `/payments/create/` - Ödeme

### **Kullanıcı:**
14. `/tenant/{slug}/users/login/` - Giriş
15. `/wishlists/` - Favoriler
16. `/orders/` - Siparişlerim

---

## 📌 HEADER KULLANIMI

**Tüm Public Endpoint'lerde:**
```
X-Tenant-Slug: avrupa-mutfak
```

**Authenticated Endpoint'lerde:**
```
X-Tenant-Slug: avrupa-mutfak
Authorization: Bearer {access_token}
```

---

## 🚀 NEXT.JS ENTEGRASYON ÖRNEĞİ

```typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL

export async function apiClient(tenantSlug: string, token?: string) {
  return axios.create({
    baseURL: API_URL,
    headers: {
      'X-Tenant-Slug': tenantSlug,
      ...(token && { 'Authorization': `Bearer ${token}` })
    }
  })
}

// Kullanım
const client = await apiClient('avrupa-mutfak', userToken)
const products = await client.get('/public/products/')
```

---

**Toplam:** 50 endpoint  
**Son Güncelleme:** 2026-01-16
