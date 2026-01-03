"""
Show current bridge configuration
"""
from django.core.management.base import BaseCommand
from apps.meshcore.models import BridgeConfiguration


class Command(BaseCommand):
    help = 'Show current bridge configuration'

    def handle(self, *args, **options):
        config = BridgeConfiguration.objects.first()
        
        if not config:
            self.stdout.write(self.style.ERROR('No configuration found in database'))
            return
        
        self.stdout.write(self.style.SUCCESS('\n=== Bridge Configuration ===\n'))
        
        self.stdout.write(f'Serial Enabled: {config.serial_enabled}')
        self.stdout.write(f'Serial Port: {config.serial_port or "(empty)"}')
        self.stdout.write(f'Serial Baud: {config.serial_baud}')
        self.stdout.write(f'Serial Connected: {config.serial_connected}')
        
        self.stdout.write(f'\nMQTT Enabled: {config.mqtt_enabled}')
        self.stdout.write(f'MQTT Broker: {config.mqtt_broker or "(empty)"}')
        self.stdout.write(f'MQTT Port: {config.mqtt_port}')
        self.stdout.write(f'MQTT Connected: {config.mqtt_connected}')
        
        self.stdout.write(f'\nAuto Acknowledge: {config.auto_acknowledge}')
        self.stdout.write(f'Store Packets: {config.store_packets}')
        self.stdout.write(f'Forward to MQTT: {config.forward_to_mqtt}')
        
        self.stdout.write(f'\nLast Updated: {config.updated_at}')
