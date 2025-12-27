"""
Management command to create demo data for MeshCore
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
import os
from apps.meshcore.models import (
    Node, Channel, Message, NodeStats, BridgeConfiguration, BridgeStatus
)


class Command(BaseCommand):
    help = 'Create demo data for MeshCore application'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Creating demo data...')
        
        # Create nodes
        nodes_data = [
            {
                'public_key': os.urandom(32),
                'node_type': 'chat',
                'name': 'Base Station',
                'short_name': 'BASE',
                'latitude': 37.7749,
                'longitude': -122.4194,
                'is_online': True,
            },
            {
                'public_key': os.urandom(32),
                'node_type': 'repeater',
                'name': 'Hilltop Repeater',
                'short_name': 'RPT1',
                'latitude': 37.8044,
                'longitude': -122.2712,
                'is_online': True,
            },
            {
                'public_key': os.urandom(32),
                'node_type': 'chat',
                'name': 'Mobile Unit 1',
                'short_name': 'MOB1',
                'latitude': 37.7849,
                'longitude': -122.4094,
                'is_online': True,
            },
            {
                'public_key': os.urandom(32),
                'node_type': 'room_server',
                'name': 'Community BBS',
                'short_name': 'BBS1',
                'latitude': 37.7649,
                'longitude': -122.4294,
                'is_online': True,
            },
            {
                'public_key': os.urandom(32),
                'node_type': 'sensor',
                'name': 'Weather Station',
                'short_name': 'WX01',
                'latitude': 37.7949,
                'longitude': -122.3994,
                'is_online': False,
            },
        ]
        
        nodes = []
        for node_data in nodes_data:
            public_key = node_data.pop('public_key')
            node_hash = format(public_key[0], '02x')
            
            node, created = Node.objects.get_or_create(
                node_hash=node_hash,
                defaults={
                    'public_key': public_key,
                    **node_data,
                    'last_seen': timezone.now() - timedelta(minutes=random.randint(1, 30)) if node_data['is_online'] else timezone.now() - timedelta(hours=2),
                }
            )
            nodes.append(node)
            self.stdout.write(f"  {'Created' if created else 'Found'} node: {node.name} (#{node.node_hash})")
        
        # Create channels
        channels_data = [
            {
                'channel_hash': 'a1',
                'shared_key': os.urandom(32),
                'name': 'General',
                'description': 'General discussion channel',
            },
            {
                'channel_hash': 'b2',
                'shared_key': os.urandom(32),
                'name': 'Emergency',
                'description': 'Emergency communications',
                'is_private': True,
            },
        ]
        
        channels = []
        for channel_data in channels_data:
            channel, created = Channel.objects.get_or_create(
                channel_hash=channel_data['channel_hash'],
                defaults=channel_data
            )
            channels.append(channel)
            self.stdout.write(f"  {'Created' if created else 'Found'} channel: {channel.name}")
        
        # Create messages
        online_nodes = [n for n in nodes if n.is_online]
        message_contents = [
            "Hello mesh!",
            "Testing MeshCore",
            "Signal strength good",
            "Anyone copy?",
            "Roger that",
            "Checking in",
            "Weather looks good",
            "Battery at 75%",
            "Moving to new location",
            "All clear here",
        ]
        
        for i in range(30):
            sender = random.choice(online_nodes)
            recipient = random.choice([n for n in online_nodes if n != sender])
            
            message = Message.objects.create(
                message_id=f"msg_{i}_{sender.node_hash}_{int(timezone.now().timestamp())}",
                checksum=format(random.randint(0, 0xFFFFFFFF), '08x'),
                sender=sender,
                sender_hash=sender.node_hash,
                recipient=recipient,
                recipient_hash=recipient.node_hash,
                message_type='txt_msg',
                txt_type='plain',
                content=random.choice(message_contents),
                timestamp=timezone.now() - timedelta(minutes=random.randint(1, 120)),
                rssi=random.randint(-120, -40),
                snr=random.uniform(-10, 10),
            )
        
        self.stdout.write(f"  Created 30 messages")
        
        # Create group messages
        for i in range(10):
            sender = random.choice(online_nodes)
            channel = random.choice(channels)
            
            message = Message.objects.create(
                message_id=f"grp_{i}_{sender.node_hash}_{int(timezone.now().timestamp())}",
                checksum=format(random.randint(0, 0xFFFFFFFF), '08x'),
                sender=sender,
                sender_hash=sender.node_hash,
                channel=channel,
                message_type='grp_txt',
                txt_type='plain',
                content=f"{sender.short_name}: {random.choice(message_contents)}",
                timestamp=timezone.now() - timedelta(minutes=random.randint(1, 120)),
                rssi=random.randint(-120, -40),
                snr=random.uniform(-10, 10),
            )
        
        self.stdout.write(f"  Created 10 group messages")
        
        # Create node stats
        for node in online_nodes:
            stats = NodeStats.objects.create(
                node=node,
                battery_mv=random.randint(3200, 4200),
                rssi=random.randint(-120, -40),
                snr=random.uniform(-5, 15),
                packets_received=random.randint(100, 1000),
                packets_sent=random.randint(50, 500),
                packets_flood_sent=random.randint(20, 200),
                packets_direct_sent=random.randint(30, 300),
                airtime_seconds=random.randint(60, 3600),
                uptime_seconds=random.randint(3600, 86400),
                tx_queue_length=random.randint(0, 10),
                free_queue_length=random.randint(10, 50),
            )
        
        self.stdout.write(f"  Created stats for {len(online_nodes)} nodes")
        
        # Create bridge configuration
        config, created = BridgeConfiguration.objects.get_or_create(
            id=1,
            defaults={
                'mqtt_broker': 'mqtt.example.com',
                'mqtt_port': 1883,
                'mqtt_topic_prefix': 'meshcore',
                'serial_port': '/dev/ttyACM0',
                'serial_baud': 115200,
            }
        )
        self.stdout.write(f"  {'Created' if created else 'Found'} bridge configuration")
        
        # Create bridge status
        status, created = BridgeStatus.objects.get_or_create(
            id=1,
            defaults={
                'status': 'running',
                'serial_connected': True,
                'mqtt_connected': True,
                'messages_received': 1247,
                'messages_published': 1247,
                'packets_processed': 1500,
                'started_at': timezone.now() - timedelta(hours=24),
                'last_message_at': timezone.now() - timedelta(minutes=2),
            }
        )
        self.stdout.write(f"  {'Created' if created else 'Found'} bridge status")
        
        self.stdout.write(self.style.SUCCESS('\nDemo data created successfully!'))
