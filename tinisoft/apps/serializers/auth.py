"""
Authentication serializers.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.models import User, Tenant


class RegisterSerializer(serializers.Serializer):
    """
    Register serializer.
    Mağaza adı, domain ve kullanıcı bilgileri alır.
    """
    # Kullanıcı bilgileri
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    phone = serializers.CharField(max_length=20, required=False)
    
    # Mağaza bilgileri
    store_name = serializers.CharField(max_length=255)  # Mağaza adı
    store_slug = serializers.SlugField(max_length=255)  # URL-friendly mağaza adı
    
    # Domain bilgileri
    custom_domain = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Custom domain (örn: example.com). Boş bırakılırsa sadece subdomain kullanılır."
    )
    
    # Template seçimi (sadece custom domain varsa)
    template = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default='default',
        help_text="Frontend template adı (default, modern, classic, vb.). Sadece custom domain girildiğinde seçilebilir."
    )
    
    def validate_email(self, value):
        """Email kontrolü."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email adresi zaten kullanılıyor.")
        return value
    
    def validate_store_slug(self, value):
        """Store slug kontrolü."""
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError("Bu mağaza adı zaten kullanılıyor.")
        return value
    
    def validate_custom_domain(self, value):
        """Custom domain kontrolü."""
        if value:
            # Domain format kontrolü
            if not value.replace('.', '').replace('-', '').isalnum():
                raise serializers.ValidationError("Geçersiz domain formatı.")
            
            # Domain zaten kayıtlı mı?
            from apps.models import Domain
            if Domain.objects.filter(domain_name=value).exists():
                raise serializers.ValidationError("Bu domain zaten kullanılıyor.")
        return value
    
    def validate(self, attrs):
        """Template ve custom domain ilişkisi kontrolü."""
        custom_domain = attrs.get('custom_domain', '').strip()
        template = attrs.get('template', '').strip()
        
        # Custom domain yoksa template seçilemez
        if not custom_domain and template and template != 'default':
            raise serializers.ValidationError({
                'template': 'Template seçimi sadece custom domain girildiğinde yapılabilir. Subdomain için bizim template kullanılacak.'
            })
        
        # Custom domain varsa template zorunlu
        if custom_domain and not template:
            attrs['template'] = 'default'  # Varsayılan template
        
        return attrs
    
    def create(self, validated_data):
        """Kullanıcı ve tenant oluştur."""
        from apps.services.auth_service import AuthService
        return AuthService.register(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone'),
            store_name=validated_data['store_name'],
            store_slug=validated_data['store_slug'],
            custom_domain=validated_data.get('custom_domain', ''),
            template=validated_data.get('template', 'default'),
        )


class LoginSerializer(serializers.Serializer):
    """
    Login serializer.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Email ve şifre kontrolü."""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError("Email veya şifre hatalı.")
            if not user.is_active:
                raise serializers.ValidationError("Hesabınız aktif değil.")
            attrs['user'] = user
        else:
            raise serializers.ValidationError("Email ve şifre gereklidir.")
        
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """User serializer."""
    tenant = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'phone',
            'role',
            'role_display',
            'tenant',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined', 'role_display']
    
    def get_tenant(self, obj):
        """Tenant bilgisini döndür."""
        if obj.tenant:
            return {
                'id': str(obj.tenant.id),
                'name': obj.tenant.name,
                'slug': obj.tenant.slug,
                'subdomain': obj.tenant.subdomain,
                'subdomain_url': obj.tenant.get_subdomain_url(),
                'custom_domain': obj.tenant.custom_domain,
                'custom_domain_url': obj.tenant.get_custom_domain_url(),
                'status': obj.tenant.status,
            }
        return None


class TenantSerializer(serializers.ModelSerializer):
    """Tenant serializer."""
    owner = UserSerializer(read_only=True)
    subdomain_url = serializers.SerializerMethodField()
    custom_domain_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'slug',
            'owner',
            'subdomain',
            'subdomain_url',
            'custom_domain',
            'custom_domain_url',
            'status',
            'plan',
            'template',  # Frontend template adı
            'activated_at',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'activated_at']
    
    def get_subdomain_url(self, obj):
        return obj.get_subdomain_url()
    
    def get_custom_domain_url(self, obj):
        return obj.get_custom_domain_url()

