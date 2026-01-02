"""
MeshCore Django Models
Based on MeshCore protocol specification
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta
import json


class Node(models.Model):
    """
    Represents a node in the MeshCore mesh network
    """
    NODE_TYPE_CHOICES = [
        ('chat', 'Chat Node'),
        ('repeater', 'Repeater'),
        ('room_server', 'Room Server'),
        ('sensor', 'Sensor'),
        ('companion', 'Companion'),
    ]
    
    # Identity (Ed25519)
    public_key = models.BinaryField(max_length=32, unique=True, db_index=True, help_text='Ed25519 public key')
    node_hash = models.CharField(max_length=2, db_index=True, help_text='First byte of public key (hex)')
    
    # Node information
    node_type = models.CharField(max_length=20, choices=NODE_TYPE_CHOICES, default='chat')
    name = models.CharField(max_length=255, blank=True)
    short_name = models.CharField(max_length=4, blank=True)
    
    # Location (from advertisement appdata)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    altitude = models.FloatField(null=True, blank=True)
    
    # Status
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    last_advertisement = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    is_favorite = models.BooleanField(default=False)
    is_ignored = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    hardware_model = models.CharField(max_length=100, blank=True)
    firmware_version = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Template aliases
    @property
    def battery_level(self):
        """Get battery level from latest stats"""
        latest_stats = self.stats.first()
        if latest_stats:
            return latest_stats.battery_percentage
        return None
    
    class Meta:
        ordering = ['-last_seen']
        verbose_name = 'Node'
        verbose_name_plural = 'Nodes'
        indexes = [
            models.Index(fields=['node_hash', 'is_online']),
            models.Index(fields=['node_type', 'is_online']),
        ]
    
    def __str__(self):
        return f"{self.name or self.short_name or self.node_hash} ({self.get_node_type_display()})"
    
    def update_status(self):
        """Update online status based on last_seen"""
        if self.last_seen:
            time_since = timezone.now() - self.last_seen
            self.is_online = time_since < timedelta(minutes=15)
            self.save(update_fields=['is_online'])
    
    @property
    def public_key_hex(self):
        """Return public key as hex string"""
        return self.public_key.hex() if self.public_key else None


class Channel(models.Model):
    """
    Represents a group channel with shared encryption key
    """
    # Channel identity
    channel_hash = models.CharField(max_length=2, unique=True, db_index=True, help_text='First byte of SHA256(shared_key)')
    shared_key = models.BinaryField(max_length=32, help_text='Shared encryption key for channel')
    
    # Channel info
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_private = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Channel'
        verbose_name_plural = 'Channels'
    
    def __str__(self):
        return f"{self.name} (#{self.channel_hash})"


class Message(models.Model):
    """
    Represents a message in the MeshCore network
    """
    MESSAGE_TYPE_CHOICES = [
        ('txt_msg', 'Text Message'),
        ('grp_txt', 'Group Text'),
        ('req', 'Request'),
        ('response', 'Response'),
        ('ack', 'Acknowledgment'),
        ('anon_req', 'Anonymous Request'),
    ]
    
    TXT_TYPE_CHOICES = [
        ('plain', 'Plain Text'),
        ('cli', 'CLI Command'),
        ('signed', 'Signed Text'),
    ]
    
    # Message identity
    message_id = models.CharField(max_length=64, unique=True, db_index=True)
    checksum = models.CharField(max_length=8, db_index=True, help_text='CRC32 checksum')
    
    # Routing
    sender = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='sent_messages', null=True, blank=True)
    sender_hash = models.CharField(max_length=2, db_index=True)
    recipient = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    recipient_hash = models.CharField(max_length=2, db_index=True, blank=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    
    # Message content
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES)
    txt_type = models.CharField(max_length=20, choices=TXT_TYPE_CHOICES, default='plain')
    content = models.TextField()
    timestamp = models.DateTimeField(db_index=True)
    
    # Message metadata
    attempt_number = models.IntegerField(default=0)
    is_encrypted = models.BooleanField(default=True)
    is_acknowledged = models.BooleanField(default=False)
    published_to_mqtt = models.BooleanField(default=False)
    
    # Reception info
    received_at = models.DateTimeField(auto_now_add=True)
    rssi = models.IntegerField(null=True, blank=True)
    snr = models.FloatField(null=True, blank=True)
    
    # Aliases for template compatibility
    @property
    def text_content(self):
        """Alias for content field"""
        return self.content
    
    @property
    def rx_time(self):
        """Alias for received_at field"""
        return self.received_at
    
    @property
    def to_node(self):
        """Alias for recipient field"""
        return self.recipient
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['sender_hash', 'timestamp']),
            models.Index(fields=['recipient_hash', 'timestamp']),
            models.Index(fields=['message_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.sender_hash} → {self.recipient_hash or 'broadcast'}: {self.content[:50]}"


class Packet(models.Model):
    """
    Represents a raw packet received/sent in the network
    """
    ROUTE_TYPE_CHOICES = [
        ('flood', 'Flood'),
        ('direct', 'Direct'),
        ('transport_flood', 'Transport Flood'),
        ('transport_direct', 'Transport Direct'),
    ]
    
    PAYLOAD_TYPE_CHOICES = [
        ('req', 'Request'),
        ('response', 'Response'),
        ('txt_msg', 'Text Message'),
        ('ack', 'Acknowledgment'),
        ('advert', 'Advertisement'),
        ('grp_txt', 'Group Text'),
        ('grp_data', 'Group Data'),
        ('anon_req', 'Anonymous Request'),
        ('path', 'Path'),
        ('trace', 'Trace'),
        ('multipart', 'Multipart'),
        ('control', 'Control'),
        ('raw_custom', 'Raw Custom'),
    ]
    
    # Packet header
    route_type = models.CharField(max_length=20, choices=ROUTE_TYPE_CHOICES)
    payload_type = models.CharField(max_length=20, choices=PAYLOAD_TYPE_CHOICES)
    payload_version = models.IntegerField(default=1)
    
    # Transport codes (optional)
    transport_code_1 = models.IntegerField(null=True, blank=True)
    transport_code_2 = models.IntegerField(null=True, blank=True)
    
    # Path
    path = models.JSONField(default=list, help_text='List of node hashes in path')
    hop_count = models.IntegerField(default=0)
    
    # Payload
    payload_data = models.BinaryField(help_text='Raw payload bytes')
    
    # Reception metadata
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    rssi = models.IntegerField(null=True, blank=True)
    snr = models.FloatField(null=True, blank=True)
    
    # Related message (if parsed)
    message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True, related_name='packets')
    
    class Meta:
        ordering = ['-received_at']
        verbose_name = 'Packet'
        verbose_name_plural = 'Packets'
        indexes = [
            models.Index(fields=['payload_type', 'received_at']),
            models.Index(fields=['route_type', 'received_at']),
        ]
    
    def __str__(self):
        return f"{self.get_payload_type_display()} via {self.get_route_type_display()} ({self.hop_count} hops)"


class NodeStats(models.Model):
    """
    Statistics and telemetry for a node
    """
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='stats')
    
    # Battery
    battery_mv = models.IntegerField(null=True, blank=True, help_text='Battery voltage in millivolts')
    
    # Radio metrics
    rssi = models.IntegerField(null=True, blank=True, help_text='Last RSSI value')
    snr = models.FloatField(null=True, blank=True, help_text='Last SNR value')
    
    # Packet counters
    packets_received = models.BigIntegerField(default=0)
    packets_sent = models.BigIntegerField(default=0)
    packets_flood_sent = models.BigIntegerField(default=0)
    packets_direct_sent = models.BigIntegerField(default=0)
    packets_flood_received = models.BigIntegerField(default=0)
    packets_direct_received = models.BigIntegerField(default=0)
    duplicate_packets = models.BigIntegerField(default=0)
    
    # Queue status
    tx_queue_length = models.IntegerField(default=0)
    free_queue_length = models.IntegerField(default=0)
    
    # Timing
    airtime_seconds = models.BigIntegerField(default=0, help_text='Total time transmitting')
    uptime_seconds = models.BigIntegerField(default=0, help_text='Total uptime')
    
    # Error tracking
    error_flags = models.IntegerField(default=0)
    
    # Timestamp
    collected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-collected_at']
        verbose_name = 'Node Statistics'
        verbose_name_plural = 'Node Statistics'
        indexes = [
            models.Index(fields=['node', 'collected_at']),
        ]
    
    def __str__(self):
        return f"{self.node.name or self.node.node_hash} stats at {self.collected_at}"
    
    @property
    def battery_percentage(self):
        """Estimate battery percentage from voltage"""
        if not self.battery_mv:
            return None
        # Rough LiPo estimation: 4200mV = 100%, 3000mV = 0%
        percentage = ((self.battery_mv - 3000) / 1200) * 100
        return max(0, min(100, percentage))


class BridgeConfiguration(models.Model):
    """
    Configuration for the MeshCore to MQTT bridge
    All settings are managed through the web UI
    """
    # MQTT settings
    mqtt_broker = models.CharField(max_length=255, default='', blank=True)
    mqtt_port = models.IntegerField(default=1883)
    mqtt_username = models.CharField(max_length=255, blank=True)
    mqtt_password = models.CharField(max_length=255, blank=True)
    mqtt_topic_prefix = models.CharField(max_length=255, default='meshcore')
    mqtt_enabled = models.BooleanField(default=False, help_text='Enable MQTT connection')
    
    # Serial connection (RAK4631)
    serial_port = models.CharField(max_length=255, default='', blank=True, help_text='COM3, COM4 (Windows) or /dev/ttyACM0 (Linux)')
    serial_baud = models.IntegerField(default=115200)
    serial_enabled = models.BooleanField(default=False, help_text='Enable serial connection')
    
    # Connection status
    mqtt_connected = models.BooleanField(default=False)
    mqtt_last_test = models.DateTimeField(null=True, blank=True)
    mqtt_last_error = models.TextField(blank=True)
    
    serial_connected = models.BooleanField(default=False)
    serial_last_test = models.DateTimeField(null=True, blank=True)
    serial_last_error = models.TextField(blank=True)
    
    # Bridge behavior
    auto_acknowledge = models.BooleanField(default=True)
    store_packets = models.BooleanField(default=True)
    forward_to_mqtt = models.BooleanField(default=True)
    
    # Filters
    ignored_node_types = models.JSONField(default=list, help_text='List of node types to ignore')
    allowed_channels = models.JSONField(default=list, help_text='List of channel hashes to allow (empty = all)')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bridge Configuration'
        verbose_name_plural = 'Bridge Configurations'
    
    def __str__(self):
        return f"Bridge Configuration"
    
    @property
    def mqtt_status(self):
        """Get MQTT connection status"""
        if not self.mqtt_enabled:
            return 'disabled'
        return 'connected' if self.mqtt_connected else 'disconnected'
    
    @property
    def serial_status(self):
        """Get serial connection status"""
        if not self.serial_enabled:
            return 'disabled'
        return 'connected' if self.serial_connected else 'disconnected'


# Import multimedia models
from .models_multimedia import MediaFile, MultiPartPacket, MediaGallery

class BridgeStatus(models.Model):
    """
    Current status of the bridge
    """
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('stopped', 'Stopped'),
        ('error', 'Error'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='stopped')
    
    # Connection status
    serial_connected = models.BooleanField(default=False)
    mqtt_connected = models.BooleanField(default=False)
    rak4631_connected = models.BooleanField(default=False)
    
    # Counters
    messages_received = models.BigIntegerField(default=0)
    messages_published = models.BigIntegerField(default=0)
    packets_processed = models.BigIntegerField(default=0)
    errors = models.BigIntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    last_error = models.TextField(blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bridge Status'
        verbose_name_plural = 'Bridge Status'
    
    def __str__(self):
        return f"Bridge: {self.get_status_display()}"
    
    @property
    def uptime_seconds(self):
        """Calculate uptime in seconds"""
        if self.started_at:
            return int((timezone.now() - self.started_at).total_seconds())
        return 0


class DeviceConnection(models.Model):
    """
    Stored device connection configurations
    """
    CONNECTION_TYPE_CHOICES = [
        ('serial', 'Serial (USB)'),
        ('bluetooth', 'Bluetooth'),
        ('http', 'HTTP'),
        ('tcp', 'TCP'),
    ]
    
    STATUS_CHOICES = [
        ('disconnected', 'Disconnected'),
        ('connecting', 'Connecting'),
        ('connected', 'Connected'),
        ('error', 'Error'),
    ]
    
    # Basic info
    device_id = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255, blank=True)
    connection_type = models.CharField(max_length=20, choices=CONNECTION_TYPE_CHOICES)
    
    # Connection details (stored as JSON for flexibility)
    connection_params = models.JSONField(default=dict, help_text='Connection parameters (port, address, etc.)')
    
    # Hardware info
    hardware_model = models.CharField(max_length=100, blank=True)
    firmware_version = models.CharField(max_length=50, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disconnected')
    is_primary = models.BooleanField(default=False)
    auto_connect = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    
    # Metadata
    last_connected_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary', '-last_connected_at']
        verbose_name = 'Device Connection'
        verbose_name_plural = 'Device Connections'
    
    def __str__(self):
        return f"{self.name or self.device_id} ({self.get_connection_type_display()})"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary device
        if self.is_primary:
            DeviceConnection.objects.filter(is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
