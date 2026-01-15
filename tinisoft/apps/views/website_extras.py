"""
Website Extras Views
Form Builder, Popup, URL Redirects, Template Revisions, Preview Mode
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.models.website import (
    WebsiteTemplate, CustomForm, FormSubmission,
    Popup, URLRedirect, TemplateRevision
)
from apps.serializers.website_extras import (
    CustomFormSerializer, FormSubmissionSerializer,
    PopupSerializer, PublicPopupSerializer,
    URLRedirectSerializer, TemplateRevisionSerializer
)
from apps.permissions import IsTenantUser


# ================================
# FORM BUILDER
# ================================

class FormListCreateView(APIView):
    """GET, POST /api/v1/tenant/website/forms/"""
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def get(self, request):
        """List all forms"""
        tenant = request.user.tenant
        template = get_object_or_404(WebsiteTemplate, tenant=tenant)
        forms = template.custom_forms.all()
        serializer = CustomFormSerializer(forms, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create new form"""
        tenant = request.user.tenant
        template, _ = WebsiteTemplate.objects.get_or_create(tenant=tenant)
        
        serializer = CustomFormSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(template=template)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FormDetailView(APIView):
    """GET, PUT, DELETE /api/v1/tenant/website/forms/{id}/"""
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def get_form(self, request, form_id):
        tenant = request.user.tenant
        template = get_object_or_404(WebsiteTemplate, tenant=tenant)
        return get_object_or_404(CustomForm, id=form_id, template=template)
    
    def get(self, request, form_id):
        form = self.get_form(request, form_id)
        serializer = CustomFormSerializer(form)
        return Response(serializer.data)
    
    def put(self, request, form_id):
        form = self.get_form(request, form_id)
        serializer = CustomFormSerializer(form, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, form_id):
        form = self.get_form(request, form_id)
        form.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FormSubmitView(APIView):
    """POST /api/v1/public/forms/{slug}/submit/"""
    permission_classes = [AllowAny]
    
    def post(self, request, slug):
        """Public form submit endpoint"""
        tenant_slug = request.headers.get('X-Tenant-Slug')
        if not tenant_slug:
            return Response({"error": "X-Tenant-Slug header required"}, status=400)
        
        form = get_object_or_404(
            CustomForm,
            slug=slug,
            template__tenant__slug=tenant_slug,
            is_active=True
        )
        
        # Save submission
        submission = FormSubmission.objects.create(
            form=form,
            data=request.data,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            "message": "Form başarıyla gönderildi.",
            "submission_id": submission.id
        }, status=status.HTTP_201_CREATED)


class FormSubmissionsView(APIView):
    """GET /api/v1/tenant/website/forms/{id}/submissions/"""
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def get(self, request, form_id):
        """Get form submissions"""
        tenant = request.user.tenant
        template = get_object_or_404(WebsiteTemplate, tenant=tenant)
        form = get_object_or_404(CustomForm, id=form_id, template=template)
        
        submissions = form.submissions.all()
        serializer = FormSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)


# ================================
# POPUP BUILDER
# ================================

