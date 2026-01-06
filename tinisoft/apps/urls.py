"""
URL configuration for Tinisoft apps.
"""
from django.urls import path
from apps.views.auth import register, login, tenant_detail
from apps.views.tenant_user import register_tenant_user, login_tenant_user, send_verification_code_tenant_user, verify_registration_tenant_user
from apps.views.domain import verify_domain, verify_domain_by_code, domain_status, list_domains, deploy_domain, retry_verification, create_domain
from apps.views.product import (
    product_list_create, product_detail,
    product_list_public, product_detail_public,
    category_list_create, category_list_public, category_detail,
    product_activate, product_deactivate,
    delete_all_products
)
from apps.views.product_brands import (
    brand_list_create, brand_detail, legacy_product_brands,
    brand_list_public, brand_detail_public
)
from apps.views.product_import import import_products_from_excel, excel_template_download, import_status, excel_columns_info
from apps.views.product_image_upload import (
    upload_product_image_by_slug,
    bulk_upload_product_images,
    upload_product_image_by_sku
)
from apps.views.product_image_delete import (
    delete_product_image,
    bulk_delete_product_images
)
from apps.views.product_image_from_excel import upload_images_from_excel_paths
from apps.views.order import order_list_create, order_detail, order_track
from apps.views.aras_cargo import aras_create_shipment, aras_track_shipment, aras_print_label, aras_cancel_shipment
from apps.views.aras_cargo import aras_create_shipment, aras_track_shipment, aras_print_label, aras_cancel_shipment
from apps.views.cart import (
    cart_detail, add_to_cart, cart_item_detail,
    update_shipping_method, apply_coupon
)
from apps.views.payment import (
    payment_list_create, payment_detail, payment_create_with_provider, payment_verify,
    kuveyt_callback_ok, kuveyt_callback_fail, payment_callback_handler
)
from apps.views.customer import customer_list, customer_detail, update_customer_statistics
from apps.views.inventory import inventory_movement_list_create, inventory_movement_detail
from apps.views.search import search_products, search_suggestions, filter_options
from apps.views.bulk import (
    bulk_update_products, bulk_delete_products,
    bulk_update_order_status, bulk_export_products
)
from apps.views.loyalty import loyalty_program, my_loyalty_points, loyalty_transactions
from apps.views.review import review_list, review_create, review_list_all, review_detail, review_helpful
from apps.views.wishlist import wishlist_list_create, wishlist_detail, wishlist_item_add_remove, wishlist_clear
from apps.views.compare import compare_list, compare_add_product, compare_remove_product, compare_clear, compare_products_detail
from apps.views.discount import (
    coupon_list_create, coupon_detail, coupon_validate, coupon_list_public,
    promotion_list_create, promotion_detail
)
from apps.views.gift_card import (
    gift_card_list_create, gift_card_detail, gift_card_validate,
    gift_card_balance, gift_card_transactions
)
from apps.views.shipping import (
    shipping_method_list_create, shipping_method_detail,
    shipping_address_list_create, shipping_address_detail,
    shipping_zone_list_create, shipping_zone_detail,
    shipping_zone_rate_list_create, shipping_zone_rate_detail,
    shipping_calculate
)
from apps.views.tax import (
    tax_list_create, tax_detail,
    tax_activate, tax_deactivate, tax_active
)
from apps.views.currency import (
    currency_list, currency_exchange_rates, currency_update_rates
)
from apps.views.bundle import (
    bundle_list_create, bundle_detail,
    bundle_item_add, bundle_item_detail
)
from apps.views.analytics import (
    analytics_event_create, analytics_events_list,
    analytics_dashboard, sales_reports_list, product_analytics_list
)
from apps.views.abandoned_cart import (
    abandoned_cart_list, abandoned_cart_detail,
    abandoned_cart_recover, abandoned_cart_send_reminder
)
from apps.views.webhook import (
    webhook_list_create, webhook_detail,
    webhook_test, webhook_events_list
)
from apps.views.inventory_alert import (
    inventory_alert_list_create, inventory_alert_detail,
    inventory_alert_check
)
from apps.views.integration import (
    integration_list_create, integration_detail,
    integration_test, integration_by_type
)
from apps.views.basket import basket, basket_item

