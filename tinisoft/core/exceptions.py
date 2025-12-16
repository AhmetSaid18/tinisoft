"""
Custom exception handlers for better error management.
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed, ValidationError
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses.
    Tüm hataları standart formatta döndürür.
    """
    # DRF'nin default exception handler'ını çağır
    response = exception_handler(exc, context)
    
    if response is not None:
        # Response'u standart formata çevir
        custom_response_data = {
            'success': False,
            'message': 'Bir hata oluştu.',
            'error_code': None,
            'errors': {},
        }
        
        # Exception tipine göre mesaj ve kod belirle
        if isinstance(exc, PermissionDenied):
            custom_response_data['message'] = 'Bu işlem için yetkiniz yok.'
            custom_response_data['error_code'] = 'PERMISSION_DENIED'
            if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
                custom_response_data.update(exc.detail)
            elif hasattr(exc, 'detail'):
                custom_response_data['message'] = str(exc.detail)
        
        elif isinstance(exc, AuthenticationFailed):
            custom_response_data['message'] = 'Kimlik doğrulama başarısız.'
            custom_response_data['error_code'] = 'AUTHENTICATION_FAILED'
            if hasattr(exc, 'detail'):
                custom_response_data['message'] = str(exc.detail)
        
        elif isinstance(exc, ValidationError):
            custom_response_data['message'] = 'Geçersiz veri.'
            custom_response_data['error_code'] = 'VALIDATION_ERROR'
            if hasattr(exc, 'detail'):
                if isinstance(exc.detail, dict):
                    custom_response_data['errors'] = exc.detail
                else:
                    custom_response_data['message'] = str(exc.detail)
        
        else:
            # Diğer hatalar için
            if hasattr(exc, 'detail'):
                if isinstance(exc.detail, dict):
                    custom_response_data.update(exc.detail)
                else:
                    custom_response_data['message'] = str(exc.detail)
        
        # Response data'yı güncelle
        response.data = custom_response_data
        
        # Logla
        logger.error(f"Exception: {type(exc).__name__} - {custom_response_data['message']}")
    
    return response

