"""
Traefik service.
Traefik File Provider ile domain routing yönetimi.
"""
import os
import yaml
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class TraefikService:
    """Traefik routing yönetim servisi."""
    
    @staticmethod
    def get_dynamic_config_path():
        """Traefik dynamic config dosya yolu."""
        config_path = getattr(
            settings, 
            'TRAEFIK_DYNAMIC_CONFIG_PATH', 
            '/app/traefik/dynamic/routing.yaml'
        )
        # Eğer relative path ise, BASE_DIR'e göre ayarla
        if not os.path.isabs(config_path):
            from django.conf import settings as django_settings
            base_dir = getattr(django_settings, 'BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, '..', config_path.lstrip('/'))
            config_path = os.path.abspath(config_path)
        
        # Dizin yoksa oluştur
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        return config_path
    
    @staticmethod
    def load_dynamic_config():
        """Mevcut dynamic config'i yükle."""
        config_path = TraefikService.get_dynamic_config_path()
        
        if not os.path.exists(config_path):
            return {
                'http': {
                    'routers': {},
                    'services': {}
                }
            }
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                if 'http' not in config:
                    config['http'] = {'routers': {}, 'services': {}}
                if 'routers' not in config['http']:
                    config['http']['routers'] = {}
                if 'services' not in config['http']:
                    config['http']['services'] = {}
                return config
        except Exception as e:
            logger.error(f"Failed to load Traefik config: {str(e)}")
            return {
                'http': {
                    'routers': {},
                    'services': {}
                }
            }
    
    @staticmethod
    def save_dynamic_config(config):
        """Dynamic config'i kaydet."""
        config_path = TraefikService.get_dynamic_config_path()
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            logger.info(f"Traefik config saved to: {config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save Traefik config: {str(e)}")
            return False
    
    @staticmethod
    def add_domain_route(domain):
        """
        Traefik'e domain routing ekle (file-based).
        """
        # Router name
        router_name = f"router-{domain.domain_name.replace('.', '-')}"
        domain.traefik_router_name = router_name
        
        # Service name
        service_name = f"service-{domain.tenant.subdomain}"
        domain.traefik_service_name = service_name
        domain.save()
        
        # Mevcut config'i yükle
        config = TraefikService.load_dynamic_config()
        
        # Router ekle
        router_config = {
            'rule': f"Host(`{domain.domain_name}`)",
            'service': service_name,
            'entryPoints': ['web'],
        }
        
        # SSL aktifse TLS ekle
        if domain.ssl_enabled:
            router_config['tls'] = {
                'certResolver': 'letsencrypt'
            }
        
        config['http']['routers'][router_name] = router_config
        
        # Service ekle (eğer yoksa)
        if service_name not in config['http']['services']:
            config['http']['services'][service_name] = {
                'loadBalancer': {
                    'servers': [
                        {
                            'url': f"http://frontend-{domain.tenant.subdomain}:3000"
                        }
                    ]
                }
            }
        
        # Config'i kaydet
        if TraefikService.save_dynamic_config(config):
            logger.info(f"Traefik route added for: {domain.domain_name}")
            return True
        else:
            logger.error(f"Failed to add Traefik route for: {domain.domain_name}")
            return False
    
    @staticmethod
    def remove_domain_route(domain):
        """
        Traefik'ten domain routing'i kaldır.
        """
        if not domain.traefik_router_name:
            logger.warning(f"No router name for domain: {domain.domain_name}")
            return False
        
        # Mevcut config'i yükle
        config = TraefikService.load_dynamic_config()
        
        # Router'ı kaldır
        router_name = domain.traefik_router_name
        if router_name in config['http']['routers']:
            del config['http']['routers'][router_name]
            logger.info(f"Router removed: {router_name}")
        
        # Service'i kontrol et - başka router kullanıyorsa kaldırma
        service_name = domain.traefik_service_name
        if service_name:
            # Bu service'i kullanan başka router var mı?
            service_in_use = any(
                router.get('service') == service_name
                for router in config['http']['routers'].values()
            )
            
            if not service_in_use and service_name in config['http']['services']:
                del config['http']['services'][service_name]
                logger.info(f"Service removed: {service_name}")
        
        # Config'i kaydet
        if TraefikService.save_dynamic_config(config):
            logger.info(f"Traefik route removed for: {domain.domain_name}")
            return True
        else:
            logger.error(f"Failed to remove Traefik route for: {domain.domain_name}")
            return False
    
    @staticmethod
    def update_domain_route(domain):
        """
        Domain routing'i güncelle.
        """
        # Önce kaldır, sonra ekle
        TraefikService.remove_domain_route(domain)
        return TraefikService.add_domain_route(domain)

