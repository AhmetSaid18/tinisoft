"""
Comprehensive API Test Script
Tenant olarak kayıt olup tüm endpoint'leri test eder.
"""
import requests
import json
import time
from typing import Dict, Optional

# Base URL - Docker container içinden veya localhost
# Docker compose'da backend port 5000'e map edilmiş: 127.0.0.1:5000:8000
BASE_URL = "http://127.0.0.1:5000/api"  # Host'tan erişim
# BASE_URL = "http://backend:8000/api"  # Docker network içinden (container'dan)

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.tenant_slug: Optional[str] = None
        self.tenant_user_token: Optional[str] = None
        self.created_resources: Dict = {
            'products': [],
            'categories': [],
            'orders': [],
            'carts': [],
            'reviews': [],
            'wishlists': [],
            'coupons': [],
            'promotions': [],
            'gift_cards': [],
            'shipping_methods': [],
            'shipping_addresses': [],
            'bundles': [],
            'abandoned_carts': [],
            'webhooks': [],
            'inventory_alerts': [],
        }
    
    def log(self, message: str, status: str = "INFO"):
        """Log mesajı yazdır."""
        status_icons = {
            "INFO": "[INFO]",
            "SUCCESS": "[OK]",
            "ERROR": "[ERROR]",
            "WARNING": "[WARN]"
        }
        icon = status_icons.get(status, "[INFO]")
        print(f"{icon} {message}")
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     headers: Optional[Dict] = None, expected_status: int = 200) -> Optional[Dict]:
        """HTTP request yap ve sonucu döndür."""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == 'POST':
                headers['Content-Type'] = 'application/json'
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PATCH':
                headers['Content-Type'] = 'application/json'
                response = requests.patch(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                headers['Content-Type'] = 'application/json'
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                self.log(f"Unsupported method: {method}", "ERROR")
                return None
            
            if response.status_code == expected_status:
                self.log(f"{method} {endpoint} - Status: {response.status_code}", "SUCCESS")
                try:
                    return response.json()
                except:
                    return {"status": response.status_code, "text": response.text}
            else:
                self.log(f"{method} {endpoint} - Expected {expected_status}, got {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"Error: {json.dumps(error_data, indent=2)}", "ERROR")
                except:
                    self.log(f"Error: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"Request error: {str(e)}", "ERROR")
            return None
    
    def test_register(self):
        """1. Tenant Owner kaydı."""
        self.log("\n=== 1. TENANT OWNER KAYDI ===", "INFO")
        
        timestamp = int(time.time())
        data = {
            "email": f"test_owner_{timestamp}@test.com",
            "password": "Test123456!",
            "first_name": "Test",
            "last_name": "Owner",
            "phone": "+905551234567",
            "store_name": f"Test Store {timestamp}",
            "store_slug": f"test-store-{timestamp}",
            "custom_domain": "",  # Subdomain kullan
        }
        
        result = self.make_request('POST', '/auth/register/', data, expected_status=201)
        if result and result.get('success'):
            # Register token döndürmüyor, login yapmamız gerekiyor
            tenant_data = result.get('tenant', {})
            self.tenant_slug = tenant_data.get('slug')
            self.log(f"Tenant oluşturuldu: {self.tenant_slug}", "SUCCESS")
            
            # Hemen login yap
            login_result = self.test_login(data['email'], data['password'])
            if login_result:
                return True
            return False
        return False
    
    def test_login(self, email: str, password: str):
        """2. Login."""
        self.log("\n=== 2. LOGIN ===", "INFO")
        
        data = {
            "email": email,
            "password": password
        }
        
        result = self.make_request('POST', '/auth/login/', data, expected_status=200)
        if result and result.get('success'):
            # Token response'ta farklı yerde olabilir
            self.token = result.get('token') or result.get('data', {}).get('token')
            if self.token:
                self.log(f"Login başarılı. Token: {self.token[:20]}...", "SUCCESS")
            else:
                self.log("Login başarılı ama token bulunamadı", "WARNING")
                self.log(f"Response: {json.dumps(result, indent=2)}", "INFO")
            return result
        return None
    
    def test_create_category(self):
        """3. Kategori oluştur."""
        self.log("\n=== 3. KATEGORİ OLUŞTUR ===", "INFO")
        
        data = {
            "name": "Test Kategori",
            "slug": "test-kategori",
            "description": "Test kategori açıklaması",
            "is_active": True
        }
        
        result = self.make_request('POST', '/categories/', data, expected_status=201)
        if result and result.get('success'):
            category = result.get('category', {})
            category_id = category.get('id')
            if category_id:
                self.created_resources['categories'].append(category_id)
            self.log(f"Kategori oluşturuldu: {category.get('name')}", "SUCCESS")
            return category
        return None
    
    def test_create_product(self):
        """4. Ürün oluştur."""
        self.log("\n=== 4. ÜRÜN OLUŞTUR ===", "INFO")
        
        data = {
            "name": "Test Ürün",
            "slug": "test-urun",
            "description": "Test ürün açıklaması",
            "price": "100.00",
            "compare_at_price": "120.00",
            "sku": "TEST-001",
            "track_inventory": True,
            "inventory_quantity": 50,
            "is_variant_product": False,
            "status": "active",
            "is_visible": True,
            "category_ids": self.created_resources['categories'][:1] if self.created_resources['categories'] else []
        }
        
        result = self.make_request('POST', '/products/', data, expected_status=201)
        if result and result.get('success'):
            product = result.get('product', {})
            product_id = product.get('id')
            if product_id:
                self.created_resources['products'].append(product_id)
            self.log(f"Ürün oluşturuldu: {product.get('name')}", "SUCCESS")
            return product
        return None
    
    def test_get_products(self):
        """5. Ürünleri listele."""
        self.log("\n=== 5. ÜRÜNLERİ LİSTELE ===", "INFO")
        
        result = self.make_request('GET', '/products/', expected_status=200)
        if result:
            products = result.get('products', [])
            self.log(f"{len(products)} ürün bulundu", "SUCCESS")
            return products
        return None
    
    def test_get_product_detail(self):
        """6. Ürün detayı."""
        self.log("\n=== 6. ÜRÜN DETAYI ===", "INFO")
        
        if not self.created_resources['products']:
            self.log("Ürün yok, atlanıyor", "WARNING")
            return None
        
        product_id = self.created_resources['products'][0]
        result = self.make_request('GET', f'/products/{product_id}/', expected_status=200)
        if result and result.get('success'):
            self.log("Ürün detayı alındı", "SUCCESS")
            return result.get('product')
        return None
    
    def test_register_tenant_user(self):
        """7. Tenant User kaydı."""
        self.log("\n=== 7. TENANT USER KAYDI ===", "INFO")
        
        if not self.tenant_slug:
            self.log("Tenant slug yok, atlanıyor", "WARNING")
            return None
        
        timestamp = int(time.time())
        data = {
            "email": f"test_customer_{timestamp}@test.com",
            "password": "Test123456!",
            "first_name": "Test",
            "last_name": "Customer",
            "phone": "+905559876543"
        }
        
        result = self.make_request('POST', f'/tenant/{self.tenant_slug}/users/register/', 
                                 data, expected_status=201)
        if result and result.get('success'):
            self.log("Tenant user kaydı başarılı", "SUCCESS")
            return result
        return None
    
    def test_login_tenant_user(self, email: str, password: str):
        """8. Tenant User login."""
        self.log("\n=== 8. TENANT USER LOGIN ===", "INFO")
        
        if not self.tenant_slug:
            self.log("Tenant slug yok, atlanıyor", "WARNING")
            return None
        
        data = {
            "email": email,
            "password": password
        }
        
        result = self.make_request('POST', f'/tenant/{self.tenant_slug}/users/login/', 
                                 data, expected_status=200)
        if result and result.get('success'):
            self.tenant_user_token = result.get('token')
            self.log(f"Tenant user login başarılı. Token: {self.tenant_user_token[:20] if self.tenant_user_token else 'None'}...", "SUCCESS")
            return result
        return None
    
    def test_create_cart(self):
        """9. Sepet oluştur (public endpoint - token gerekmez)."""
        self.log("\n=== 9. SEPET OLUŞTUR ===", "INFO")
        
        # Public endpoint, token gerekmez ama session gerekebilir
        result = self.make_request('POST', '/cart/', {}, headers={}, expected_status=201)
        if result and result.get('success'):
            cart = result.get('cart', {})
            cart_id = cart.get('id')
            if cart_id:
                self.created_resources['carts'].append(cart_id)
            self.log("Sepet oluşturuldu", "SUCCESS")
            return cart
        return None
    
    def test_add_to_cart(self):
        """10. Sepete ürün ekle."""
        self.log("\n=== 10. SEPETE ÜRÜN EKLE ===", "INFO")
        
        if not self.created_resources['products']:
            self.log("Ürün yok, atlanıyor", "WARNING")
            return None
        
        product_id = self.created_resources['products'][0]
        data = {
            "product_id": product_id,
            "quantity": 2
        }
        
        result = self.make_request('POST', '/cart/add/', data, expected_status=200)
        if result and result.get('success'):
            self.log("Ürün sepete eklendi", "SUCCESS")
            return result.get('cart')
        return None
    
    def test_get_cart(self):
        """11. Sepeti getir."""
        self.log("\n=== 11. SEPETİ GETİR ===", "INFO")
        
        result = self.make_request('GET', '/cart/', expected_status=200)
        if result and result.get('success'):
            cart = result.get('cart', {})
            items_count = len(cart.get('items', []))
            self.log(f"Sepet alındı. {items_count} kalem var", "SUCCESS")
            return cart
        return None
    
    def test_search_products(self):
        """12. Ürün ara."""
        self.log("\n=== 12. ÜRÜN ARA ===", "INFO")
        
        params = {
            "q": "test",
            "ordering": "newest"
        }
        
        result = self.make_request('GET', '/search/products/', params, expected_status=200)
        if result and result.get('success'):
            products = result.get('products', [])
            self.log(f"Arama sonucu: {len(products)} ürün", "SUCCESS")
            return products
        return None
    
    def test_public_product_list(self):
        """13. Public ürün listesi."""
        self.log("\n=== 13. PUBLIC ÜRÜN LİSTESİ ===", "INFO")
        
        result = self.make_request('GET', '/public/products/', {}, headers={}, expected_status=200)
        if result and result.get('success'):
            products = result.get('products', [])
            self.log(f"Public ürün listesi: {len(products)} ürün", "SUCCESS")
            return products
        return None
    
    def test_loyalty_program(self):
        """14. Sadakat programı."""
        self.log("\n=== 14. SADAKAT PROGRAMI ===", "INFO")
        
        # Program bilgilerini getir
        result = self.make_request('GET', '/loyalty/program/', expected_status=200)
        if result and result.get('success'):
            self.log("Sadakat programı bilgisi alındı", "SUCCESS")
            
            # Programı güncelle (aktif/deaktif)
            update_data = {
                "is_active": True,
                "points_per_currency": 1.0,
                "currency_per_point": 0.01
            }
            update_result = self.make_request('PATCH', '/loyalty/program/', update_data, expected_status=200)
            if update_result and update_result.get('success'):
                self.log("Sadakat programı güncellendi", "SUCCESS")
            
            return result.get('program')
        return None
    
    def test_create_review(self):
        """15. Ürün yorumu oluştur."""
        self.log("\n=== 15. ÜRÜN YORUMU OLUŞTUR ===", "INFO")
        
        if not self.created_resources['products']:
            self.log("Ürün yok, atlanıyor", "WARNING")
            return None
        
        product_id = self.created_resources['products'][0]
        data = {
            "customer_name": "Test Müşteri",
            "customer_email": "test@example.com",
            "rating": 5,
            "title": "Harika ürün!",
            "comment": "Çok beğendim, kesinlikle tavsiye ederim.",
            "images": []
        }
        
        result = self.make_request('POST', f'/products/{product_id}/reviews/', data, expected_status=201)
        if result and result.get('success'):
            review = result.get('review', {})
            review_id = review.get('id')
            if review_id:
                self.created_resources['reviews'].append(review_id)
            self.log("Yorum oluşturuldu", "SUCCESS")
            return review
        return None
    
    def test_get_reviews(self):
        """16. Ürün yorumlarını listele."""
        self.log("\n=== 16. ÜRÜN YORUMLARI ===", "INFO")
        
        if not self.created_resources['products']:
            self.log("Ürün yok, atlanıyor", "WARNING")
            return None
        
        product_id = self.created_resources['products'][0]
        result = self.make_request('GET', f'/products/{product_id}/reviews/', expected_status=200)
        if result and result.get('success'):
            reviews = result.get('reviews', [])
            self.log(f"{len(reviews)} yorum bulundu", "SUCCESS")
            return reviews
        return None
    
    def test_create_wishlist(self):
        """17. Wishlist oluştur."""
        self.log("\n=== 17. WISHLIST OLUŞTUR ===", "INFO")
        
        # Tenant user token kullan
        old_token = self.token
        if self.tenant_user_token:
            self.token = self.tenant_user_token
        
        data = {
            "name": "Favorilerim",
            "is_default": True,
            "is_public": False
        }
        
        result = self.make_request('POST', '/wishlists/', data, expected_status=201)
        if self.tenant_user_token:
            self.token = old_token
        
        if result and result.get('success'):
            wishlist = result.get('wishlist', {})
            wishlist_id = wishlist.get('id')
            if wishlist_id:
                self.created_resources['wishlists'].append(wishlist_id)
            self.log("Wishlist oluşturuldu", "SUCCESS")
            return wishlist
        return None
    
    def test_add_to_wishlist(self):
        """18. Wishlist'e ürün ekle."""
        self.log("\n=== 18. WISHLIST'E ÜRÜN EKLE ===", "INFO")
        
        if not self.created_resources['wishlists'] or not self.created_resources['products']:
            self.log("Wishlist veya ürün yok, atlanıyor", "WARNING")
            return None
        
        wishlist_id = self.created_resources['wishlists'][0]
        product_id = self.created_resources['products'][0]
        
        # Tenant user token kullan
        old_token = self.token
        if self.tenant_user_token:
            self.token = self.tenant_user_token
        
        data = {
            "product_id": product_id,
            "note": "Bu ürünü beğendim"
        }
        
        result = self.make_request('POST', f'/wishlists/{wishlist_id}/items/', data, expected_status=201)
        if self.tenant_user_token:
            self.token = old_token
        
        if result and result.get('success'):
            self.log("Ürün wishlist'e eklendi", "SUCCESS")
            return result.get('item')
        return None
    
    def test_create_coupon(self):
        """19. Kupon oluştur."""
        self.log("\n=== 19. KUPON OLUŞTUR ===", "INFO")
        
        timestamp = int(time.time())
        data = {
            "code": f"TEST{timestamp}",
            "name": "Test Kuponu",
            "description": "Test kuponu açıklaması",
            "discount_type": "percentage",
            "discount_value": "10.00",
            "minimum_order_amount": "50.00",
            "usage_limit": 100,
            "is_active": True
        }
        
        result = self.make_request('POST', '/coupons/', data, expected_status=201)
        if result and result.get('success'):
            coupon = result.get('coupon', {})
            coupon_id = coupon.get('id')
            if coupon_id:
                self.created_resources['coupons'].append(coupon_id)
            self.log(f"Kupon oluşturuldu: {coupon.get('code')}", "SUCCESS")
            return coupon
        return None
    
    def test_validate_coupon(self):
        """20. Kupon doğrula."""
        self.log("\n=== 20. KUPON DOĞRULA ===", "INFO")
        
        if not self.created_resources['coupons']:
            self.log("Kupon yok, atlanıyor", "WARNING")
            return None
        
        # Kupon kodunu almak için önce detayını getir
        coupon_id = self.created_resources['coupons'][0]
        coupon_detail = self.make_request('GET', f'/coupons/{coupon_id}/', expected_status=200)
        
        if coupon_detail and coupon_detail.get('success'):
            coupon_code = coupon_detail.get('coupon', {}).get('code')
            
            data = {
                "code": coupon_code,
                "order_amount": "100.00",
                "customer_email": "test@example.com"
            }
            
            result = self.make_request('POST', '/coupons/validate/', data, expected_status=200, headers={})
            if result and result.get('success'):
                discount = result.get('discount', {})
                self.log(f"Kupon geçerli. İndirim: {discount.get('discount_amount')} TL", "SUCCESS")
                return result
        return None
    
    def test_create_gift_card(self):
        """21. Gift card oluştur."""
        self.log("\n=== 21. GIFT CARD OLUŞTUR ===", "INFO")
        
        data = {
            "type": "fixed",
            "initial_amount": "100.00",
            "customer_email": "test@example.com",
            "note": "Test gift card"
        }
        
        result = self.make_request('POST', '/gift-cards/', data, expected_status=201)
        if result and result.get('success'):
            gift_card = result.get('gift_card', {})
            gift_card_id = gift_card.get('id')
            if gift_card_id:
                self.created_resources['gift_cards'].append(gift_card_id)
            self.log(f"Gift card oluşturuldu: {gift_card.get('code')}", "SUCCESS")
            return gift_card
        return None
    
    def test_validate_gift_card(self):
        """22. Gift card doğrula."""
        self.log("\n=== 22. GIFT CARD DOĞRULA ===", "INFO")
        
        if not self.created_resources['gift_cards']:
            self.log("Gift card yok, atlanıyor", "WARNING")
            return None
        
        # Gift card kodunu almak için önce detayını getir
        gift_card_id = self.created_resources['gift_cards'][0]
        gift_card_detail = self.make_request('GET', f'/gift-cards/{gift_card_id}/', expected_status=200)
        
        if gift_card_detail and gift_card_detail.get('success'):
            gift_card_code = gift_card_detail.get('gift_card', {}).get('code')
            
            data = {
                "code": gift_card_code,
                "order_amount": "50.00"
            }
            
            result = self.make_request('POST', '/gift-cards/validate/', data, expected_status=200, headers={})
            if result and result.get('success'):
                discount = result.get('discount', {})
                self.log(f"Gift card geçerli. İndirim: {discount.get('discount_amount')} TL", "SUCCESS")
                return result
        return None
    
    def test_create_shipping_method(self):
        """23. Kargo yöntemi oluştur."""
        self.log("\n=== 23. KARGO YÖNTEMİ OLUŞTUR ===", "INFO")
        
        data = {
            "name": "Aras Kargo",
            "code": "aras",
            "is_active": True,
            "price": "15.00",
            "free_shipping_threshold": "200.00"
        }
        
        result = self.make_request('POST', '/shipping/methods/', data, expected_status=201)
        if result and result.get('success'):
            shipping_method = result.get('shipping_method', {})
            method_id = shipping_method.get('id')
            if method_id:
                self.created_resources['shipping_methods'].append(method_id)
            self.log(f"Kargo yöntemi oluşturuldu: {shipping_method.get('name')}", "SUCCESS")
            return shipping_method
        return None
    
    def test_calculate_shipping(self):
        """24. Kargo ücreti hesapla."""
        self.log("\n=== 24. KARGO ÜCRETİ HESAPLA ===", "INFO")
        
        if not self.created_resources['shipping_methods']:
            self.log("Kargo yöntemi yok, atlanıyor", "WARNING")
            return None
        
        method_id = self.created_resources['shipping_methods'][0]
        data = {
            "shipping_method_id": method_id,
            "country": "TR",
            "city": "Istanbul",
            "postal_code": "34000",
            "order_amount": "150.00",
            "total_weight": "1.5"
        }
        
        result = self.make_request('POST', '/shipping/calculate/', data, expected_status=200, headers={})
        if result and result.get('success'):
            shipping_cost = result.get('shipping_cost')
            self.log(f"Kargo ücreti: {shipping_cost} TL", "SUCCESS")
            return result
        return None
    
    def test_create_shipping_address(self):
        """25. Kargo adresi oluştur."""
        self.log("\n=== 25. KARGO ADRESİ OLUŞTUR ===", "INFO")
        
        # Tenant user token kullan
        old_token = self.token
        if self.tenant_user_token:
            self.token = self.tenant_user_token
        
        data = {
            "first_name": "Test",
            "last_name": "Müşteri",
            "phone": "+905551234567",
            "address_line_1": "Test Mahallesi Test Sokak No:1",
            "city": "Istanbul",
            "postal_code": "34000",
            "country": "Turkey",
            "is_default": True
        }
        
        result = self.make_request('POST', '/shipping/addresses/', data, expected_status=201)
        if self.tenant_user_token:
            self.token = old_token
        
        if result and result.get('success'):
            address = result.get('shipping_address', {})
            address_id = address.get('id')
            if address_id:
                self.created_resources['shipping_addresses'].append(address_id)
            self.log("Kargo adresi oluşturuldu", "SUCCESS")
            return address
        return None
    
    def test_create_bundle(self):
        """26. Bundle oluştur."""
        self.log("\n=== 26. BUNDLE OLUŞTUR ===", "INFO")
        
        if not self.created_resources['products']:
            self.log("Ürün yok, atlanıyor", "WARNING")
            return None
        
        main_product_id = self.created_resources['products'][0]
        timestamp = int(time.time())
        data = {
            "name": f"Test Bundle {timestamp}",
            "slug": f"test-bundle-{timestamp}",
            "description": "Test bundle açıklaması",
            "main_product_id": main_product_id,
            "bundle_price": "150.00",
            "discount_percentage": "10.00",
            "is_active": True,
            "sort_order": 0
        }
        
        result = self.make_request('POST', '/bundles/', data, expected_status=201)
        if result and result.get('success'):
            bundle = result.get('bundle', {})
            bundle_id = bundle.get('id')
            if bundle_id:
                self.created_resources['bundles'].append(bundle_id)
            self.log(f"Bundle oluşturuldu: {bundle.get('name')}", "SUCCESS")
            return bundle
        return None
    
    def test_add_bundle_item(self):
        """27. Bundle'a ürün ekle."""
        self.log("\n=== 27. BUNDLE'A ÜRÜN EKLE ===", "INFO")
        
        if not self.created_resources['bundles'] or not self.created_resources['products']:
            self.log("Bundle veya ürün yok, atlanıyor", "WARNING")
            return None
        
        bundle_id = self.created_resources['bundles'][0]
        product_id = self.created_resources['products'][0]
        
        data = {
            "product_id": product_id,
            "quantity": 1,
            "position": 0
        }
        
        result = self.make_request('POST', f'/bundles/{bundle_id}/items/', data, expected_status=201)
        if result and result.get('success'):
            self.log("Ürün bundle'a eklendi", "SUCCESS")
            return result.get('item')
        return None
    
    def test_create_analytics_event(self):
        """28. Analytics event oluştur."""
        self.log("\n=== 28. ANALYTICS EVENT OLUŞTUR ===", "INFO")
        
        data = {
            "event_type": "product_view",
            "session_id": f"test_session_{int(time.time())}",
            "event_data": {
                "product_id": str(self.created_resources['products'][0]) if self.created_resources['products'] else None
            }
        }
        
        result = self.make_request('POST', '/analytics/events/', data, expected_status=201, headers={})
        if result and result.get('success'):
            self.log("Analytics event oluşturuldu", "SUCCESS")
            return result.get('event')
        return None
    
    def test_get_analytics_dashboard(self):
        """29. Analytics dashboard getir."""
        self.log("\n=== 29. ANALYTICS DASHBOARD ===", "INFO")
        
        result = self.make_request('GET', '/analytics/dashboard/', expected_status=200)
        if result and result.get('success'):
            dashboard = result.get('dashboard', {})
            orders = dashboard.get('orders', {})
            self.log(f"Dashboard alındı. Toplam sipariş: {orders.get('total')}, Gelir: {orders.get('total_revenue')} TL", "SUCCESS")
            return dashboard
        return None
    
    def test_get_abandoned_carts(self):
        """30. Abandoned cart listesi getir."""
        self.log("\n=== 30. ABANDONED CART LİSTESİ ===", "INFO")
        
        result = self.make_request('GET', '/abandoned-carts/', expected_status=200)
        if result and result.get('success'):
            abandoned_carts = result.get('abandoned_carts', [])
            self.log(f"{len(abandoned_carts)} abandoned cart bulundu", "SUCCESS")
            return abandoned_carts
        return None
    
    def test_create_webhook(self):
        """31. Webhook oluştur."""
        self.log("\n=== 31. WEBHOOK OLUŞTUR ===", "INFO")
        
        data = {
            "name": "Test Webhook",
            "url": "https://example.com/webhook",
            "events": ["order.created", "order.completed"],
            "status": "active"
        }
        
        result = self.make_request('POST', '/webhooks/', data, expected_status=201)
        if result and result.get('success'):
            webhook = result.get('webhook', {})
            webhook_id = webhook.get('id')
            if webhook_id:
                self.created_resources.setdefault('webhooks', []).append(webhook_id)
            self.log(f"Webhook oluşturuldu: {webhook.get('name')}", "SUCCESS")
            return webhook
        return None
    
    def test_get_webhooks(self):
        """32. Webhook listesi getir."""
        self.log("\n=== 32. WEBHOOK LİSTESİ ===", "INFO")
        
        result = self.make_request('GET', '/webhooks/', expected_status=200)
        if result and result.get('success'):
            webhooks = result.get('webhooks', [])
            self.log(f"{len(webhooks)} webhook bulundu", "SUCCESS")
            return webhooks
        return None
    
    def test_create_inventory_alert(self):
        """33. Inventory alert oluştur."""
        self.log("\n=== 33. INVENTORY ALERT OLUŞTUR ===", "INFO")
        
        if not self.created_resources['products']:
            self.log("Ürün yok, atlanıyor", "WARNING")
            return None
        
        product_id = self.created_resources['products'][0]
        data = {
            "product_id": product_id,
            "threshold": 10,
            "notify_email": "test@example.com",
            "notify_on_low_stock": True,
            "notify_on_out_of_stock": True,
            "is_active": True
        }
        
        result = self.make_request('POST', '/inventory/alerts/', data, expected_status=201)
        if result and result.get('success'):
            alert = result.get('alert', {})
            alert_id = alert.get('id')
            if alert_id:
                self.created_resources.setdefault('inventory_alerts', []).append(alert_id)
            self.log(f"Inventory alert oluşturuldu: threshold={alert.get('threshold')}", "SUCCESS")
            return alert
        return None
    
    def test_get_inventory_alerts(self):
        """34. Inventory alert listesi getir."""
        self.log("\n=== 34. INVENTORY ALERT LİSTESİ ===", "INFO")
        
        result = self.make_request('GET', '/inventory/alerts/', expected_status=200)
        if result and result.get('success'):
            alerts = result.get('alerts', [])
            self.log(f"{len(alerts)} inventory alert bulundu", "SUCCESS")
            return alerts
        return None
    
    def test_create_shipping_zone_rate(self):
        """35. Shipping zone rate oluştur."""
        self.log("\n=== 35. SHIPPING ZONE RATE OLUŞTUR ===", "INFO")
        
        # Önce bir shipping zone oluştur
        zone_data = {
            "name": "Test Zone",
            "countries": ["TR"],
            "cities": ["Istanbul"],
            "is_active": True
        }
        
        zone_result = self.make_request('POST', '/shipping/zones/', zone_data, expected_status=201)
        if not zone_result or not zone_result.get('success'):
            self.log("Shipping zone oluşturulamadı, atlanıyor", "WARNING")
            return None
        
        zone_id = zone_result.get('shipping_zone', {}).get('id')
        if not zone_id:
            self.log("Zone ID alınamadı, atlanıyor", "WARNING")
            return None
        
        if not self.created_resources['shipping_methods']:
            self.log("Shipping method yok, atlanıyor", "WARNING")
            return None
        
        method_id = self.created_resources['shipping_methods'][0]
        data = {
            "shipping_method_id": method_id,
            "base_price": "20.00",
            "price_per_kg": "5.00",
            "free_shipping_threshold": "200.00",
            "is_active": True
        }
        
        result = self.make_request('POST', f'/shipping/zones/{zone_id}/rates/', data, expected_status=201)
        if result and result.get('success'):
            rate = result.get('rate', {})
            self.log(f"Shipping zone rate oluşturuldu: base_price={rate.get('base_price')}", "SUCCESS")
            return rate
        return None
    
    def run_all_tests(self):
        """Tüm testleri çalıştır."""
        self.log("=" * 60, "INFO")
        self.log("API TEST BAŞLIYOR", "INFO")
        self.log("=" * 60, "INFO")
        
        # 1. Register
        if not self.test_register():
            self.log("Register başarısız, testler durduruluyor", "ERROR")
            return
        
        # 2. Login (tekrar)
        timestamp = int(time.time())
        email = f"test_owner_{timestamp}@test.com"
        self.test_login(email, "Test123456!")
        
        # 3-6. Product operations
        self.test_create_category()
        self.test_create_product()
        self.test_get_products()
        self.test_get_product_detail()
        
        # 7-8. Tenant user
        user_result = self.test_register_tenant_user()
        if user_result:
            user_email = user_result.get('user', {}).get('email')
            if user_email:
                self.test_login_tenant_user(user_email, "Test123456!")
        
        # 9-11. Cart operations
        self.test_create_cart()
        self.test_add_to_cart()
        self.test_get_cart()
        
        # 12-13. Search & Public
        self.test_search_products()
        self.test_public_product_list()
        
        # 14. Loyalty
        self.test_loyalty_program()
        
        # 15-16. Review
        self.test_create_review()
        self.test_get_reviews()
        
        # 17-18. Wishlist
        self.test_create_wishlist()
        self.test_add_to_wishlist()
        
        # 19-20. Discount/Coupon
        self.test_create_coupon()
        self.test_validate_coupon()
        
        # 21-22. Gift Card
        self.test_create_gift_card()
        self.test_validate_gift_card()
        
        # 23-25. Shipping
        self.test_create_shipping_method()
        self.test_calculate_shipping()
        self.test_create_shipping_address()
        
        # 26-28. Bundle
        self.test_create_bundle()
        self.test_add_bundle_item()
        
        # 29-30. Analytics
        self.test_create_analytics_event()
        self.test_get_analytics_dashboard()
        
        # 31. Abandoned Cart
        self.test_get_abandoned_carts()
        
        # 32-34. Webhook
        self.test_create_webhook()
        self.test_get_webhooks()
        
        # 35-36. Inventory Alert
        self.test_create_inventory_alert()
        self.test_get_inventory_alerts()
        
        # 37. Shipping Zone Rate
        self.test_create_shipping_zone_rate()
        
        self.log("=" * 60, "INFO")
        self.log("TÜM TESTLER TAMAMLANDI", "SUCCESS")
        self.log("=" * 60, "INFO")
        
        # Özet
        self.log(f"\nOluşturulan kaynaklar:", "INFO")
        self.log(f"  - Kategoriler: {len(self.created_resources['categories'])}", "INFO")
        self.log(f"  - Ürünler: {len(self.created_resources['products'])}", "INFO")
        self.log(f"  - Sepetler: {len(self.created_resources['carts'])}", "INFO")
        self.log(f"  - Yorumlar: {len(self.created_resources['reviews'])}", "INFO")
        self.log(f"  - Wishlist'ler: {len(self.created_resources['wishlists'])}", "INFO")
        self.log(f"  - Kuponlar: {len(self.created_resources['coupons'])}", "INFO")
        self.log(f"  - Gift Card'lar: {len(self.created_resources['gift_cards'])}", "INFO")
        self.log(f"  - Kargo Yöntemleri: {len(self.created_resources['shipping_methods'])}", "INFO")
        self.log(f"  - Kargo Adresleri: {len(self.created_resources['shipping_addresses'])}", "INFO")
        self.log(f"  - Bundle'lar: {len(self.created_resources['bundles'])}", "INFO")


if __name__ == "__main__":
    import sys
    
    # Base URL argüman olarak alınabilir
    base_url = sys.argv[1] if len(sys.argv) > 1 else BASE_URL
    
    tester = APITester(base_url)
    tester.run_all_tests()

