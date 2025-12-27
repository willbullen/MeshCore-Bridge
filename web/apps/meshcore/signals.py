"""
Signals for MeshCore app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, Node


@receiver(post_save, sender=Message)
def update_node_last_seen(sender, instance, created, **kwargs):
    """Update sender node's last_seen when a message is received"""
    if created and instance.sender:
        instance.sender.last_seen = instance.timestamp
        instance.sender.update_status()
