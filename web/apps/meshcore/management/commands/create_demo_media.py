from django.core.management.base import BaseCommand
from apps.meshcore.models import Node
from apps.meshcore.models_multimedia import MediaFile, MediaGallery
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Create demo multimedia files'

    def handle(self, *args, **kwargs):
        # Get nodes
        nodes = list(Node.objects.all())
        if not nodes:
            self.stdout.write(self.style.ERROR('No nodes found. Run create_demo_data first.'))
            return
        
        # Create some demo images
        images_data = [
            {'filename': 'field_site_overview.jpg', 'size': 45000, 'status': 'received'},
            {'filename': 'sensor_deployment.jpg', 'size': 38000, 'status': 'received'},
            {'filename': 'weather_station.jpg', 'size': 52000, 'status': 'sent'},
            {'filename': 'antenna_setup.jpg', 'size': 41000, 'status': 'sending', 'progress': 65},
            {'filename': 'node_installation.jpg', 'size': 47000, 'status': 'received'},
        ]
        
        created_images = []
        for i, img_data in enumerate(images_data):
            session_id = 1000000 + i
            media_file = MediaFile.objects.create(
                file_id=f'img_{session_id}',
                session_id=session_id,
                media_type='image',
                filename=img_data['filename'],
                original_size=img_data['size'],
                compressed_size=int(img_data['size'] * 0.3),  # 30% compression
                sender=random.choice(nodes),
                recipient=random.choice(nodes) if random.random() > 0.5 else None,
                status=img_data['status'],
                progress=img_data.get('progress', 100 if img_data['status'] in ['received', 'sent'] else 0),
                total_packets=int(img_data['size'] * 0.3 / 176) + 1,  # 176 bytes per packet
                received_packets=int((img_data.get('progress', 100) / 100) * (int(img_data['size'] * 0.3 / 176) + 1)),
                created_at=timezone.now() - timedelta(hours=random.randint(1, 48)),
                metadata={'resolution': '160x120', 'format': 'JPEG'},
            )
            created_images.append(media_file)
            self.stdout.write(self.style.SUCCESS(f'Created image: {img_data["filename"]}'))
        
        # Create some demo voice messages
        voice_data = [
            {'filename': 'voice_msg_001.webm', 'duration': 8.5, 'size': 1200, 'status': 'received'},
            {'filename': 'voice_msg_002.webm', 'duration': 15.2, 'size': 2100, 'status': 'received'},
            {'filename': 'voice_msg_003.webm', 'duration': 6.8, 'size': 950, 'status': 'sent'},
            {'filename': 'voice_msg_004.webm', 'duration': 22.5, 'size': 3200, 'status': 'sending', 'progress': 45},
            {'filename': 'voice_msg_005.webm', 'duration': 12.0, 'size': 1700, 'status': 'received'},
        ]
        
        for i, voice_data_item in enumerate(voice_data):
            session_id = 2000000 + i
            media_file = MediaFile.objects.create(
                file_id=f'voice_{session_id}',
                session_id=session_id,
                media_type='voice',
                filename=voice_data_item['filename'],
                original_size=voice_data_item['size'],
                compressed_size=voice_data_item['size'],  # Already compressed
                sender=random.choice(nodes),
                recipient=random.choice(nodes) if random.random() > 0.5 else None,
                status=voice_data_item['status'],
                progress=voice_data_item.get('progress', 100 if voice_data_item['status'] in ['received', 'sent'] else 0),
                total_packets=int(voice_data_item['size'] / 176) + 1,
                received_packets=int((voice_data_item.get('progress', 100) / 100) * (int(voice_data_item['size'] / 176) + 1)),
                created_at=timezone.now() - timedelta(hours=random.randint(1, 24)),
                metadata={'duration': voice_data_item['duration'], 'codec': 'WebM Opus'},
            )
            self.stdout.write(self.style.SUCCESS(f'Created voice message: {voice_data_item["filename"]} ({voice_data_item["duration"]}s)'))
        
        # Create a demo gallery
        gallery = MediaGallery.objects.create(
            name='Field Deployment 2025',
            description='Photos and voice notes from the January 2025 field deployment',
            created_by=nodes[0],
            is_public=True,
        )
        gallery.media_files.set(created_images[:3])  # Add first 3 images to gallery
        self.stdout.write(self.style.SUCCESS(f'Created gallery: {gallery.name}'))
        
        self.stdout.write(self.style.SUCCESS('\nDemo multimedia files created successfully!'))
        self.stdout.write(self.style.SUCCESS(f'Total images: {len(images_data)}'))
        self.stdout.write(self.style.SUCCESS(f'Total voice messages: {len(voice_data)}'))
        self.stdout.write(self.style.SUCCESS(f'Total galleries: 1'))
