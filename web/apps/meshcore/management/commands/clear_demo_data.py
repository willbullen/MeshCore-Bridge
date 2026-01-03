"""
Management command to clear all demo/test data
"""
from django.core.management.base import BaseCommand
from apps.meshcore.models import Node, Channel, Message, Packet, NodeStats


class Command(BaseCommand):
    help = 'Clear all demo/test data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                'This will delete ALL nodes, messages, packets, and stats from the database.'
            ))
            self.stdout.write(self.style.WARNING(
                'Run with --confirm flag to proceed: python manage.py clear_demo_data --confirm'
            ))
            return

        self.stdout.write('Clearing demo data...')
        
        # Delete in order to avoid foreign key issues
        deleted_stats = NodeStats.objects.all().delete()
        self.stdout.write(f'  Deleted {deleted_stats[0]} node stats')
        
        deleted_packets = Packet.objects.all().delete()
        self.stdout.write(f'  Deleted {deleted_packets[0]} packets')
        
        deleted_messages = Message.objects.all().delete()
        self.stdout.write(f'  Deleted {deleted_messages[0]} messages')
        
        deleted_nodes = Node.objects.all().delete()
        self.stdout.write(f'  Deleted {deleted_nodes[0]} nodes')
        
        deleted_channels = Channel.objects.all().delete()
        self.stdout.write(f'  Deleted {deleted_channels[0]} channels')
        
        self.stdout.write(self.style.SUCCESS('\nDemo data cleared successfully!'))
        self.stdout.write('Your database is now clean and ready for real mesh network data.')
