"""
URL configuration for Tinisoft project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.views.welcome import welcome_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.urls')),
    path('welcome/', welcome_page, name='welcome'),  # Welcome page
    path('', welcome_page, name='welcome_root'),  # Root'ta da welcome göster
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

