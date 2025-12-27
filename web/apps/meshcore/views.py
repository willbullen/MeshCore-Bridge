"""
MeshCore Views
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import (
    Node, Channel, Message, Packet, NodeStats,
    BridgeConfiguration, BridgeStatus
)


def dashboard(request):
    """Main dashboard view"""
    # Get bridge status
    bridge_status = BridgeStatus.objects.first()
    if not bridge_status:
        bridge_status = BridgeStatus.objects.create()
    
    # Get node counts
    total_nodes = Node.objects.count()
    online_nodes = Node.objects.filter(is_online=True).count()
    
    # Get message counts
    total_messages = Message.objects.count()
    recent_messages = Message.objects.select_related('sender', 'recipient').order_by('-timestamp')[:10]
    
    # Get message type breakdown
    message_types = {}
    for msg_type, display in Message.MESSAGE_TYPE_CHOICES:
        count = Message.objects.filter(message_type=msg_type).count()
        if count > 0:
            message_types[display] = count
    
    context = {
        'bridge_status': bridge_status,
        'total_nodes': total_nodes,
        'online_nodes': online_nodes,
        'total_messages': total_messages,
        'recent_messages': recent_messages,
        'message_types': message_types,
    }
    return render(request, 'meshcore/dashboard.html', context)


def nodes_list(request):
    """List all nodes"""
    nodes = Node.objects.all().order_by('-last_seen')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'online':
        nodes = nodes.filter(is_online=True)
    elif status_filter == 'offline':
        nodes = nodes.filter(is_online=False)
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        nodes = nodes.filter(node_type=type_filter)
    
    context = {
        'nodes': nodes,
        'node_types': Node.NODE_TYPE_CHOICES,
    }
    return render(request, 'meshcore/nodes_list.html', context)


def node_detail(request, node_hash):
    """Node detail view"""
    node = get_object_or_404(Node, node_hash=node_hash)
    
    # Get recent messages
    sent_messages = Message.objects.filter(sender=node).order_by('-timestamp')[:20]
    received_messages = Message.objects.filter(recipient=node).order_by('-timestamp')[:20]
    
    # Get latest stats
    latest_stats = NodeStats.objects.filter(node=node).first()
    
    context = {
        'node': node,
        'sent_messages': sent_messages,
        'received_messages': received_messages,
        'latest_stats': latest_stats,
    }
    return render(request, 'meshcore/node_detail.html', context)


def messages_list(request):
    """List all messages"""
    messages = Message.objects.select_related('sender', 'recipient', 'channel').order_by('-timestamp')
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        messages = messages.filter(message_type=type_filter)
    
    # Filter by channel
    channel_id = request.GET.get('channel')
    if channel_id:
        messages = messages.filter(channel_id=channel_id)
    
    channels = Channel.objects.filter(is_active=True)
    
    context = {
        'messages': messages[:100],  # Limit to 100
        'message_types': Message.MESSAGE_TYPE_CHOICES,
        'channels': channels,
    }
    return render(request, 'meshcore/messages_list.html', context)


def channels_list(request):
    """List all channels"""
    channels = Channel.objects.all()
    
    context = {
        'channels': channels,
    }
    return render(request, 'meshcore/channels.html', context)


def map_view(request):
    """Map view showing node locations"""
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    
    nodes_with_location = Node.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    )
    
    # Prepare nodes data for JavaScript
    nodes_data = []
    for node in nodes_with_location:
        nodes_data.append({
            'node_hash': node.node_hash,
            'name': node.name or node.short_name,
            'latitude': float(node.latitude) if node.latitude else None,
            'longitude': float(node.longitude) if node.longitude else None,
            'is_online': node.is_online,
            'is_favorite': node.is_favorite,
            'hardware_model': node.node_type.title(),
            'battery_level': None,
            'snr': None,
            'last_seen_ago': node.get_last_seen_display() if hasattr(node, 'get_last_seen_display') else 'N/A',
        })
    
    # Prepare waypoints data (empty for now)
    waypoints_data = []
    
    context = {
        'nodes': nodes_with_location,
        'nodes_json': json.dumps(nodes_data, cls=DjangoJSONEncoder),
        'waypoints_json': json.dumps(waypoints_data, cls=DjangoJSONEncoder),
    }
    return render(request, 'meshcore/map.html', context)


def telemetry(request):
    """Telemetry dashboard"""
    # Get nodes with recent stats
    nodes = Node.objects.filter(is_online=True)
    telemetry_data = []
    
    for node in nodes:
        latest_stats = NodeStats.objects.filter(node=node).first()
        if latest_stats:
            telemetry_data.append({
                'node': node,
                'stats': latest_stats,
            })
    
    context = {
        'telemetry_data': telemetry_data,
    }
    return render(request, 'meshcore/telemetry.html', context)


def connections(request):
    """Connection management"""
    context = {}
    return render(request, 'meshcore/connections.html', context)


def configuration(request):
    """Bridge configuration"""
    config = BridgeConfiguration.objects.first()
    if not config:
        config = BridgeConfiguration.objects.create()
    
    if request.method == 'POST':
        # Update configuration
        config.mqtt_broker = request.POST.get('mqtt_broker', config.mqtt_broker)
        config.mqtt_port = int(request.POST.get('mqtt_port', config.mqtt_port))
        config.serial_port = request.POST.get('serial_port', config.serial_port)
        config.save()
    
    context = {
        'config': config,
    }
    return render(request, 'meshcore/configuration.html', context)


# API Views

def api_status(request):
    """API endpoint for bridge status"""
    bridge_status = BridgeStatus.objects.first()
    if not bridge_status:
        bridge_status = BridgeStatus.objects.create()
    
    return JsonResponse({
        'status': bridge_status.status,
        'serial_connected': bridge_status.serial_connected,
        'mqtt_connected': bridge_status.mqtt_connected,
        'messages_received': bridge_status.messages_received,
        'messages_published': bridge_status.messages_published,
        'uptime_seconds': bridge_status.uptime_seconds,
    })


def api_nodes(request):
    """API endpoint for nodes"""
    nodes = Node.objects.all()
    
    data = [{
        'node_hash': node.node_hash,
        'name': node.name,
        'node_type': node.node_type,
        'is_online': node.is_online,
        'latitude': node.latitude,
        'longitude': node.longitude,
        'last_seen': node.last_seen.isoformat() if node.last_seen else None,
    } for node in nodes]
    
    return JsonResponse({'nodes': data})


def api_messages(request):
    """API endpoint for messages"""
    messages = Message.objects.select_related('sender', 'recipient').order_by('-timestamp')[:50]
    
    data = [{
        'message_id': msg.message_id,
        'sender_hash': msg.sender_hash,
        'recipient_hash': msg.recipient_hash,
        'message_type': msg.message_type,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat(),
    } for msg in messages]
    
    return JsonResponse({'messages': data})


def flasher(request):
    """Firmware flasher page"""
    return render(request, 'meshcore/flasher.html')
