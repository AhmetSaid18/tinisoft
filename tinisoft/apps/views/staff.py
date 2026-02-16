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
        
        # Debug: Permission değişikliği takibi
        old_perms = list(staff.staff_permissions or [])
        new_perms_in_request = request.data.get('staff_permissions', 'NOT_SENT')
        logger.info(
            f"[STAFF_UPDATE] PATCH staff | Staff: {staff.email} | "
            f"By: {request.user.email} | "
            f"Old perms: {old_perms} | "
            f"New perms in request: {new_perms_in_request} | "
            f"Full request data keys: {list(request.data.keys())}"
        )
            
        serializer = UserSerializer(staff, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Kaydedildikten sonra kontrol et
            staff.refresh_from_db()
            logger.info(
                f"[STAFF_UPDATE] PATCH staff SAVED | Staff: {staff.email} | "
                f"Saved perms in DB: {staff.staff_permissions}"
            )
            
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
        # Security: Require password confirmation for staff deletion
        # This prevents unauthorized deletion from hijacked sessions
        password = request.data.get('password')
        if not password:
             return Response({
                'success': False,
                'message': 'Güvenlik gereği personel silmek için şifrenizi girmelisiniz.',
                'error_code': 'PASSWORD_REQUIRED'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not request.user.check_password(password):
            logger.warning(f"Failed stuff deletion attempt (invalid password) by {request.user.email} for staff {staff.email}")
            return Response({
                'success': False,
                'message': 'Girdiğiniz şifre yanlış.',
                'error_code': 'INVALID_PASSWORD'
            }, status=status.HTTP_403_FORBIDDEN)

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