app_name = 'apps'

urlpatterns = [
    # Owner kayıt/giriş (mağaza sahibi)
    path('auth/register/', register, name='register'),
    path('auth/login/', login, name='login'),
    
    # Tenant yönetimi
    path('tenant/', tenant_detail, name='tenant_detail'),  # GET: Tenant bilgilerini getir, PATCH: Güncelle
    
    # TenantUser kayıt/giriş (tenant'ın sitesinde müşteriler)
    path('tenant/<str:tenant_slug>/users/send-code/', send_verification_code_tenant_user, name='send_verification_code_tenant_user'),
    path('tenant/<str:tenant_slug>/users/register/', register_tenant_user, name='register_tenant_user'),
    path('tenant/<str:tenant_slug>/users/verify/', verify_registration_tenant_user, name='verify_registration_tenant_user'),
    path('tenant/<str:tenant_slug>/users/login/', login_tenant_user, name='login_tenant_user'),
    
    # Domain yönetimi
    path('domains/', list_domains, name='list_domains'),  # GET: List, POST: Create
    path('domains/verify-by-code/', verify_domain_by_code, name='verify_domain_by_code'),  # Public endpoint (verification_code ile)
    path('domains/<uuid:domain_id>/verify/', verify_domain, name='verify_domain'),  # Authenticated endpoint
    path('domains/<uuid:domain_id>/retry-verification/', retry_verification, name='retry_verification'),  # Retry verification
    path('domains/<uuid:domain_id>/deploy/', deploy_domain, name='deploy_domain'),  # Manual deployment
    path('domains/<uuid:domain_id>/status/', domain_status, name='domain_status'),
    
    # Ürün yönetimi
    path('products/', product_list_create, name='product_list_create'),  # GET: List, POST: Create
    path('brands/', brand_list_create, name='brand_list_create'),  # GET: List, POST: Create
    path('brands/<uuid:brand_id>/', brand_detail, name='brand_detail'),  # GET, PATCH, DELETE
    path('products/brands/legacy/', legacy_product_brands, name='legacy_product_brands'),  # Eski usül ürün markaları
    path('products/delete-all/', delete_all_products, name='delete_all_products'),  # DELETE: Tüm ürünleri sil
    path('products/<uuid:product_id>/', product_detail, name='product_detail'),  # GET, PUT, PATCH, DELETE
    path('products/<uuid:product_id>/activate/', product_activate, name='product_activate'),  # POST: Ürünü aktif yap
    path('products/<uuid:product_id>/deactivate/', product_deactivate, name='product_deactivate'),  # POST: Ürünü pasif yap
    path('products/import/', import_products_from_excel, name='import_products_from_excel'),  # POST: Excel'den ürün import (async/sync)
    path('products/import/columns/', excel_columns_info, name='excel_columns_info'),  # POST: Excel kolon isimlerini listele (debug)
    path('products/import/status/<str:task_id>/', import_status, name='import_status'),  # GET: Import durumu kontrol
    path('products/import/template/', excel_template_download, name='excel_template_download'),  # GET: Excel template indir
    path('products/images/upload/', upload_product_image_by_slug, name='upload_product_image_by_slug'),  # POST: Slug ile görsel yükle
    path('products/images/bulk-upload/', bulk_upload_product_images, name='bulk_upload_product_images'),  # POST: Toplu görsel yükle
    path('products/images/upload-by-sku/', upload_product_image_by_sku, name='upload_product_image_by_sku'),  # POST: SKU ile görsel yükle
    path('products/images/upload-from-excel/', upload_images_from_excel_paths, name='upload_images_from_excel_paths'),  # POST: Excel'den resim yollarını yükle
    path('products/<uuid:product_id>/images/<uuid:image_id>/', delete_product_image, name='delete_product_image'),  # DELETE: Tek görsel sil
    path('products/<uuid:product_id>/images/bulk-delete/', bulk_delete_product_images, name='bulk_delete_product_images'),  # DELETE: Toplu görsel sil
    # Public product endpoints (tenant_slug ile)
    path('public/products/', product_list_public, name='product_list_public'),  # GET: ?tenant_slug=xxx veya header ile
    path('public/<str:tenant_slug>/products/', product_list_public, name='product_list_public_by_slug'),  # GET: Path parameter ile
    # Ürün detayı - yeni format (urun ile)
    path('public/products/urun/<str:urun_slug>/', product_detail_public, name='product_detail_public'),  # GET: ?tenant_slug=xxx veya header ile
    path('public/<str:tenant_slug>/products/urun/<str:urun_slug>/', product_detail_public, name='product_detail_public_by_slug'),  # GET: Path parameter ile
    # Ürün detayı - eski format (geriye dönük uyumluluk)
    path('public/products/<str:product_slug>/', product_detail_public, name='product_detail_public_old'),  # GET: ?tenant_slug=xxx veya header ile (eski format)
    path('public/<str:tenant_slug>/products/<str:product_slug>/', product_detail_public, name='product_detail_public_old_by_slug'),  # GET: Path parameter ile (eski format)
    path('categories/', category_list_create, name='category_list_create'),  # GET: List, POST: Create
    path('categories/<uuid:category_id>/', category_detail, name='category_detail'),  # GET, PATCH, DELETE
    # Public category endpoints
    path('public/categories/', category_list_public, name='category_list_public'),  # GET: ?tenant_slug=xxx veya header ile
    path('public/<str:tenant_slug>/categories/', category_list_public, name='category_list_public_by_slug'),  # GET: Path parameter ile
    # Public brand endpoints
    path('public/brands/', brand_list_public, name='brand_list_public'),
    path('public/<str:tenant_slug>/brands/', brand_list_public, name='brand_list_public_by_slug'),
    path('public/brands/<str:brand_slug>/', brand_detail_public, name='brand_detail_public'),
    path('public/<str:tenant_slug>/brands/<str:brand_slug>/', brand_detail_public, name='brand_detail_public_by_slug'),
    
    # Sipariş yönetimi
    path('orders/', order_list_create, name='order_list_create'),  # GET: List, POST: Create
    path('orders/<uuid:order_id>/', order_detail, name='order_detail'),  # GET, PATCH
    path('orders/<uuid:order_id>/aras/create-shipment/', aras_create_shipment, name='aras_create_shipment'),  # POST: Aras Kargo gönderi oluştur
    path('orders/track/<str:order_number>/', order_track, name='order_track'),  # GET: Track order by order number
    
    # Aras Kargo API
    path('aras/track/<str:tracking_number>/', aras_track_shipment, name='aras_track_shipment'),  # GET: Gönderi takip
    path('aras/label/<str:tracking_number>/', aras_print_label, name='aras_print_label'),  # GET: Etiket yazdır
    path('aras/cancel/<str:tracking_number>/', aras_cancel_shipment, name='aras_cancel_shipment'),  # POST: Gönderi iptal
    
    # Sepet yönetimi (Basket - Basit CRUD)
    path('basket/', basket, name='basket'),  # GET: Sepeti getir, POST: Sepete ürün ekle
    path('basket/<uuid:item_id>/', basket_item, name='basket_item'),  # PATCH: Güncelle, DELETE: Sil
    
    # Cart endpoint'leri
    path('cart/', cart_detail, name='cart_detail'),
    path('cart/add/', add_to_cart, name='add_to_cart'),
    path('cart/items/<uuid:item_id>/', cart_item_detail, name='cart_item_detail'),
    path('cart/shipping/', update_shipping_method, name='update_shipping_method'),
    path('cart/coupon/', apply_coupon, name='apply_coupon'),
    
    # Ödeme yönetimi
    path('payments/', payment_list_create, name='payment_list_create'),  # GET: List, POST: Create
    path('payments/<uuid:payment_id>/', payment_detail, name='payment_detail'),  # GET, PATCH
    path('payments/create/', payment_create_with_provider, name='payment_create_with_provider'),  # POST: Create payment with provider (Kuveyt API)
    path('payments/verify/', payment_verify, name='payment_verify'),  # POST: Verify payment (callback)
    path('payments/verify', payment_verify, name='payment_verify_no_slash'),  # POST: Verify payment (no trailing slash)
    # Kuveyt 3D Secure callback endpoints
    path('payments/kuveyt/callback/ok/', kuveyt_callback_ok, name='kuveyt_callback_ok'),  # POST: Kuveyt OkUrl callback
    path('payments/kuveyt/callback/ok', kuveyt_callback_ok, name='kuveyt_callback_ok_no_slash'),  # POST: Kuveyt OkUrl callback (no trailing slash)
    path('payments/kuveyt/callback/fail/', kuveyt_callback_fail, name='kuveyt_callback_fail'),  # POST: Kuveyt FailUrl callback
    path('payments/kuveyt/callback/fail', kuveyt_callback_fail, name='kuveyt_callback_fail_no_slash'),  # POST: Kuveyt FailUrl callback (no trailing slash)
    # Payment callback handler (frontend için)
    path('payments/callback-handler/', payment_callback_handler, name='payment_callback_handler'),  # GET: Payment callback handler (frontend redirect için)
    path('payments/callback-handler', payment_callback_handler, name='payment_callback_handler_no_slash'),  # GET: Payment callback handler (no trailing slash)
    
    # Müşteri yönetimi
    path('customers/', customer_list, name='customer_list'),  # GET: List
    path('customers/<uuid:customer_id>/', customer_detail, name='customer_detail'),  # GET, PATCH
    path('customers/<uuid:customer_id>/update-statistics/', update_customer_statistics, name='update_customer_statistics'),  # POST
    
    # Stok yönetimi
    path('inventory/movements/', inventory_movement_list_create, name='inventory_movement_list_create'),  # GET: List, POST: Create
    path('inventory/movements/<uuid:movement_id>/', inventory_movement_detail, name='inventory_movement_detail'),  # GET
    
    # Arama ve filtreleme
    path('search/products/', search_products, name='search_products'),  # GET: Search products
    path('search/suggestions/', search_suggestions, name='search_suggestions'),  # GET: Search suggestions
    path('search/filter-options/', filter_options, name='filter_options'),  # GET: Filter options
    
    # Toplu işlemler
    path('bulk/products/update/', bulk_update_products, name='bulk_update_products'),  # POST: Bulk update products
    path('bulk/products/delete/', bulk_delete_products, name='bulk_delete_products'),  # POST: Bulk delete products
    path('bulk/products/export/', bulk_export_products, name='bulk_export_products'),  # POST: Bulk export products
    path('bulk/orders/update-status/', bulk_update_order_status, name='bulk_update_order_status'),  # POST: Bulk update order status
    
    # Sadakat puanları
    path('loyalty/program/', loyalty_program, name='loyalty_program'),  # GET: Get, POST: Create, PATCH: Update (aktif/deaktif)
    path('loyalty/my-points/', my_loyalty_points, name='my_loyalty_points'),  # GET: Müşteri kendi puanlarını görüntüle
    path('loyalty/transactions/', loyalty_transactions, name='loyalty_transactions'),  # GET: İşlem geçmişi
    
    # Ürün yorumları
    path('reviews/', review_list_all, name='review_list_all'),  # GET: Tüm yorumları listele (Tenant Owner)
    path('products/<uuid:product_id>/reviews/', review_list, name='review_list'),  # GET: List (public, product bazlı)
    path('products/<uuid:product_id>/reviews/create/', review_create, name='review_create'),  # POST: Create (authenticated, purchase required)
    path('reviews/<uuid:review_id>/', review_detail, name='review_detail'),  # GET, PATCH, DELETE
    path('reviews/<uuid:review_id>/helpful/', review_helpful, name='review_helpful'),  # POST: Like/Dislike
    
    # İstek listesi (Wishlist)
    path('wishlists/', wishlist_list_create, name='wishlist_list_create'),  # GET: List, POST: Create
    path('wishlists/<uuid:wishlist_id>/', wishlist_detail, name='wishlist_detail'),  # GET, PATCH, DELETE
    path('wishlists/<uuid:wishlist_id>/items/', wishlist_item_add_remove, name='wishlist_item_add_remove'),  # POST: Add, DELETE: Remove
    path('wishlists/<uuid:wishlist_id>/clear/', wishlist_clear, name='wishlist_clear'),  # DELETE: Clear all items
    
    # Ürün Karşılaştırma (Compare)
    path('compare/', compare_list, name='compare_list'),  # GET: Karşılaştırma listesini getir
    path('compare/add/', compare_add_product, name='compare_add_product'),  # POST: Ürün ekle
    path('compare/remove/<uuid:product_id>/', compare_remove_product, name='compare_remove_product'),  # DELETE: Ürün çıkar
    path('compare/clear/', compare_clear, name='compare_clear'),  # DELETE: Listeyi temizle
    path('compare/products/', compare_products_detail, name='compare_products_detail'),  # GET: Ürün detaylarını getir
    
    # İndirim ve Kuponlar
    path('coupons/', coupon_list_create, name='coupon_list_create'),  # GET: List, POST: Create
    path('coupons/<uuid:coupon_id>/', coupon_detail, name='coupon_detail'),  # GET, PATCH, DELETE
    path('coupons/validate/', coupon_validate, name='coupon_validate'),  # POST: Validate coupon
    path('public/coupons/', coupon_list_public, name='coupon_list_public'),  # GET: Public coupon list
    
    # Promosyonlar
    path('promotions/', promotion_list_create, name='promotion_list_create'),  # GET: List, POST: Create
    path('promotions/<uuid:promotion_id>/', promotion_detail, name='promotion_detail'),  # GET, PATCH, DELETE
    
    # Hediye Kartları
    path('gift-cards/', gift_card_list_create, name='gift_card_list_create'),  # GET: List, POST: Create
    path('gift-cards/<uuid:gift_card_id>/', gift_card_detail, name='gift_card_detail'),  # GET, PATCH, DELETE
    path('gift-cards/validate/', gift_card_validate, name='gift_card_validate'),  # POST: Validate gift card
    path('gift-cards/<uuid:gift_card_id>/balance/', gift_card_balance, name='gift_card_balance'),  # GET: Check balance
    path('gift-cards/<uuid:gift_card_id>/transactions/', gift_card_transactions, name='gift_card_transactions'),  # GET: Transaction history
    
    # Kargo Yönetimi
    path('shipping/methods/', shipping_method_list_create, name='shipping_method_list_create'),  # GET: List, POST: Create
    path('shipping/methods/<uuid:method_id>/', shipping_method_detail, name='shipping_method_detail'),  # GET, PATCH, DELETE
    path('shipping/addresses/', shipping_address_list_create, name='shipping_address_list_create'),  # GET: List, POST: Create
    path('shipping/addresses/<uuid:address_id>/', shipping_address_detail, name='shipping_address_detail'),  # GET, PATCH, DELETE
    path('shipping/zones/', shipping_zone_list_create, name='shipping_zone_list_create'),  # GET: List, POST: Create
    path('shipping/zones/<uuid:zone_id>/', shipping_zone_detail, name='shipping_zone_detail'),  # GET, PATCH, DELETE
    path('shipping/zones/<uuid:zone_id>/rates/', shipping_zone_rate_list_create, name='shipping_zone_rate_list_create'),  # GET: List, POST: Create
    path('shipping/zones/<uuid:zone_id>/rates/<uuid:rate_id>/', shipping_zone_rate_detail, name='shipping_zone_rate_detail'),  # GET, PATCH, DELETE
    path('shipping/calculate/', shipping_calculate, name='shipping_calculate'),  # POST: Calculate shipping cost
    
    # Bundle (Ürün Paketleri)
    path('bundles/', bundle_list_create, name='bundle_list_create'),  # GET: List, POST: Create
    path('bundles/<uuid:bundle_id>/', bundle_detail, name='bundle_detail'),  # GET, PATCH, DELETE
    path('bundles/<uuid:bundle_id>/items/', bundle_item_add, name='bundle_item_add'),  # POST: Add item
    path('bundles/<uuid:bundle_id>/items/<uuid:item_id>/', bundle_item_detail, name='bundle_item_detail'),  # PATCH, DELETE
    
    # Analytics
    path('analytics/events/', analytics_event_create, name='analytics_event_create'),  # POST: Create event (public)
    path('analytics/events/list/', analytics_events_list, name='analytics_events_list'),  # GET: List events
    path('analytics/dashboard/', analytics_dashboard, name='analytics_dashboard'),  # GET: Dashboard data
    path('analytics/reports/', sales_reports_list, name='sales_reports_list'),  # GET: Sales reports
    path('analytics/products/', product_analytics_list, name='product_analytics_list'),  # GET: Product analytics
    
    # Abandoned Cart
    path('abandoned-carts/', abandoned_cart_list, name='abandoned_cart_list'),  # GET: List
    path('abandoned-carts/<uuid:abandoned_cart_id>/', abandoned_cart_detail, name='abandoned_cart_detail'),  # GET, PATCH
    path('abandoned-carts/<uuid:abandoned_cart_id>/recover/', abandoned_cart_recover, name='abandoned_cart_recover'),  # POST: Recover
    path('abandoned-carts/<uuid:abandoned_cart_id>/send-reminder/', abandoned_cart_send_reminder, name='abandoned_cart_send_reminder'),  # POST: Send reminder
    
    # Webhook
    path('webhooks/', webhook_list_create, name='webhook_list_create'),  # GET: List, POST: Create
    path('webhooks/<uuid:webhook_id>/', webhook_detail, name='webhook_detail'),  # GET, PATCH, DELETE
    path('webhooks/<uuid:webhook_id>/test/', webhook_test, name='webhook_test'),  # POST: Test webhook
    path('webhooks/<uuid:webhook_id>/events/', webhook_events_list, name='webhook_events_list'),  # GET: Event history
    
    # Inventory Alert
    path('inventory/alerts/', inventory_alert_list_create, name='inventory_alert_list_create'),  # GET: List, POST: Create
    path('inventory/alerts/<uuid:alert_id>/', inventory_alert_detail, name='inventory_alert_detail'),  # GET, PATCH, DELETE
    path('inventory/alerts/<uuid:alert_id>/check/', inventory_alert_check, name='inventory_alert_check'),  # POST: Check and notify
    
    # Integration API Keys
    path('integrations/', integration_list_create, name='integration_list_create'),  # GET: List, POST: Create
    path('integrations/<uuid:integration_id>/', integration_detail, name='integration_detail'),  # GET, PATCH, DELETE
    path('integrations/<uuid:integration_id>/test/', integration_test, name='integration_test'),  # POST: Test integration
    path('integrations/type/<str:provider_type>/', integration_by_type, name='integration_by_type'),  # GET: Get active integration by type
    
    # KDV/Vergi Yönetimi
    path('taxes/', tax_list_create, name='tax_list_create'),  # GET: List, POST: Create
    path('taxes/active/', tax_active, name='tax_active'),  # GET: Aktif vergiyi getir
    path('taxes/<uuid:tax_id>/', tax_detail, name='tax_detail'),  # GET, PUT, PATCH, DELETE
    path('taxes/<uuid:tax_id>/activate/', tax_activate, name='tax_activate'),  # POST: Vergiyi aktif et
    path('taxes/<uuid:tax_id>/deactivate/', tax_deactivate, name='tax_deactivate'),  # POST: Vergiyi pasif et
    
    # Para Birimi Yönetimi
    path('public/currencies/', currency_list, name='currency_list'),  # GET: Aktif para birimlerini listele (public)
    path('public/currency/exchange-rates/', currency_exchange_rates, name='currency_exchange_rates'),  # GET: TCMB kurları (public)
    path('currency/update-rates/', currency_update_rates, name='currency_update_rates'),  # POST: Tenant para birimi kurlarını güncelle
]

