"""
JWT token utilities.
Token oluşturma ve doğrulama işlemleri.
"""
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


def get_jwt_secret_key():
    """JWT secret key'i al. SECRET_KEY kullanılır."""
    return getattr(settings, 'SECRET_KEY', 'django-insecure-temporary-key-change-in-production-1234567890')


def get_jwt_algorithm():
    """JWT algorithm'i döndür."""
    return 'HS256'


def get_jwt_expiration_hours():
    """JWT token expiration süresini saat cinsinden döndür."""
    return getattr(settings, 'JWT_EXPIRATION_HOURS', 24)


def generate_jwt_token(user):
    """
    Kullanıcı için JWT token oluştur.
    
    Args:
        user: User instance
    
    Returns:
        str: JWT token
    """
    try:
        # Token payload
        payload = {
            'user_id': str(user.id),
            'email': user.email,
            'username': user.username,
            'role': user.role if hasattr(user, 'role') else None,
            'tenant_id': str(user.tenant.id) if user.tenant else None,
            'is_owner': user.is_owner if hasattr(user, 'is_owner') else False,
            'iat': datetime.utcnow(),  # Issued at
            'exp': datetime.utcnow() + timedelta(hours=get_jwt_expiration_hours()),  # Expiration
        }
        
        # Token oluştur
        token = jwt.encode(
            payload,
            get_jwt_secret_key(),
            algorithm=get_jwt_algorithm()
        )
        
        logger.info(f"JWT token generated for user: {user.email}")
        return token
        
    except Exception as e:
        logger.error(f"Failed to generate JWT token for user {user.email}: {str(e)}")
        raise


def verify_jwt_token(token):
    """
    JWT token'ı doğrula ve user'ı döndür.
    
    Args:
        token: JWT token string
    
    Returns:
        tuple: (user, payload) veya (None, None) eğer geçersizse
    """
    try:
        # Token'ı decode et
        payload = jwt.decode(
            token,
            get_jwt_secret_key(),
            algorithms=[get_jwt_algorithm()]
        )
        
        # User'ı al
        user_id = payload.get('user_id')
        if not user_id:
            logger.warning("JWT token missing user_id")
            return None, None
        
        try:
            user = User.objects.get(id=user_id)
            
            # User aktif mi kontrol et
            if not user.is_active:
                logger.warning(f"User {user.email} is not active")
                return None, None
            
            return user, payload
            
        except User.DoesNotExist:
            logger.warning(f"User not found: {user_id}")
            return None, None
            
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None, None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}")
        return None, None
    except Exception as e:
        logger.error(f"JWT token verification error: {str(e)}")
        return None, None


def get_token_from_request(request):
    """
    Request'ten JWT token'ı al.
    Authorization header'dan "Bearer {token}" formatında alır.
    
    Args:
        request: Django request object
    
    Returns:
        str: Token veya None
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header:
        return None
    
    # "Bearer {token}" formatını parse et
    parts = auth_header.split()
    
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]

