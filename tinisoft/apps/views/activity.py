"""
Activity Log views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from apps.models import ActivityLog
from apps.permissions import IsTenantOwner, HasStaffPermission
from core.middleware import get_tenant_from_request
import logging

logger = logging.getLogger(__name__)


class ActivityLogPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([IsAuthenticated, HasStaffPermission])
def activity_log_list(request):
    """
    Tenant işlem loglarını listele.
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        return Response({
            'success': False,
            'message': 'Tenant bulunamadı.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    queryset = ActivityLog.objects.filter(tenant=tenant).select_related('user')
    
    # Filtreler
    user_id = request.query_params.get('user_id')
    if user_id:
        queryset = queryset.filter(user_id=user_id)
        
    action = request.query_params.get('action')
    if action:
        queryset = queryset.filter(action=action)
        
    content_type = request.query_params.get('content_type')
    if content_type:
        queryset = queryset.filter(content_type=content_type)
        
    # Pagination
    paginator = ActivityLogPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        data = []
        for log in page:
            data.append({
                'id': log.id,
                'user': {
                    'id': log.user.id if log.user else None,
                    'email': log.user.email if log.user else 'System',
                    'full_name': f"{log.user.first_name} {log.user.last_name}" if log.user else 'System',
                },
                'action': log.action,
                'description': log.description,
                'content_type': log.content_type,
                'object_id': log.object_id,
                'changes': log.changes,
                'ip_address': log.ip_address,
                'created_at': log.created_at,
            })
        return paginator.get_paginated_response(data)
    
    return Response({
        'success': True,
        'logs': [],
    })

# Set staff permissions
activity_log_list.staff_permission = 'activity'
