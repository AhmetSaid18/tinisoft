# Template Selection Guide

## Template Seçim Kuralları

### 1. Custom Domain Varsa
- ✅ **Template seçimi zorunlu**
- Kullanıcı kendi template'ini seçebilir (default, modern, classic, vb.)
- Domain doğrulandığında seçilen template ile frontend build yapılır
- Custom domain'de kullanıcının seçtiği template yayınlanır

**Örnek:**
```json
{
  "store_name": "My Store",
  "store_slug": "my-store",
  "custom_domain": "example.com",
  "template": "modern"  // ← Zorunlu, seçilen template
}
```

### 2. Custom Domain Yoksa
- ❌ **Template seçimi yapılamaz**
- Subdomain bizim template'imizle (`default`) yayınlanır
- `template` field'ı gönderilse bile yok sayılır
- Subdomain: `{store-slug}.domains.tinisoft.com.tr` → Bizim template

**Örnek:**
```json
{
  "store_name": "My Store",
  "store_slug": "my-store"
  // custom_domain yok → template seçilemez
  // Subdomain bizim template ile yayınlanır
}
```

## API Response

### Register Response (Custom Domain ile)
```json
{
  "success": true,
  "tenant": {
    "template": "modern"  // ← Kullanıcının seçtiği template
  },
  "custom_domain": "example.com",
  "template": "modern"
}
```

### Register Response (Sadece Subdomain)
```json
{
  "success": true,
  "tenant": {
    "template": "default"  // ← Bizim template (zorunlu)
  },
  "subdomain_url": "https://my-store.domains.tinisoft.com.tr"
  // custom_domain yok → template seçilemez
}
```

## Frontend Build Süreci

1. **Subdomain Build:**
   - Template: `default` (bizim template)
   - URL: `{store-slug}.domains.tinisoft.com.tr`
   - Otomatik yayınlanır

2. **Custom Domain Build:**
   - Template: Kullanıcının seçtiği template
   - URL: `example.com`
   - Domain doğrulandıktan sonra yayınlanır

## Hata Durumları

### Template seçimi ama custom domain yok:
```json
{
  "template": ["Template seçimi sadece custom domain girildiğinde yapılabilir. Subdomain için bizim template kullanılacak."]
}
```

### Custom domain var ama template yok:
- Otomatik olarak `default` template atanır

