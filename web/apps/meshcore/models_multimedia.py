"""
MeshCore Multimedia Models
Handles images, voice messages, and multi-part file transfers
"""
from django.db import models
from django.utils import timezone
from .models import Node
import os


class MediaFile(models.Model):
    """
    Represents a multimedia file (image or voice)
    """
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('voice', 'Voice Message'),
        ('file', 'Generic File'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('receiving', 'Receiving'),
        ('received', 'Received'),
        ('failed', 'Failed'),
    ]
    
    # Identity
    file_id = models.CharField(max_length=32, unique=True, db_index=True, help_text='Unique file identifier')
    session_id = models.IntegerField(db_index=True, help_text='Multi-part session ID')
    
    # Metadata
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    filename = models.CharField(max_length=255)
    original_size = models.IntegerField(help_text='Original file size in bytes')
    compressed_size = models.IntegerField(null=True, blank=True, help_text='Compressed size in bytes')
    
    # Transfer info
    sender = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='sent_media')
    recipient = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='received_media', null=True, blank=True)
    channel_hash = models.CharField(max_length=2, blank=True, help_text='For group messages')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0, help_text='Transfer progress percentage')
    total_packets = models.IntegerField(default=0)
    received_packets = models.IntegerField(default=0)
    
    # Files
    original_file = models.FileField(upload_to='media/original/', null=True, blank=True)
    compressed_file = models.FileField(upload_to='media/compressed/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='media/thumbnails/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata JSON
    metadata = models.JSONField(default=dict, blank=True, help_text='Additional metadata (duration, resolution, etc.)')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Media File'
        verbose_name_plural = 'Media Files'
        indexes = [
            models.Index(fields=['session_id', 'status']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['media_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_media_type_display()}: {self.filename} ({self.get_status_display()})"
    
    def update_progress(self):
        """Update transfer progress percentage"""
        if self.total_packets > 0:
            self.progress = int((self.received_packets / self.total_packets) * 100)
            self.save(update_fields=['progress'])
    
    def mark_complete(self):
        """Mark file transfer as complete"""
        self.status = 'received' if self.recipient else 'sent'
        self.progress = 100
        if self.status == 'received':
            self.received_at = timezone.now()
        else:
            self.sent_at = timezone.now()
        self.save(update_fields=['status', 'progress', 'received_at', 'sent_at'])


class MultiPartPacket(models.Model):
    """
    Tracks individual packets in a multi-part transfer
    """
    media_file = models.ForeignKey(MediaFile, on_delete=models.CASCADE, related_name='packets')
    packet_index = models.IntegerField(help_text='Packet sequence number')
    data = models.BinaryField(help_text='Packet data chunk')
    size = models.IntegerField(help_text='Size of this chunk in bytes')
    
    # Status
    sent = models.BooleanField(default=False)
    acknowledged = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    ack_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['packet_index']
        unique_together = [['media_file', 'packet_index']]
        verbose_name = 'Multi-Part Packet'
        verbose_name_plural = 'Multi-Part Packets'
        indexes = [
            models.Index(fields=['media_file', 'packet_index']),
            models.Index(fields=['sent', 'acknowledged']),
        ]
    
    def __str__(self):
        return f"Packet {self.packet_index}/{self.media_file.total_packets} for {self.media_file.filename}"


class MediaGallery(models.Model):
    """
    Organizes media files into galleries/albums
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='galleries')
    media_files = models.ManyToManyField(MediaFile, related_name='galleries', blank=True)
    
    # Metadata
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Media Gallery'
        verbose_name_plural = 'Media Galleries'
    
    def __str__(self):
        return f"{self.name} ({self.media_files.count()} files)"
    
    @property
    def cover_image(self):
        """Get the first image in the gallery as cover"""
        return self.media_files.filter(media_type='image', status='received').first()
