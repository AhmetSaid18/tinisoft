"""
URL configuration for Tinisoft apps.
"""
from django.urls import path
from apps.views.auth import register, login
from apps.views.tenant_user import register_tenant_user, login_tenant_user
from apps.views.domain import verify_domain, verify_domain_by_code, domain_status, list_domains

app_name = 'apps'

urlpatterns = [
    # Owner kayıt/giriş (mağaza sahibi)
    path('auth/register/', register, name='register'),
    path('auth/login/', login, name='login'),
    
    # TenantUser kayıt/giriş (tenant'ın sitesinde müşteriler)
    path('tenant/<str:tenant_slug>/users/register/', register_tenant_user, name='register_tenant_user'),
    path('tenant/<str:tenant_slug>/users/login/', login_tenant_user, name='login_tenant_user'),
    
    # Domain yönetimi
    path('domains/', list_domains, name='list_domains'),
    path('domains/verify-by-code/', verify_domain_by_code, name='verify_domain_by_code'),  # Public endpoint (verification_code ile)
    path('domains/<uuid:domain_id>/verify/', verify_domain, name='verify_domain'),  # Authenticated endpoint
    path('domains/<uuid:domain_id>/status/', domain_status, name='domain_status'),
]

