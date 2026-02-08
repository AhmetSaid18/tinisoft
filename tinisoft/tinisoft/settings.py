"""
Django settings for Tinisoft project.
"""
import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
# Önce environment variable'dan oku (docker-compose), yoksa .env'den oku
SECRET_KEY = env('SECRET_KEY', default='django-insecure-temporary-key-change-in-production-1234567890')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')


# Development ve SaaS Production için tüm hostlara izin ver
# Güvenlik Traefik ve TenantMiddleware ile sağlanır
ALLOWED_HOSTS = ["*"]

# CORS Configuration
# SaaS yapısında müşterilerin kendi domainleri olacağı için (binlerce farklı domain)
# CORS kısıtlaması yerine Authentication (Token) ve Tenant yetkilendirmesi kullanılır.
CORS_ALLOW_ALL_ORIGINS = True

# Custom User Model
AUTH_USER_MODEL = 'apps.User'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'apps.auth_backends.ManagementRoleEmailBackend',  # Smart Login (e-posta & rol kontrolü)
    'django.contrib.auth.backends.ModelBackend',     # Standart Django girişi
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    
    # Local apps
    'apps',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'core.middleware.TenantMiddleware',  # Multi-tenant middleware
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tinisoft.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tinisoft.wsgi.application'

# Database - Tek PostgreSQL veritabanı, tüm modüller burada
# Multi-tenant için schema'lar kullanılacak (public, tenant_1, tenant_2, vb.)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='tinisoft'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='postgres'),
        'HOST': env('DB_HOST', default='postgres'),
        'PORT': env('DB_PORT', default='5432'),
        'OPTIONS': {
            # Default schema: public (sistem tabloları ve tenant yönetimi için)
            'options': f'-c search_path={env("DB_SCHEMA", default="public")}'
        },
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}

# Multi-Tenant Settings
MULTI_TENANT_ENABLED = env.bool('MULTI_TENANT_ENABLED', default=True)
DEFAULT_TENANT_SCHEMA = 'public'  # Sistem tabloları için

# Database Router - Multi-tenant için schema routing
DATABASE_ROUTERS = ['core.db_router.TenantDatabaseRouter']

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Session Configuration (Cookie için)
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 gün
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # HTTPS için True yap (production'da)
SESSION_COOKIE_SAMESITE = 'Lax'  # CORS için 'Lax' veya 'None' (Secure=True ise 'None')
SESSION_SAVE_EVERY_REQUEST = True  # Her istekte session'ı kaydet
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Tarayıcı kapanınca session'ı silme

# CSRF Configuration (Cookie için)
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_HTTPONLY = False  # JavaScript'ten okunabilir olmalı
CSRF_COOKIE_SECURE = False  # HTTPS için True yap (production'da)
CSRF_COOKIE_SAMESITE = 'Lax'  # CORS için 'Lax' veya 'None' (Secure=True ise 'None')
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'http://localhost:3000',
    'http://localhost:3001',
    'https://tinisoft.com.tr',
    'https://www.tinisoft.com.tr',
    'https://test.avrupamutfak.com',
    'http://test.avrupamutfak.com',
])

# Internationalization
LANGUAGE_CODE = env('LANGUAGE_CODE', default='tr-tr')
TIME_ZONE = env('TIME_ZONE', default='Europe/Istanbul')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (Product images) - Cloudflare R2
USE_R2 = env.bool('USE_R2', default=False)  # R2 kullanılsın mı?

if USE_R2:
    # Cloudflare R2 Storage
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
    
    # R2 Settings (S3 uyumlu)
    AWS_ACCESS_KEY_ID = env('R2_ACCESS_KEY_ID', default='')
    AWS_SECRET_ACCESS_KEY = env('R2_SECRET_ACCESS_KEY', default='')
    AWS_STORAGE_BUCKET_NAME = env('R2_BUCKET_NAME', default='')
    AWS_S3_ENDPOINT_URL = env('R2_ENDPOINT_URL', default='')  # Örn: https://xxx.r2.cloudflarestorage.com
    AWS_S3_REGION_NAME = env('R2_REGION', default='auto')
    AWS_S3_CUSTOM_DOMAIN = env('R2_CUSTOM_DOMAIN', default='')  # Örn: cdn.tinisoft.com.tr (opsiyonel)
    R2_ACCOUNT_ID = env('R2_ACCOUNT_ID', default='')  # Cloudflare R2 Account ID (opsiyonel, bazı işlemler için gerekli)
    
    # R2 özel ayarlar
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',  # 1 gün cache
    }
    AWS_DEFAULT_ACL = 'public-read'  # Public read (görseller için)
    AWS_QUERYSTRING_AUTH = False  # Query string auth yok (CDN için)
    AWS_S3_FILE_OVERWRITE = False  # Aynı isimli dosya üzerine yazma
    
    # Media URL (R2'den)
    # Custom domain varsa onu kullan, yoksa endpoint URL'i kullan
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    elif AWS_S3_ENDPOINT_URL:
        # R2 endpoint URL'i direkt kullan (boto3 otomatik olarak bucket'a yönlendirir)
        MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/media/'
    else:
        MEDIA_URL = '/media/'  # Fallback
    
    MEDIA_ROOT = ''  # R2 kullanıldığında local media root gerekmez
