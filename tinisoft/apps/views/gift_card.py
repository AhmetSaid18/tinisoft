"""
Gift Card views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal
import uuid
from apps.models import GiftCard, GiftCardTransaction
from apps.serializers.gift_card import (
    GiftCardSerializer, GiftCardCreateSerializer,
    GiftCardValidateSerializer, GiftCardApplySerializer,
    GiftCardTransactionSerializer
)
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class GiftCardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def generate_gift_card_code():
    """Gift card kodu oluştur."""
    return f"GC-{uuid.uuid4().hex[:12].upper()}"


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def gift_card_list_create(request):
    """
    Gift card listesi (GET) veya yeni gift card oluştur (POST).
    
    GET: /api/gift-cards/
    POST: /api/gift-cards/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        # Kullanıcının gift card'larını getir
        queryset = GiftCard.objects.filter(tenant=tenant, is_deleted=False)
        
        # Eğer tenant user ise, sadece kendi kartlarını göster
        if request.user.is_tenant_user and request.user.tenant == tenant:
            queryset = queryset.filter(
                Q(customer=request.user) | Q(customer_email=request.user.email)
            )
        # Admin ise tüm kartları göster
        elif not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Filtreleme
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        code = request.query_params.get('code')
        if code:
            queryset = queryset.filter(code__icontains=code)
        
        # Sıralama
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        paginator = GiftCardPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = GiftCardSerializer(page, many=True)
            return paginator.get_paginated_response({
                'success': True,
                'gift_cards': serializer.data,
            })
        
        serializer = GiftCardSerializer(queryset, many=True)
        return Response({
            'success': True,
            'gift_cards': serializer.data,
        })
    
    elif request.method == 'POST':
        # Sadece admin veya tenant owner
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = GiftCardCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Code yoksa otomatik oluştur
            code = serializer.validated_data.get('code')
            if not code:
                code = generate_gift_card_code()
                # Unique kontrolü
                while GiftCard.objects.filter(tenant=tenant, code=code, is_deleted=False).exists():
                    code = generate_gift_card_code()
            else:
                # Code unique kontrolü
                if GiftCard.objects.filter(tenant=tenant, code=code, is_deleted=False).exists():
                    return Response({
                        'success': False,
                        'message': 'Bu kart kodu zaten kullanılıyor.',
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Gift card oluştur
            initial_amount = serializer.validated_data.get('initial_amount', Decimal('0.00'))
            gift_card = GiftCard.objects.create(
                tenant=tenant,
                code=code,
                type=serializer.validated_data.get('type', 'fixed'),
                initial_amount=initial_amount,
                current_amount=initial_amount,
                percentage_value=serializer.validated_data.get('percentage_value'),
                customer_email=serializer.validated_data.get('customer_email', ''),
                valid_from=serializer.validated_data.get('valid_from', timezone.now()),
                valid_until=serializer.validated_data.get('valid_until'),
                note=serializer.validated_data.get('note', ''),
            )
            
            # Transaction kaydı
            GiftCardTransaction.objects.create(
                gift_card=gift_card,
                transaction_type='purchase',
                amount=initial_amount,
                notes='Gift card oluşturuldu',
            )
            
            return Response({
                'success': True,
                'message': 'Gift card oluşturuldu.',
                'gift_card': GiftCardSerializer(gift_card).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def gift_card_detail(request, gift_card_id):
    """
    Gift card detayı (GET), güncelle (PATCH) veya sil (DELETE).
    
    GET: /api/gift-cards/{gift_card_id}/
    PATCH: /api/gift-cards/{gift_card_id}/
    DELETE: /api/gift-cards/{gift_card_id}/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        gift_card = GiftCard.objects.get(id=gift_card_id, tenant=tenant, is_deleted=False)
    except GiftCard.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Gift card bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Erişim kontrolü
    if request.user.is_tenant_user and request.user.tenant == tenant:
        if gift_card.customer != request.user and gift_card.customer_email != request.user.email:
            return Response({
                'success': False,
                'message': 'Bu gift card\'a erişim yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = GiftCardSerializer(gift_card)
        return Response({
            'success': True,
            'gift_card': serializer.data,
        })
    
    elif request.method == 'PATCH':
        # Sadece admin veya tenant owner
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = GiftCardCreateSerializer(gift_card, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Gift card güncellendi.',
                'gift_card': GiftCardSerializer(gift_card).data,
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Sadece admin veya tenant owner
        if not (request.user.is_owner or (request.user.is_tenant_owner and request.user.tenant == tenant)):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        gift_card.soft_delete()
        return Response({
            'success': True,
            'message': 'Gift card silindi.',
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def gift_card_validate(request):
    """
    Gift card doğrula ve bakiye kontrolü.
    
    POST: /api/gift-cards/validate/
    Body: {"code": "GC-ABC123", "order_amount": 100.00}
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = GiftCardValidateSerializer(data=request.data)
    
    if serializer.is_valid():
        code = serializer.validated_data['code']
        order_amount = Decimal(str(serializer.validated_data.get('order_amount', 0.00)))
        
        # Gift card'ı bul
        try:
            gift_card = GiftCard.objects.get(
                code=code,
                tenant=tenant,
                is_deleted=False
            )
        except GiftCard.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Gift card bulunamadı.',
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Gift card geçerliliğini kontrol et
        is_valid, message = gift_card.is_valid()
        
        if not is_valid:
            return Response({
                'success': False,
                'message': message,
                'valid': False,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # İndirim tutarını hesapla
        discount_amount = gift_card.calculate_discount(order_amount)
        final_amount = order_amount - discount_amount
        
        return Response({
            'success': True,
            'valid': True,
            'message': 'Gift card geçerli.',
            'gift_card': {
                'id': str(gift_card.id),
                'code': gift_card.code,
                'type': gift_card.type,
                'current_amount': str(gift_card.current_amount),
                'initial_amount': str(gift_card.initial_amount),
            },
            'discount': {
                'discount_amount': str(discount_amount),
                'order_amount': str(order_amount),
                'final_amount': str(final_amount),
            },
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'errors': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gift_card_balance(request, gift_card_id):
    """
    Gift card bakiye kontrolü.
    
    GET: /api/gift-cards/{gift_card_id}/balance/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        gift_card = GiftCard.objects.get(id=gift_card_id, tenant=tenant, is_deleted=False)
    except GiftCard.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Gift card bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Erişim kontrolü
    if request.user.is_tenant_user and request.user.tenant == tenant:
        if gift_card.customer != request.user and gift_card.customer_email != request.user.email:
            return Response({
                'success': False,
                'message': 'Bu gift card\'a erişim yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
    
    is_valid, message = gift_card.is_valid()
    
    return Response({
        'success': True,
        'gift_card': {
            'code': gift_card.code,
            'type': gift_card.type,
            'initial_amount': str(gift_card.initial_amount),
            'current_amount': str(gift_card.current_amount),
            'status': gift_card.status,
        },
        'is_valid': is_valid,
        'message': message,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gift_card_transactions(request, gift_card_id):
    """
    Gift card işlem geçmişi.
    
    GET: /api/gift-cards/{gift_card_id}/transactions/
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        gift_card = GiftCard.objects.get(id=gift_card_id, tenant=tenant, is_deleted=False)
    except GiftCard.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Gift card bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Erişim kontrolü
    if request.user.is_tenant_user and request.user.tenant == tenant:
        if gift_card.customer != request.user and gift_card.customer_email != request.user.email:
            return Response({
                'success': False,
                'message': 'Bu gift card\'a erişim yetkiniz yok.',
            }, status=status.HTTP_403_FORBIDDEN)
    
    transactions = GiftCardTransaction.objects.filter(
        gift_card=gift_card,
        is_deleted=False
    ).order_by('-created_at')
    
    serializer = GiftCardTransactionSerializer(transactions, many=True)
    return Response({
        'success': True,
        'transactions': serializer.data,
    }, status=status.HTTP_200_OK)

