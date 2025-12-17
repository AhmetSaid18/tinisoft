"""
Webhook views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
import requests
import time
import hmac
import hashlib
import json
from apps.models import Webhook, WebhookEvent
from apps.serializers.webhook import (
    WebhookSerializer, WebhookCreateSerializer,
    WebhookEventSerializer, WebhookTestSerializer
)
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class WebhookPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def generate_webhook_signature(secret_key, payload):
    """Webhook signature oluştur."""
    return hmac.new(
        secret_key.encode('utf-8'),
        json.dumps(payload, sort_keys=True).encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def webhook_list_create(request):
    """
    Webhook listesi (GET) veya yeni webhook oluştur (POST).
    
    GET: /api/webhooks/
    POST: /api/webhooks/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        queryset = Webhook.objects.filter(tenant=tenant, is_deleted=False)
        
        # Filtreleme
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(url__icontains=search)
            )
        
        # Sıralama
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        paginator = WebhookPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = WebhookSerializer(page, many=True)
            return paginator.get_paginated_response({
                'success': True,
                'webhooks': serializer.data,
            })
        
        serializer = WebhookSerializer(queryset, many=True)
        return Response({
            'success': True,
            'webhooks': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = WebhookCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            webhook = serializer.save(tenant=tenant)
            
            return Response({
                'success': True,
                'message': 'Webhook oluşturuldu.',
                'webhook': WebhookSerializer(webhook).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def webhook_detail(request, webhook_id):
    """
    Webhook detayı (GET), güncelle (PATCH) veya sil (DELETE).
    
    GET: /api/webhooks/<webhook_id>/
    PATCH: /api/webhooks/<webhook_id>/
    DELETE: /api/webhooks/<webhook_id>/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        webhook = Webhook.objects.get(tenant=tenant, id=webhook_id, is_deleted=False)
    except Webhook.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Webhook bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = WebhookSerializer(webhook)
        return Response({
            'success': True,
            'webhook': serializer.data,
        })
    
    elif request.method == 'PATCH':
        serializer = WebhookCreateSerializer(webhook, data=request.data, partial=True)
        
        if serializer.is_valid():
            webhook = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Webhook güncellendi.',
                'webhook': WebhookSerializer(webhook).data,
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        webhook.is_deleted = True
        webhook.save()
        
        return Response({
            'success': True,
            'message': 'Webhook silindi.',
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def webhook_test(request, webhook_id):
    """
    Webhook test et.
    
    POST: /api/webhooks/<webhook_id>/test/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        webhook = Webhook.objects.get(tenant=tenant, id=webhook_id, is_deleted=False)
    except Webhook.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Webhook bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = WebhookTestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Test payload
    payload = serializer.validated_data['payload']
    event_type = serializer.validated_data['event_type']
    
    # Signature oluştur
    signature = generate_webhook_signature(webhook.secret_key, payload)
    
    # Headers
    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': signature,
        'X-Webhook-Event': event_type,
    }
    
    # Webhook gönder
    start_time = time.time()
    try:
        response = requests.post(
            webhook.url,
            json=payload,
            headers=headers,
            timeout=10
        )
        response_time_ms = int((time.time() - start_time) * 1000)
        
        is_success = 200 <= response.status_code < 300
        
        # Event kaydı
        webhook_event = WebhookEvent.objects.create(
            webhook=webhook,
            event_type=event_type,
            payload=payload,
            request_url=webhook.url,
            request_method='POST',
            request_headers=headers,
            request_body=json.dumps(payload),
            response_status=response.status_code,
            response_body=response.text[:1000],  # İlk 1000 karakter
            response_time_ms=response_time_ms,
            is_success=is_success,
        )
        
        # İstatistikleri güncelle
        if is_success:
            webhook.success_count += 1
        else:
            webhook.failure_count += 1
        webhook.last_triggered_at = timezone.now()
        webhook.save()
        
        return Response({
            'success': True,
            'message': 'Webhook test edildi.',
            'result': {
                'status_code': response.status_code,
                'response_time_ms': response_time_ms,
                'is_success': is_success,
                'event': WebhookEventSerializer(webhook_event).data,
            },
        })
    
    except requests.exceptions.RequestException as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Event kaydı
        webhook_event = WebhookEvent.objects.create(
            webhook=webhook,
            event_type=event_type,
            payload=payload,
            request_url=webhook.url,
            request_method='POST',
            request_headers=headers,
            request_body=json.dumps(payload),
            response_status=None,
            response_body='',
            response_time_ms=response_time_ms,
            is_success=False,
            error_message=str(e),
        )
        
        webhook.failure_count += 1
        webhook.last_triggered_at = timezone.now()
        webhook.save()
        
        return Response({
            'success': False,
            'message': f'Webhook gönderilemedi: {str(e)}',
            'event': WebhookEventSerializer(webhook_event).data,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def webhook_events_list(request, webhook_id):
    """
    Webhook event geçmişi.
    
    GET: /api/webhooks/<webhook_id>/events/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        webhook = Webhook.objects.get(tenant=tenant, id=webhook_id, is_deleted=False)
    except Webhook.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Webhook bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Sadece admin veya tenant owner
    if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
        return Response({
            'success': False,
            'message': 'Bu işlem için yetkiniz yok.',
        }, status=status.HTTP_403_FORBIDDEN)
    
    queryset = WebhookEvent.objects.filter(webhook=webhook)
    
    # Filtreleme
    is_success = request.query_params.get('is_success')
    if is_success is not None:
        queryset = queryset.filter(is_success=is_success.lower() == 'true')
    
    event_type = request.query_params.get('event_type')
    if event_type:
        queryset = queryset.filter(event_type=event_type)
    
    # Sıralama
    queryset = queryset.order_by('-created_at')
    
    # Pagination
    paginator = WebhookPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = WebhookEventSerializer(page, many=True)
        return paginator.get_paginated_response({
            'success': True,
            'events': serializer.data,
        })
    
    serializer = WebhookEventSerializer(queryset, many=True)
    return Response({
        'success': True,
        'events': serializer.data,
    })

