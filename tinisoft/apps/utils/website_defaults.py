"""
Pre-built Website Templates
WordPress benzeri hazır temalar - tenant'lar seçip kullanabilir
"""

# ==============================================
# TEMPLATE 1: MODERN MINIMALIST
# ==============================================

TEMPLATE_MODERN_MINIMALIST = {
    "name": "Modern Minimalist",
    "description": "Sade, şık ve hızlı. Modern e-ticaret siteleri için mükemmel.",
    "theme_config": {
        "colors": {
            "primary": "#000000",
            "secondary": "#1F2937",
            "accent": "#FF6B6B",
            "background": "#FFFFFF",
            "backgroundAlt": "#F9FAFB",
            "text": "#111827",
            "textSecondary": "#6B7280",
            "border": "#E5E7EB",
            "success": "#10B981",
            "warning": "#F59E0B",
            "error": "#EF4444",
        },
        "typography": {
            "fontFamily": "'Outfit', 'Inter', sans-serif",
            "headingFont": "'Outfit', sans-serif",
            "fontSize": {
                "xs": "0.75rem",
                "sm": "0.875rem",
                "base": "1rem",
                "lg": "1.125rem",
                "xl": "1.25rem",
                "2xl": "1.5rem",
                "3xl": "2rem",
                "4xl": "2.5rem",
                "5xl": "3.5rem"
            },
            "fontWeight": {
                "light": "300",
                "normal": "400",
                "medium": "500",
                "semibold": "600",
                "bold": "700"
            }
        },
        "spacing": {
            "containerMaxWidth": "1400px",
            "sectionPadding": "5rem",
            "cardPadding": "2rem",
            "buttonPadding": "1rem 2rem"
        },
        "borderRadius": {
            "none": "0",
            "sm": "0.125rem",
            "md": "0.25rem",
            "lg": "0.5rem",
            "full": "9999px"
        },
        "shadows": {
            "none": "none",
            "sm": "0 1px 3px rgba(0, 0, 0, 0.05)",
            "md": "0 4px 12px rgba(0, 0, 0, 0.08)",
            "lg": "0 8px 24px rgba(0, 0, 0, 0.12)"
        },
        "animation": {
            "duration": "0.3s",
            "easing": "cubic-bezier(0.4, 0, 0.2, 1)"
        }
    },
    "homepage_config": {
        "sections": [
            {
                "id": "hero-minimal",
                "type": "hero-minimal",
                "title": "Sadelik, Zarafet, Kalite",
                "subtitle": "Modern yaşam tarzınız için özenle seçilmiş ürünler",
                "buttonText": "Koleksiyonu Keşfet",
                "buttonLink": "/urunler",
                "layout": "centered",
                "typography": "large",
                "showScrollIndicator": True,
                "backgroundColor": "#F9FAFB"
            },
            {
                "id": "featured-minimal",
                "type": "product-grid-minimal",
                "title": "Yeni Koleksiyon",
                "displayType": "latest",
                "limit": 4,
                "columns": 4,
                "layout": "clean",
                "spacing": "wide",
                "showPrice": True,
                "showAddToCart": False,
                "hoverEffect": "fade"
            },
            {
                "id": "banner-split",
                "type": "split-banner",
                "items": [
                    {
                        "title": "Erkek Koleksiyonu",
                        "subtitle": "Yeni Sezon",
                        "link": "/kategoriler/erkek",
                        "image": "",
                        "overlay": "dark"
                    },
                    {
                        "title": "Kadın Koleksiyonu",
                        "subtitle": "Trendler",
                        "link": "/kategoriler/kadin",
                        "image": "",
                        "overlay": "dark"
                    }
                ]
            },
            {
                "id": "bestsellers",
                "type": "product-carousel",
                "title": "Çok Satanlar",
                "displayType": "bestselling",
                "limit": 8,
                "autoplay": True,
                "showDots": True,
                "layout": "minimal"
            },
            {
                "id": "values",
                "type": "icon-grid",
                "items": [
                    {
                        "icon": "package",
                        "title": "Ücretsiz Kargo",
                        "description": "500₺ ve üzeri"
                    },
                    {
                        "icon": "shield-check",
                        "title": "Güvenli Alışveriş",
                        "description": "SSL sertifikalı"
                    },
                    {
                        "icon": "refresh-cw",
                        "title": "Kolay İade",
                        "description": "15 gün garantisi"
                    },
                    {
                        "icon": "award",
                        "title": "Orijinal Ürün",
                        "description": "%100 garantili"
                    }
                ],
                "layout": "horizontal",
                "backgroundColor": "transparent"
            }
        ]
    },
    "navigation_menus": {
        "header": {
            "items": [
                {"label": "Ana Sayfa", "url": "/", "icon": "home"},
                {"label": "Ürünler", "url": "/urunler"},
                {"label": "Kategoriler", "url": "/kategoriler"},
                {"label": "Hakkımızda", "url": "/hakkimizda"},
                {"label": "İletişim", "url": "/iletisim"}
            ]
        }
    },
    "footer_config": {
        "columns": [
            {
                "title": "Kurumsal",
                "links": [
                    {"text": "Hakkımızda", "url": "/hakkimizda"},
                    {"text": "İletişim", "url": "/iletisim"},
                    {"text": "Gizlilik Politikası", "url": "/gizlilik-politikasi"},
                    {"text": "Kullanım Koşulları", "url": "/kullanim-kosullari"}
                ]
            },
            {
                "title": "Müşteri Hizmetleri",
                "links": [
                    {"text": "SSS", "url": "/sss"},
                    {"text": "Kargo ve Teslimat", "url": "/kargo"},
                    {"text": "İptal ve İade", "url": "/iade"}
                ]
            }
        ],
        "bottom_text": "© {year} Tüm hakları saklıdır.",
        "payment_icons": ["visa", "mastercard", "amex"]
    },
    "social_links": {},
    "announcement_bar": {
        "enabled": False,
        "text": "🎉 Hoş geldiniz!",
        "link": "",
        "backgroundColor": "#000000",
        "textColor": "#FFFFFF",
        "position": "top"
    },
    "analytics_config": {
        "google_analytics": {"enabled": False, "tracking_id": ""},
        "facebook_pixel": {"enabled": False, "pixel_id": ""},
        "google_tag_manager": {"enabled": False, "container_id": ""}
    },
    "pwa_config": {
        "enabled": False,
        "app_name": "",
        "short_name": "",
        "theme_color": "#000000",
        "background_color": "#FFFFFF"
    }
}

