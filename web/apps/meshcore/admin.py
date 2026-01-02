from django.contrib import admin
from .models import (
    Node, Channel, Message, Packet, NodeStats,
    BridgeConfiguration, BridgeStatus, DeviceConnection
)
from .models_multimedia import MediaFile, MultiPartPacket, MediaGallery


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ['node_hash', 'name', 'node_type', 'is_online', 'last_seen']
    list_filter = ['node_type', 'is_online', 'is_favorite']
    search_fields = ['name', 'node_hash', 'short_name']
    readonly_fields = ['public_key_hex', 'created_at', 'updated_at']
    fieldsets = (
        ('Identity', {
            'fields': ('public_key', 'public_key_hex', 'node_hash', 'node_type')
        }),
        ('Information', {
            'fields': ('name', 'short_name', 'latitude', 'longitude', 'altitude')
        }),
        ('Status', {
            'fields': ('is_online', 'last_seen', 'last_advertisement')
        }),
        ('Metadata', {
            'fields': ('is_favorite', 'is_ignored', 'notes', 'created_at', 'updated_at')
        }),
    )


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel_hash', 'is_active', 'is_private']
    list_filter = ['is_active', 'is_private']
    search_fields = ['name', 'channel_hash']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender_hash', 'recipient_hash', 'message_type', 'timestamp', 'is_acknowledged']
    list_filter = ['message_type', 'txt_type', 'is_encrypted', 'is_acknowledged']
    search_fields = ['content', 'sender_hash', 'recipient_hash']
    readonly_fields = ['message_id', 'checksum', 'received_at']
    date_hierarchy = 'timestamp'


@admin.register(Packet)
class PacketAdmin(admin.ModelAdmin):
    list_display = ['payload_type', 'route_type', 'hop_count', 'received_at']
    list_filter = ['payload_type', 'route_type']
    readonly_fields = ['received_at']
    date_hierarchy = 'received_at'


@admin.register(NodeStats)
class NodeStatsAdmin(admin.ModelAdmin):
    list_display = ['node', 'battery_mv', 'packets_received', 'packets_sent', 'collected_at']
    list_filter = ['node']
    readonly_fields = ['collected_at', 'battery_percentage']
    date_hierarchy = 'collected_at'


@admin.register(BridgeConfiguration)
class BridgeConfigurationAdmin(admin.ModelAdmin):
    list_display = ['mqtt_broker', 'mqtt_port', 'serial_port', 'forward_to_mqtt']
    fieldsets = (
        ('MQTT Settings', {
            'fields': ('mqtt_broker', 'mqtt_port', 'mqtt_username', 'mqtt_password', 'mqtt_topic_prefix')
        }),
        ('Serial Connection', {
            'fields': ('serial_port', 'serial_baud')
        }),
        ('Bridge Behavior', {
            'fields': ('auto_acknowledge', 'store_packets', 'forward_to_mqtt')
        }),
        ('Filters', {
            'fields': ('ignored_node_types', 'allowed_channels')
        }),
    )


@admin.register(BridgeStatus)
class BridgeStatusAdmin(admin.ModelAdmin):
    list_display = ['status', 'serial_connected', 'mqtt_connected', 'rak4631_connected', 'messages_received', 'updated_at']
    readonly_fields = ['uptime_seconds', 'updated_at']


@admin.register(DeviceConnection)
class DeviceConnectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'device_id', 'connection_type', 'status', 'is_primary', 'auto_connect']
    list_filter = ['connection_type', 'status', 'is_primary', 'auto_connect']
    search_fields = ['name', 'device_id', 'hardware_model']
    readonly_fields = ['device_id', 'created_at', 'updated_at', 'last_connected_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('device_id', 'name', 'connection_type', 'hardware_model', 'firmware_version')
        }),
        ('Connection Parameters', {
            'fields': ('connection_params',)
        }),
        ('Status', {
            'fields': ('status', 'is_primary', 'auto_connect', 'is_favorite', 'last_error')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_connected_at')
        }),
    )


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ['filename', 'media_type', 'sender', 'status', 'progress', 'created_at']
    list_filter = ['media_type', 'status']
    search_fields = ['filename', 'file_id']
    readonly_fields = ['file_id', 'session_id', 'created_at', 'sent_at', 'received_at']
    date_hierarchy = 'created_at'


@admin.register(MultiPartPacket)
class MultiPartPacketAdmin(admin.ModelAdmin):
    list_display = ['media_file', 'packet_index', 'size', 'sent', 'acknowledged']
    list_filter = ['sent', 'acknowledged']
    readonly_fields = ['created_at', 'sent_at', 'ack_at']


@admin.register(MediaGallery)
class MediaGalleryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'is_public', 'created_at']
    list_filter = ['is_public']
    search_fields = ['name', 'description']
    filter_horizontal = ['media_files']
