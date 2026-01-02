# Migration for updated BridgeConfiguration model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meshcore', '0003_deviceconnection_bridgestatus_rak4631_connected'),
    ]

    operations = [
        # Update existing fields
        migrations.AlterField(
            model_name='bridgeconfiguration',
            name='mqtt_broker',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='bridgeconfiguration',
            name='serial_port',
            field=models.CharField(blank=True, default='', help_text='COM3, COM4 (Windows) or /dev/ttyACM0 (Linux)', max_length=255),
        ),
        
        # Add new fields
        migrations.AddField(
            model_name='bridgeconfiguration',
            name='mqtt_enabled',
            field=models.BooleanField(default=False, help_text='Enable MQTT connection'),
        ),
        migrations.AddField(
            model_name='bridgeconfiguration',
            name='serial_enabled',
            field=models.BooleanField(default=False, help_text='Enable serial connection'),
        ),
        migrations.AddField(
            model_name='bridgeconfiguration',
            name='mqtt_connected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='bridgeconfiguration',
            name='mqtt_last_test',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='bridgeconfiguration',
            name='mqtt_last_error',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='bridgeconfiguration',
            name='serial_connected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='bridgeconfiguration',
            name='serial_last_test',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='bridgeconfiguration',
            name='serial_last_error',
            field=models.TextField(blank=True),
        ),
    ]