# ==============================================
# TEMPLATE 2: CLASSIC E-COMMERCE
# ==============================================

TEMPLATE_CLASSIC_ECOMMERCE = {
    "name": "Classic E-Commerce",
    "description": "Çok amaçlı, klasik e-ticaret şablonu. Her sektör için uygun.",
    "theme_config": {
        "colors": {
            "primary": "#2563EB",
            "secondary": "#7C3AED",
            "accent": "#F59E0B",
            "background": "#FFFFFF",
            "backgroundAlt": "#F3F4F6",
            "text": "#1F2937",
            "textSecondary": "#6B7280",
            "border": "#D1D5DB",
            "success": "#059669",
            "warning": "#D97706",
            "error": "#DC2626",
        },
        "typography": {
            "fontFamily": "'Inter', 'Roboto', sans-serif",
            "headingFont": "'Poppins', 'Inter', sans-serif",
            "fontSize": {
                "xs": "0.75rem",
                "sm": "0.875rem",
                "base": "1rem",
                "lg": "1.125rem",
                "xl": "1.25rem",
                "2xl": "1.5rem",
                "3xl": "1.875rem",
                "4xl": "2.25rem",
                "5xl": "3rem"
            },
            "fontWeight": {
                "normal": "400",
                "medium": "500",
                "semibold": "600",
                "bold": "700",
                "extrabold": "800"
            }
        },
        "spacing": {
            "containerMaxWidth": "1280px",
            "sectionPadding": "4rem",
            "cardPadding": "1.5rem",
            "buttonPadding": "0.75rem 1.5rem"
        },
        "borderRadius": {
            "sm": "0.25rem",
            "md": "0.5rem",
            "lg": "0.75rem",
            "xl": "1rem",
            "full": "9999px"
        },
        "shadows": {
            "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
            "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
            "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
            "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1)",
            "2xl": "0 25px 50px -12px rgba(0, 0, 0, 0.25)"
        },
        "animation": {
            "duration": "0.2s",
            "easing": "ease-in-out"
        }
    },
    "homepage_config": {
        "sections": [
            {
                "id": "hero-slider",
                "type": "hero-slider",
                "slides": [
                    {
                        "title": "Yaz Kampanyası",
                        "subtitle": "Tüm ürünlerde %50'ye varan indirim",
                        "buttonText": "Hemen Keşfet",
                        "buttonLink": "/kampanyalar",
                        "image": "",
                        "overlay": True,
                        "overlayColor": "rgba(0, 0, 0, 0.3)"
                    },
                    {
                        "title": "Yeni Sezon Koleksiyonu",
                        "subtitle": "En trend ürünler stoklarımızda",
                        "buttonText": "İncele",
                        "buttonLink": "/yeni-urunler",
                        "image": "",
                        "overlay": True,
                        "overlayColor": "rgba(0, 0, 0, 0.3)"
                    }
                ],
                "autoplay": True,
                "interval": 5000,
                "showDots": True,
                "showArrows": True,
                "height": "600px"
            },
            {
                "id": "categories-featured",
                "type": "category-cards",
                "title": "Kategoriler",
                "displayType": "featured",
                "columns": 4,
                "showCount": True,
                "imageShape": "rounded",
                "style": "card-with-overlay"
            },
            {
                "id": "flash-deals",
                "type": "flash-deals",
                "title": "Bugünün Fırsatları",
                "subtitle": "Sınırlı süre için özel fiyatlar",
                "displayType": "discounted",
                "limit": 6,
                "columns": 3,
                "showCountdown": True,
                "backgroundColor": "#FEF3C7",
                "showBadge": True
            },
            {
                "id": "featured-products",
                "type": "product-grid",
                "title": "Öne Çıkan Ürünler",
                "description": "En çok tercih edilen ürünlerimiz",
                "displayType": "featured",
                "limit": 8,
                "columns": 4,
                "showQuickView": True,
                "showAddToCart": True,
                "showCompare": True,
                "showWishlist": True,
                "layout": "standard"
            },
            {
                "id": "brands-showcase",
                "type": "brands-grid",
                "title": "Markalarımız",
                "displayType": "all",
                "columns": 6,
                "grayscale": True,
                "hoverEffect": "color"
            },
            {
                "id": "features-trust",
                "type": "features-grid",
                "title": "Müşteri Memnuniyeti Önceliğimiz",
                "items": [
                    {
                        "icon": "truck",
                        "title": "Hızlı Kargo",
                        "description": "Aynı gün teslimat seçenekleri",
                        "color": "#2563EB"
                    },
                    {
                        "icon": "credit-card",
                        "title": "Güvenli Ödeme",
                        "description": "256-bit SSL şifreleme",
                        "color": "#059669"
                    },
                    {
                        "icon": "headphones",
                        "title": "Müşteri Desteği",
                        "description": "7/24 canlı destek hattı",
                        "color": "#7C3AED"
                    },
                    {
                        "icon": "shield",
                        "title": "Güvenli Alışveriş",
                        "description": "Alışveriş güvencesi",
                        "color": "#DC2626"
                    }
                ],
                "layout": "grid",
                "columns": 4,
                "backgroundColor": "#F9FAFB"
            },
            {
                "id": "testimonials",
                "type": "testimonials-carousel",
                "title": "Müşterilerimiz Ne Diyor?",
                "items": [
                    {
                        "text": "Harika bir alışveriş deneyimi! Ürünler kaliteli, kargo hızlı.",
                        "author": "Ayşe K.",
                        "rating": 5
                    },
                    {
                        "text": "Güvenilir bir firma, kesinlikle tavsiye ederim.",
                        "author": "Mehmet Y.",
                        "rating": 5
                    },
                    {
                        "text": "Fiyat/performans olarak çok iyi, teşekkürler!",
                        "author": "Zeynep A.",
                        "rating": 5
                    }
                ],
                "autoplay": True,
                "showDots": True
            },
            {
                "id": "newsletter-subscribe",
                "type": "newsletter-banner",
                "title": "Kampanyalardan Haberdar Olun",
                "description": "Özel fırsatlar ve yeni ürünlerden ilk siz haberdar olun",
                "placeholder": "E-posta adresiniz",
                "buttonText": "Abone Ol",
                "backgroundColor": "#2563EB",
                "textColor": "#FFFFFF",
                "layout": "centered"
            }
        ]
    },
    "navigation_menus": {
        "header": {
            "items": [
                {"label": "Ana Sayfa", "url": "/", "icon": "home"},
                {"label": "Ürünler", "url": "/urunler"},
                {"label": "İndirimler", "url": "/kampanyalar"},
                {"label": "Hakkımızda", "url": "/hakkimizda"},
                {"label": "İletişim", "url": "/iletisim"}
            ]
        }
    },
    "footer_config": {
        "columns": [
            {
                "title": "Hızlı Erişim",
                "links": [
                    {"text": "Ana Sayfa", "url": "/"},
                    {"text": "Ürünler", "url": "/urunler"},
                    {"text": "Kampanyalar", "url": "/kampanyalar"},
                    {"text": "Rehber", "url": "/blog"}
                ]
            },
            {
                "title": "Kurumsal",
                "links": [
                    {"text": "Hakkımızda", "url": "/hakkimizda"},
                    {"text": "İletişim", "url": "/iletisim"},
                    {"text": "Kariyere", "url": "/kariyer"}
                ]
            },
            {
                "title": "Yasal",
                "links": [
                    {"text": "Gizlilik Politikası", "url": "/gizlilik-politikasi"},
                    {"text": "Kullanım Koşulları", "url": "/kullanim-kosullari"},
                    {"text": "KVKK", "url": "/kvkk"}
                ]
            }
        ],
        "bottom_text": "© {year} Tüm hakları saklıdır. Güvenli Alışveriş.",
        "payment_icons": ["visa", "mastercard", "amex", "troy"]
    },
    "social_links": {},
    "announcement_bar": {
        "enabled": True,
        "text": "🔥 Sezon Sonu İndirimleri Başladı! Acele Edin.",
        "link": "/kampanyalar",
        "backgroundColor": "#1F2937",
        "textColor": "#FFFFFF",
        "position": "top"
    },
    "analytics_config": {
        "google_analytics": {"enabled": False, "tracking_id": ""},
        "facebook_pixel": {"enabled": False, "pixel_id": ""},
        "google_tag_manager": {"enabled": False, "container_id": ""}
    },
    "pwa_config": {
        "enabled": False,
        "app_name": "",
        "short_name": "",
        "theme_color": "#2563EB",
        "background_color": "#FFFFFF"
    }
}

