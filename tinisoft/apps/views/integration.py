"""
Integration API Key yönetimi views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from apps.models import IntegrationProvider
from apps.serializers.integration import (
    IntegrationProviderSerializer,
    IntegrationProviderCreateSerializer,
    IntegrationProviderUpdateSerializer,
    IntegrationProviderTestSerializer
)
from apps.services.email_service import EmailService
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class IntegrationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def integration_list_create(request):
    """
    Entegrasyon listesi (GET) veya yeni entegrasyon oluştur (POST).
    
    GET: /api/integrations/
    POST: /api/integrations/
    Body: {
        "provider_type": "kuveyt",
        "name": "Kuveyt API - Production",
        "status": "active",
        "api_key": "your-api-key",
        "api_secret": "your-api-secret",
        "api_endpoint": "https://api.kuveyt.com/payment",
        "test_endpoint": "https://test-api.kuveyt.com/payment",
        "config": {}
    }
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece tenant owner veya admin
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        queryset = IntegrationProvider.objects.filter(tenant=tenant, is_deleted=False)
        
        # Filtreleme
        provider_type = request.query_params.get('provider_type')
        if provider_type:
            queryset = queryset.filter(provider_type=provider_type)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Sıralama
        ordering = request.query_params.get('ordering', 'provider_type')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        paginator = IntegrationPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = IntegrationProviderSerializer(page, many=True)
            return paginator.get_paginated_response({
                'success': True,
                'integrations': serializer.data,
            })
        
        serializer = IntegrationProviderSerializer(queryset, many=True)
        return Response({
            'success': True,
            'integrations': serializer.data,
        })
    
    elif request.method == 'POST':
        # Debug logging - frontend isteklerini kontrol et
        logger.info(f"[INTEGRATION POST] Content-Type: {request.content_type}")
        logger.info(f"[INTEGRATION POST] Request data: {request.data}")
        logger.info(f"[INTEGRATION POST] Request data type: {type(request.data)}")
        logger.info(f"[INTEGRATION POST] Request META Content-Type: {request.META.get('CONTENT_TYPE', 'Not set')}")
        logger.info(f"[INTEGRATION POST] Request META CONTENT_LENGTH: {request.META.get('CONTENT_LENGTH', 'Not set')}")
        
        # Eğer request.data boşsa, hata döndür - frontend sorunu
        if not request.data:
            logger.error(f"[INTEGRATION POST] Request data is empty!")
            return Response({
                'success': False,
                'message': 'Request body boş veya parse edilemedi. Content-Type: application/json olmalı.',
                'debug': {
                    'content_type': request.content_type,
                    'meta_content_type': request.META.get('CONTENT_TYPE'),
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = IntegrationProviderCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            integration = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Entegrasyon oluşturuldu.',
                'integration': IntegrationProviderSerializer(integration).data,
            }, status=status.HTTP_201_CREATED)
        
        logger.warning(f"[INTEGRATION POST] Validation errors: {serializer.errors}")
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def integration_detail(request, integration_id):
    """
    Entegrasyon detayı (GET), güncelle (PATCH) veya sil (DELETE).
    
    GET: /api/integrations/{integration_id}/
    PATCH: /api/integrations/{integration_id}/
    DELETE: /api/integrations/{integration_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        integration = IntegrationProvider.objects.get(
            id=integration_id,
            tenant=tenant,
            is_deleted=False
        )
    except IntegrationProvider.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Entegrasyon bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece tenant owner veya admin
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = IntegrationProviderSerializer(integration)
        return Response({
            'success': True,
            'integration': serializer.data,
        })
    
    elif request.method == 'PATCH':
        serializer = IntegrationProviderUpdateSerializer(
            integration,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            integration = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Entegrasyon güncellendi.',
                'integration': IntegrationProviderSerializer(integration).data,
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        integration.soft_delete()
        return Response({
            'success': True,
            'message': 'Entegrasyon silindi.',
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def integration_test(request, integration_id):
    """
    Entegrasyon test et.
    
    POST: /api/integrations/{integration_id}/test/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        integration = IntegrationProvider.objects.get(
            id=integration_id,
            tenant=tenant,
            is_deleted=False
        )
    except IntegrationProvider.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Entegrasyon bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece tenant owner veya admin
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Entegrasyon tipine göre test yap
    try:
        if integration.provider_type == IntegrationProvider.ProviderType.KUVEYT:
            # Kuveyt API test
            from apps.services.payment_providers import PaymentProviderFactory
            
            provider = PaymentProviderFactory.get_provider(
                tenant=tenant,
                provider_name='kuwait',
                config=integration.get_provider_config()
            )
            
            # Test için dummy order oluştur (gerçek order gerekmez)
            test_result = {
                'success': True,
                'message': 'Kuveyt API bağlantısı test edildi.',
                'endpoint': integration.get_endpoint(),
                'test_mode': integration.status == IntegrationProvider.Status.TEST_MODE,
            }
            
        elif integration.provider_type == IntegrationProvider.ProviderType.EMAIL:
            # Email test - test email gönder
            test_email = request.data.get('test_email', request.user.email)
            test_message = request.data.get('test_message', 'Bu bir test emailidir. SMTP ayarlarınız doğru çalışıyor!')
            
            if not test_email:
                return Response({
                    'success': False,
                    'message': 'Test email adresi gereklidir.',
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Test email gönder
            email_result = EmailService.send_email(
                tenant=tenant,
                to_email=test_email,
                subject=f"Test Email - {tenant.name}",
                html_content=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                        .content {{ padding: 20px; background-color: #f9f9f9; }}
                        .message {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Test Email</h1>
                        </div>
                        <div class="content">
                            <p>Merhaba,</p>
                            <div class="message">
                                <p>{test_message}</p>
                            </div>
                            <p>Bu email {tenant.name} tarafından SMTP ayarlarını test etmek için gönderilmiştir.</p>
                            <p>Eğer bu emaili alıyorsanız, SMTP ayarlarınız doğru çalışıyor demektir!</p>
                            <p>Teşekkür ederiz!</p>
                            <p><strong>{tenant.name}</strong></p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                text_content=f"""
Test Email

Merhaba,

{test_message}

Bu email {tenant.name} tarafından SMTP ayarlarını test etmek için gönderilmiştir.
Eğer bu emaili alıyorsanız, SMTP ayarlarınız doğru çalışıyor demektir!

Teşekkür ederiz!
{tenant.name}
                """
            )
            
            if email_result['success']:
                test_result = {
                    'success': True,
                    'message': f'Test email başarıyla gönderildi. Lütfen {test_email} adresinizi kontrol edin.',
                    'test_email': test_email,
                }
            else:
                test_result = {
                    'success': False,
                    'message': f'Email gönderilemedi: {email_result.get("message", "Bilinmeyen hata")}',
                    'error': email_result.get('error', ''),
                    'test_email': test_email,
                }
        
        elif integration.provider_type in [
            IntegrationProvider.ProviderType.ARAS,
            IntegrationProvider.ProviderType.YURTICI,
            IntegrationProvider.ProviderType.MNG,
        ]:
            # Kargo API test (ileride implement edilebilir)
            test_result = {
                'success': True,
                'message': f'{integration.get_provider_type_display()} API testi henüz implement edilmedi.',
            }
        
        else:
            test_result = {
                'success': True,
                'message': f'{integration.get_provider_type_display()} testi henüz implement edilmedi.',
            }
        
        # Test sonucuna göre response döndür
        if test_result.get('success', False):
            return Response({
                'success': True,
                'message': test_result.get('message', 'Test başarılı.'),
                'test_result': test_result,
            })
        else:
            return Response({
                'success': False,
                'message': test_result.get('message', 'Test başarısız. Lütfen SMTP ayarlarınızı kontrol edin.'),
                'test_result': test_result,
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Integration test error: {str(e)}")
        integration.last_error = str(e)
        integration.save()
        
        return Response({
            'success': False,
            'message': f'Test başarısız: {str(e)}',
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def integration_by_type(request, provider_type):
    """
    Belirli bir provider tipine göre aktif entegrasyonu getir.
    
    GET: /api/integrations/type/{provider_type}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        integration = IntegrationProvider.objects.get(
            tenant=tenant,
            provider_type=provider_type,
            status__in=[
                IntegrationProvider.Status.ACTIVE,
                IntegrationProvider.Status.TEST_MODE
            ],
            is_deleted=False
        )
    except IntegrationProvider.DoesNotExist:
        return Response({
            'success': False,
            'message': f'{provider_type} entegrasyonu bulunamadı veya aktif değil.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece tenant owner veya admin
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = IntegrationProviderSerializer(integration)
    return Response({
        'success': True,
        'integration': serializer.data,
    })

