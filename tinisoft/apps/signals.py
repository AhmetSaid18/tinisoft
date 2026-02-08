"""
Signals for the apps module.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.models import User
from apps.services.cache_service import CacheService

@receiver([post_save, post_delete], sender=User)
def clear_user_cache(sender, instance, **kwargs):
    """
    Kullanıcı güncellendiğinde veya silindiğinde yetki cache'ini temizle.
    """
    if instance.id:
        CacheService.delete_user_permissions(instance.id)
