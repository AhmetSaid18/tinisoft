from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class ManagementRoleEmailBackend(ModelBackend):
    """
    Özel Kimlik Doğrulama Sistemi (Smart Login).
    
    Bu backend şunları yapar:
    1. Standart username (email) ile girişi dener.
    2. Eğer bulamazsa, e-posta üzerinden "Yönetici" rollerini (Owner, Staff, Admin) kontrol eder.
    3. Böylece bir personel aynı e-posta ile başka mağazada müşteri olsa bile e-postasıyla giriş yapabilir.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email') or kwargs.get('username')

        # 1. Önce standart Django mantığı: Username direkt bir eşleşme mi? (Owner/Staff için username=email'dir)
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if user:
            return user

        # 2. Eğer ilk adım başarısızsa (Kullanıcı adı değişmişse -örn: müşteri olmuşsa-) 
        # sadece Management rolleri için e-posta üzerinden manuel kontrol yap.
        if username and password:
            try:
                # Sadece yönetim rollerindeki kullanıcıları e-posta adresine göre ara
                # Not: Müşteriler (TENANT_USER) bu kapıdan değil, kendi tenant loginlerinden girmeli.
                user = User.objects.get(
                    email=username,
                    role__in=[
                        User.UserRole.TENANT_OWNER, 
                        User.UserRole.TENANT_STAFF, 
                        User.UserRole.OWNER, 
                        User.UserRole.SYSTEM_ADMIN
                    ]
                )
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                return None
            except Exception:
                return None
        
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
