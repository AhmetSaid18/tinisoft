"""
Custom JWT Authentication for Django REST Framework.
"""
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from apps.utils.jwt_utils import get_token_from_request, verify_jwt_token
import logging

logger = logging.getLogger(__name__)


class JWTAuthentication(authentication.BaseAuthentication):
    """
    JWT token tabanlı authentication.
    Authorization header'dan "Bearer {token}" formatında token alır.
    """
    
    def authenticate(self, request):
        """
        Request'ten JWT token'ı al ve doğrula.
        
        Returns:
            tuple: (user, token) veya None
        """
        # Token'ı al
        token = get_token_from_request(request)
        
        if not token:
            return None  # Authentication yapılmadı, diğer authentication class'larına geç
        
        # Token'ı doğrula
        user, payload = verify_jwt_token(token)
        
        if not user:
            raise AuthenticationFailed('Geçersiz veya süresi dolmuş token.')
        
        return (user, token)

