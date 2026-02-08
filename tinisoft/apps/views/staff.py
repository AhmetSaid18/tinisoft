"""
Staff management views for Tenant Owners.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.models import User
from apps.serializers.auth import TenantStaffSerializer, UserSerializer
from apps.permissions import IsTenantOwner, HasStaffPermission
from core.middleware import get_tenant_from_request
from apps.services.activity_log_service import ActivityLogService
import logging

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasStaffPermission])
def staff_list_create(request):
    """
    Mağaza personeli listesi (GET) veya yeni personel oluştur (POST).
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        staff = User.objects.filter(tenant=tenant, role=User.UserRole.TENANT_STAFF)
        serializer = UserSerializer(staff, many=True)
        return Response({
            'success': True,
            'staff': serializer.data,
        })
    
    elif request.method == 'POST':
        serializer = TenantStaffSerializer(data=request.data, context={'tenant': tenant})
        if serializer.is_valid():
            user = serializer.save()
            
            # Activity Log
            ActivityLogService.log(
                tenant=tenant,
                user=request.user,
                action="staff_create",
                description=f"Yeni personel oluşturuldu: {user.email}",
                content_type="User",
                object_id=user.id,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({
                'success': True,
                'message': 'Personel oluşturuldu.',
                'staff': UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Personel oluşturulamadı.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, HasStaffPermission])
def staff_detail(request, staff_id):
    """
    Personel detayı veya silme.
    """
    tenant = get_tenant_from_request(request)
    try:
        staff = User.objects.get(id=staff_id, tenant=tenant, role=User.UserRole.TENANT_STAFF)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Personel bulunamadı.',
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = UserSerializer(staff)
        return Response({
            'success': True,
            'staff': serializer.data,
        })
    
    elif request.method == 'PATCH':
        # Şifre güncelleme varsa ayrıca ele alınmalı
        password = request.data.get('password')
        if password:
            staff.set_password(password)
            staff.save()
            logger.info(f"Staff password updated for: {staff.email} by {request.user.email}")
            
        serializer = UserSerializer(staff, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Activity Log
            ActivityLogService.log(
                tenant=tenant,
                user=request.user,
                action="staff_update",
                description=f"Personel bilgileri güncellendi: {staff.email}{' (Şifre dahil)' if password else ''}",
                content_type="User",
                object_id=staff.id,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({
                'success': True,
                'message': 'Personel güncellendi.',
                'staff': serializer.data,
            })
        
        return Response({
            'success': False,
            'message': 'Güncelleme başarısız.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        email = staff.email
        staff.delete()
        
        # Activity Log
        ActivityLogService.log(
            tenant=tenant,
            user=request.user,
            action="staff_delete",
            description=f"Personel silindi: {email}",
            content_type="User",
            object_id=staff_id,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'success': True,
            'message': 'Personel silindi.',
        })

# Set staff permissions
staff_list_create.cls.staff_permission = 'staff'
staff_detail.cls.staff_permission = 'staff'