class PopupListCreateView(APIView):
    """GET, POST /api/v1/tenant/website/popups/"""
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def get(self, request):
        tenant = request.user.tenant
        template = get_object_or_404(WebsiteTemplate, tenant=tenant)
        popups = template.popups.all()
        serializer = PopupSerializer(popups, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        tenant = request.user.tenant
        template, _ = WebsiteTemplate.objects.get_or_create(tenant=tenant)
        
        serializer = PopupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(template=template)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PopupDetailView(APIView):
    """GET, PUT, DELETE /api/v1/tenant/website/popups/{id}/"""
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def get_popup(self, request, popup_id):
        tenant = request.user.tenant
        template = get_object_or_404(WebsiteTemplate, tenant=tenant)
        return get_object_or_404(Popup, id=popup_id, template=template)
    
    def get(self, request, popup_id):
        popup = self.get_popup(request, popup_id)
        serializer = PopupSerializer(popup)
        return Response(serializer.data)
    
    def put(self, request, popup_id):
        popup = self.get_popup(request, popup_id)
        serializer = PopupSerializer(popup, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, popup_id):
        popup = self.get_popup(request, popup_id)
        popup.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicPopupsView(APIView):
    """GET /api/v1/public/popups/ - Storefront için aktif popups"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        tenant_slug = request.headers.get('X-Tenant-Slug')
        if not tenant_slug:
            return Response({"error": "X-Tenant-Slug header required"}, status=400)
        
        popups = Popup.objects.filter(
            template__tenant__slug=tenant_slug,
            is_active=True
        ).order_by('-priority')
        
        serializer = PublicPopupSerializer(popups, many=True)
        return Response(serializer.data)


# ================================
# URL REDIRECTS
# ================================

class URLRedirectListCreateView(APIView):
    """GET, POST /api/v1/tenant/website/redirects/"""
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def get(self, request):
        tenant = request.user.tenant
        template = get_object_or_404(WebsiteTemplate, tenant=tenant)
        redirects = template.url_redirects.all()
        serializer = URLRedirectSerializer(redirects, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        tenant = request.user.tenant
        template, _ = WebsiteTemplate.objects.get_or_create(tenant=tenant)
        
        serializer = URLRedirectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(template=template)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class URLRedirectDetailView(APIView):
    """GET, PUT, DELETE /api/v1/tenant/website/redirects/{id}/"""
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def get_redirect(self, request, redirect_id):
        tenant = request.user.tenant
        template = get_object_or_404(WebsiteTemplate, tenant=tenant)
        return get_object_or_404(URLRedirect, id=redirect_id, template=template)
    
    def get(self, request, redirect_id):
        redirect = self.get_redirect(request, redirect_id)
        serializer = URLRedirectSerializer(redirect)
        return Response(serializer.data)
    
    def put(self, request, redirect_id):
        redirect = self.get_redirect(request, redirect_id)
        serializer = URLRedirectSerializer(redirect, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, redirect_id):
        redirect = self.get_redirect(request, redirect_id)
        redirect.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ================================
# TEMPLATE REVISIONS
# ================================

class TemplateRevisionListView(APIView):
    """GET /api/v1/tenant/website/template/revisions/"""
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def get(self, request):
        """List template revisions"""
        tenant = request.user.tenant
        template = get_object_or_404(WebsiteTemplate, tenant=tenant)
        revisions = template.revisions.all()[:20]  # Son 20 revizyon
        serializer = TemplateRevisionSerializer(revisions, many=True)
        return Response(serializer.data)


class TemplateRevisionRestoreView(APIView):
    """POST /api/v1/tenant/website/template/revisions/{id}/restore/"""
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def post(self, request, revision_id):
        """Restore template to a previous revision"""
        tenant = request.user.tenant
        template = get_object_or_404(WebsiteTemplate, tenant=tenant)
        revision = get_object_or_404(TemplateRevision, id=revision_id, template=template)
        
        # Restore from snapshot
        snapshot = revision.snapshot
        for key, value in snapshot.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.save()
        
        # Create new revision for this restore
        TemplateRevision.objects.create(
            template=template,
            snapshot=snapshot,
            note=f"Restored from {revision.created_at.strftime('%Y-%m-%d %H:%M')}",
            created_by=request.user
        )
        
        return Response({"message": "Template restored successfully"})


# ================================
# PREVIEW MODE
# ================================

class EnablePreviewModeView(APIView):
    """POST /api/v1/tenant/website/template/preview/enable/"""
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def post(self, request):
        """Enable preview mode and generate token"""
        tenant = request.user.tenant
        template = get_object_or_404(WebsiteTemplate, tenant=tenant)
        
        template.preview_mode = True
        if not template.preview_token:
            template.generate_preview_token()
        template.save()
        
        return Response({
            "preview_mode": True,
            "preview_url": template.get_preview_url(),
            "preview_token": template.preview_token
        })


class DisablePreviewModeView(APIView):
    """POST /api/v1/tenant/website/template/preview/disable/"""
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def post(self, request):
        """Disable preview mode"""
        tenant = request.user.tenant
        template = get_object_or_404(WebsiteTemplate, tenant=tenant)
        
        template.preview_mode = False
        template.save()
        
        return Response({"preview_mode": False})


class PreviewTemplateView(APIView):
    """GET /api/v1/preview/{token}/ - Public preview endpoint"""
    permission_classes = [AllowAny]
    
    def get(self, request, token):
        """View template in preview mode"""
        template = get_object_or_404(WebsiteTemplate, preview_token=token, preview_mode=True)
        
        from apps.serializers.website import PublicWebsiteTemplateSerializer
        serializer = PublicWebsiteTemplateSerializer(template)
        
        return Response({
            "preview": True,
            "data": serializer.data
        })


# ================================
# PUBLISH & SYSTEM
# ================================

class PublishTemplateView(APIView):
    """POST /api/v1/tenant/website/template/publish/"""
    permission_classes = [IsAuthenticated, IsTenantUser]
    
    def post(self, request):
        """Draft değişikliklerini canlıya al (Publish)"""
        tenant = request.user.tenant
        template = get_object_or_404(WebsiteTemplate, tenant=tenant)
        
        # 1. Draft -> Live Kopyala
        template.publish_changes()
        
        # 2. Revizyon Oluştur (Snapshot al)
        from apps.models.website import TemplateRevision
        snapshot = {
            'homepage_config': template.homepage_config,
            'theme_config': template.theme_config,
            'custom_css': template.custom_css,
            # ... diğer önemli alanlar
        }
        
        TemplateRevision.objects.create(
            template=template,
            snapshot=snapshot,
            note=f"Published by {request.user.email}",
            created_by=request.user
        )
        
        # 3. Cache Temizle
        template.invalidate_cache()
        
        return Response({"message": "Website başarıyla yayınlandı!"})


class SystemFontsView(APIView):
    """GET /api/v1/system/fonts/"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Kullanılabilir Google Fontları"""
        fonts = [
            {"family": "Inter", "category": "sans-serif"},
            {"family": "Roboto", "category": "sans-serif"},
            {"family": "Open Sans", "category": "sans-serif"},
            {"family": "Lato", "category": "sans-serif"},
            {"family": "Montserrat", "category": "sans-serif"},
            {"family": "Poppins", "category": "sans-serif"},
            {"family": "Playfair Display", "category": "serif"},
            {"family": "Merriweather", "category": "serif"},
            {"family": "Lora", "category": "serif"},
            {"family": "Oswald", "category": "sans-serif"},
        ]
        return Response(fonts)
