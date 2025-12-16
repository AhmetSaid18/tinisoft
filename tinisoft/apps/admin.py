from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.models import User, Tenant, Domain

# Custom User Admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'tenant', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Tenant & Role', {'fields': ('tenant', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'subdomain', 'custom_domain', 'owner', 'status', 'plan', 'created_at']
    list_filter = ['status', 'plan', 'created_at']
    search_fields = ['name', 'slug', 'subdomain', 'custom_domain']
    readonly_fields = ['created_at', 'updated_at', 'activated_at', 'suspended_at']


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain_name', 'tenant', 'is_primary', 'is_custom', 'verification_status', 'verified_at']
    list_filter = ['is_custom', 'verification_status', 'ssl_enabled']
    search_fields = ['domain_name', 'tenant__name']
    readonly_fields = ['created_at', 'updated_at', 'verified_at', 'last_checked_at']

