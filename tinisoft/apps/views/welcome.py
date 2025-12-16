"""
Welcome page view.
Domain yayınlandığında gösterilecek welcome mesajı.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.models import Domain, Tenant
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def welcome_page(request, domain_name=None):
    """
    Welcome page - Domain yayınlandığında gösterilecek sayfa.
    
    URL: /welcome/ veya domain root'ta
    """
    # Domain'i bul
    domain = None
    tenant = None
    
    if domain_name:
        try:
            domain = Domain.objects.get(domain_name=domain_name, verification_status='verified')
            tenant = domain.tenant
        except Domain.DoesNotExist:
            pass
    
    # Eğer domain yoksa, request'ten domain'i al
    if not domain and request.META.get('HTTP_HOST'):
        host = request.META.get('HTTP_HOST').split(':')[0]  # Port'u kaldır
        try:
            domain = Domain.objects.get(domain_name=host, verification_status='verified')
            tenant = domain.tenant
        except Domain.DoesNotExist:
            pass
    
    if not domain or not tenant:
        return Response({
            'success': False,
            'message': 'Domain bulunamadı veya henüz yayınlanmamış.',
        }, status=404)
    
    # Welcome mesajı
    welcome_data = {
        'success': True,
        'message': '🎉 Siteniz başarıyla yayınlandı!',
        'domain': {
            'name': domain.domain_name,
            'is_primary': domain.is_primary,
            'ssl_enabled': domain.ssl_enabled,
            'verified_at': domain.verified_at.isoformat() if domain.verified_at else None,
        },
        'tenant': {
            'name': tenant.name,
            'slug': tenant.slug,
            'status': tenant.status,
            'template': tenant.template,
        },
        'welcome_message': f'Hoş geldiniz {tenant.name}!',
        'next_steps': [
            'Siteniz başarıyla yayınlandı.',
            'Frontend template yükleniyor...',
            'Yakında tam özellikli mağazanız hazır olacak!',
        ]
    }
    
    # HTML response döndür
    html_content = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{tenant.name} - Yayında!</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                padding: 40px;
                max-width: 600px;
                width: 100%;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
            }}
            .success-icon {{
                font-size: 80px;
                margin-bottom: 20px;
            }}
            h1 {{
                color: #333;
                font-size: 32px;
                margin-bottom: 10px;
            }}
            .domain-name {{
                color: #667eea;
                font-size: 24px;
                font-weight: bold;
                margin: 20px 0;
                padding: 10px;
                background: #f5f5f5;
                border-radius: 8px;
            }}
            .message {{
                color: #666;
                font-size: 18px;
                line-height: 1.6;
                margin: 20px 0;
            }}
            .steps {{
                text-align: left;
                margin: 30px 0;
                padding: 20px;
                background: #f9f9f9;
                border-radius: 10px;
            }}
            .steps li {{
                margin: 10px 0;
                color: #555;
            }}
            .status {{
                display: inline-block;
                padding: 8px 16px;
                background: #4caf50;
                color: white;
                border-radius: 20px;
                font-size: 14px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">🎉</div>
            <h1>{welcome_data['welcome_message']}</h1>
            <div class="domain-name">{domain.domain_name}</div>
            <p class="message">{welcome_data['message']}</p>
            <div class="steps">
                <ul>
                    {''.join([f'<li>{step}</li>' for step in welcome_data['next_steps']])}
                </ul>
            </div>
            <div class="status">✅ Site Aktif</div>
        </div>
    </body>
    </html>
    """
    
    return Response(html_content, content_type='text/html')