# Default pages (her iki template için aynı)
DEFAULT_PAGES = [
    {
        "slug": "hakkimizda",
        "title": "Hakkımızda",
        "meta_title": "Hakkımızda - Biz Kimiz?",
        "meta_description": "Şirketimiz ve değerlerimiz hakkında bilgi edinin",
        "show_in_menu": True,
        "sort_order": 1,
        "is_active": True,
        "page_config": {
            "sections": [
                {
                    "id": "about-hero",
                    "type": "page-hero",
                    "title": "Hakkımızda",
                    "subtitle": "Kalite ve güven ile hizmetinizdeyiz"
                },
                {
                    "id": "our-story",
                    "type": "text-content",
                    "content": "<h2>Hikayemiz</h2><p>Yılların tecrübesi ile sektörde lider konumdayız. Müşteri memnuniyeti odaklı çalışma prensiplerimiz ve kaliteli ürün yelpazemiz ile sizlere hizmet vermekten mutluluk duyuyoruz.</p>"
                }
            ]
        }
    },
    {
        "slug": "iletisim",
        "title": "İletişim",
        "meta_title": "İletişim - Bize Ulaşın",
        "meta_description": "Sorularınız için bizimle iletişime geçin",
        "show_in_menu": True,
        "sort_order": 2,
        "is_active": True,
        "page_config": {
            "sections": [
                {
                    "id": "contact-hero",
                    "type": "page-hero",
                    "title": "İletişim",
                    "subtitle": "Size nasıl yardımcı olabiliriz?"
                },
                {
                    "id": "contact-form",
                    "type": "contact-form",
                    "fields": [
                        {"type": "text", "name": "name", "label": "Ad Soyad", "required": True},
                        {"type": "email", "name": "email", "label": "E-posta", "required": True},
                        {"type": "tel", "name": "phone", "label": "Telefon"},
                        {"type": "textarea", "name": "message", "label": "Mesajınız", "required": True, "rows": 5}
                    ],
                    "submitText": "Gönder"
                }
            ]
        }
    },
    {
        "slug": "gizlilik-politikasi",
        "title": "Gizlilik Politikası",
        "meta_title": "Gizlilik Politikası",
        "meta_description": "Kişisel verilerinizin korunması",
        "show_in_menu": False,
        "sort_order": 10,
        "is_active": True,
        "page_config": {
            "sections": [
                {
                    "id": "privacy",
                    "type": "legal-content",
                    "content": "<h1>Gizlilik Politikası</h1><p>Kişisel verileriniz 6698 sayılı KVKK kapsamında korunmaktadır.</p>"
                }
            ]
        }
    },
    {
        "slug": "kullanim-kosullari",
        "title": "Kullanım Koşulları",
        "meta_title": "Kullanım Koşulları",
        "meta_description": "Site kullanım şartları",
        "show_in_menu": False,
        "sort_order": 11,
        "is_active": True,
        "page_config": {
            "sections": [
                {
                    "id": "terms",
                    "type": "legal-content",
                    "content": "<h1>Kullanım Koşulları</h1><p>Sitemizi kullanarak bu şartları kabul etmiş sayılırsınız.</p>"
                }
            ]
        }
    }
]


# Template registry
AVAILABLE_TEMPLATES = {
    "modern-minimalist": TEMPLATE_MODERN_MINIMALIST,
    "classic-ecommerce": TEMPLATE_CLASSIC_ECOMMERCE,
}


def get_template_by_key(template_key="classic-ecommerce"):
    """
    Template key'e göre template data döndür
    
    Args:
        template_key: 'modern-minimalist' veya 'classic-ecommerce'
    
    Returns:
        Template data dict
    """
    return AVAILABLE_TEMPLATES.get(template_key, TEMPLATE_CLASSIC_ECOMMERCE)


def get_default_template_data(tenant, template_key="classic-ecommerce"):
    """
    Tenant için template data oluştur
    
    Args:
        tenant: Tenant instance
        template_key: Hangi template kullanılacak
    
    Returns:
        Template data dict
    """
    template = get_template_by_key(template_key)
    
    return {
        "tenant": tenant,
        "site_name": tenant.name,
        "homepage_config": template["homepage_config"],
        "theme_config": template["theme_config"],
        "meta_title": f"{tenant.name} - Online Alışveriş",
        "meta_description": f"{tenant.name} ile kaliteli ürünler, uygun fiyatlar ve hızlı teslimat.",
        "is_active": True
    }