else:
    # Local storage (development)
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File Upload Limits (413 hatası için)
# Excel dosyaları için yüksek limit (4000+ ürün için)
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100 MB (10 MB'dan artırıldı)
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100 MB (10 MB'dan artırıldı)
DATA_UPLOAD_MAX_NUMBER_FIELDS = 50000  # Form field limit (10000'den artırıldı)

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.utils.jwt_authentication.JWTAuthentication',  # JWT authentication (öncelikli)
        'rest_framework.authentication.SessionAuthentication',  # Session authentication (fallback)
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',  # JSON parser
        'rest_framework.parsers.FormParser',  # Form data parser
        'rest_framework.parsers.MultiPartParser',  # File upload parser
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',  # Custom exception handler
}

# JWT Settings
JWT_EXPIRATION_HOURS = env.int('JWT_EXPIRATION_HOURS', default=24)  # Token geçerlilik süresi (saat)

# API Base URL (Backend domain - Kuveyt callback için)
# Kuveyt'e gönderilecek OkUrl ve FailUrl'ler bu domain'i kullanır
# Örnek: https://api.tinisoft.com.tr
API_BASE_URL = env('API_BASE_URL', default='https://api.tinisoft.com.tr')

# Kuveyt Payment API Endpoints (Sabit - env'den alınır)
KUVEYT_API_URL = env('KUVEYT_API_URL', default='https://boa.kuveytturk.com.tr/sanalposservice/Home/ThreeDModelPayGate')
KUVEYT_API_TEST_URL = env('KUVEYT_API_TEST_URL', default='https://boatest.kuveytturk.com.tr/boa.virtualpos.services/Home/ThreeDModelPayGate')

# Frontend URL (Store frontend domain - callback sonrası redirect için)
# Kuveyt callback işlendikten sonra kullanıcı bu domain'e yönlendirilir
# Örnek: https://avrupamutfak.com veya tenant-specific domain
FRONTEND_URL = env('FRONTEND_URL', default='https://avrupamutfak.com')
STORE_FRONTEND_URL = env('STORE_FRONTEND_URL', default=None)  # Tenant-specific frontend URL (opsiyonel)

# CORS
# CORS_ALLOWED_ORIGINS listesi artık gereksiz çünkü CORS_ALLOW_ALL_ORIGINS = True yaptık.
# Güvenlik Token ve Tenant ID kontrolü ile sağlanır.

CORS_ALLOW_CREDENTIALS = True

# CORS Headers - Tüm gerekli header'ları ekle
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-tenant-id',  # Multi-tenant için
    'x-tenant-slug',  # Multi-tenant için (slug ile)
    'x-guest-id',  # Guest sepet ID'si için (frontend localStorage'dan)
    'x-currency-code',  # Para birimi seçimi için (TRY, USD, EUR)
    'cache-control',
    'pragma',
]

# CORS Methods - Tüm HTTP method'larına izin ver
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Preflight cache süresi (OPTIONS istekleri için)
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 saat

# Integration Encryption Key (API key şifreleme için)
# Production'da mutlaka değiştirilmeli!
INTEGRATION_ENCRYPTION_KEY = env('INTEGRATION_ENCRYPTION_KEY', default='django-insecure-integration-key-change-in-production-12345678901234567890')

# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Redis Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f"redis://{env('REDIS_HOST', default='redis')}:{env('REDIS_PORT', default='6379')}/{env('REDIS_DB', default='0')}",
    }
}

# Domain Management Settings
DOMAIN_VERIFICATION_TXT_PREFIX = 'tinisoft-verify'
DOMAIN_VERIFICATION_CNAME_TARGET = 'verify.tinisoft.com.tr'
DOMAIN_VERIFICATION_CHECK_INTERVAL = 300  # 5 dakika

# Build Automation Settings
FRONTEND_REPO_URL = env('FRONTEND_REPO_URL', default='')
FRONTEND_BUILD_DIR = env('FRONTEND_BUILD_DIR', default='/app/builds')
DOCKER_REGISTRY = env('DOCKER_REGISTRY', default='')
TRAEFIK_API_URL = env('TRAEFIK_API_URL', default='http://traefik:8080')

# Logging
# Log klasörünü oluştur (yoksa)
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': env('LOG_FILE', default=os.path.join(LOG_DIR, 'tinisoft.log')),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',

    },
}

# Integration API Keys Encryption Key
# Production'da mutlaka güçlü bir key kullanın!
# Key oluşturmak için: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Development için default key (production'da environment variable'dan ayarlanmalı!)
INTEGRATION_ENCRYPTION_KEY = env(
    'INTEGRATION_ENCRYPTION_KEY', 
    default='AYKTqmBEf7a56UVkiH_E0ZmSd4luaba4q5q6xX-LGP0='
)

# Kuveyt Türk Test Ortam Bilgileri (Test modunda otomatik kullanılır)
KUVEYT_TEST_CUSTOMER_ID = env('KUVEYT_TEST_CUSTOMER_ID', default='400235')
KUVEYT_TEST_MERCHANT_ID = env('KUVEYT_TEST_MERCHANT_ID', default='496')
KUVEYT_TEST_USERNAME = env('KUVEYT_TEST_USERNAME', default='apitest')
KUVEYT_TEST_PASSWORD = env('KUVEYT_TEST_PASSWORD', default='api123')

