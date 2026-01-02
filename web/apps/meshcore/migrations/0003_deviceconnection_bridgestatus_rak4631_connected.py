# Generated manually for DeviceConnection model and BridgeStatus update

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meshcore', '0002_mediafile_mediagallery_multipartpacket_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bridgestatus',
            name='rak4631_connected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='message',
            name='published_to_mqtt',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='node',
            name='hardware_model',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='node',
            name='firmware_version',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.CreateModel(
            name='DeviceConnection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_id', models.CharField(db_index=True, max_length=64, unique=True)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('connection_type', models.CharField(choices=[('serial', 'Serial (USB)'), ('bluetooth', 'Bluetooth'), ('http', 'HTTP'), ('tcp', 'TCP')], max_length=20)),
                ('connection_params', models.JSONField(default=dict, help_text='Connection parameters (port, address, etc.)')),
                ('hardware_model', models.CharField(blank=True, max_length=100)),
                ('firmware_version', models.CharField(blank=True, max_length=50)),
                ('status', models.CharField(choices=[('disconnected', 'Disconnected'), ('connecting', 'Connecting'), ('connected', 'Connected'), ('error', 'Error')], default='disconnected', max_length=20)),
                ('is_primary', models.BooleanField(default=False)),
                ('auto_connect', models.BooleanField(default=False)),
                ('is_favorite', models.BooleanField(default=False)),
                ('last_connected_at', models.DateTimeField(blank=True, null=True)),
                ('last_error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Device Connection',
                'verbose_name_plural': 'Device Connections',
                'ordering': ['-is_primary', '-last_connected_at'],
            },
        ),
    ]
