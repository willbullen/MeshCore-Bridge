from django.urls import path
from . import views
from .views_multimedia import (media_gallery, upload_image, upload_voice, 
                                media_detail, send_media, delete_media, 
                                api_media_status, create_gallery, gallery_detail)
from .views_device import (scan_serial_ports, scan_bluetooth_devices, 
                            create_device_connection, connect_device, 
                            disconnect_device, delete_device, test_device_connection)
from .views_config import (test_mqtt_connection, test_serial_connection,
                           save_configuration, get_configuration, reload_bridge_config,
                           get_bridge_logs)

app_name = 'meshcore'

urlpatterns = [
    # Main views
    path('', views.dashboard, name='dashboard'),
    path('nodes/', views.nodes_list, name='nodes_list'),
    path('nodes/<str:node_hash>/', views.node_detail, name='node_detail'),
    path('messages/', views.messages_list, name='messages_list'),
    path('channels/', views.channels_list, name='channels'),
    path('map/', views.map_view, name='map'),
    path('telemetry/', views.telemetry, name='telemetry'),
    path('connections/', views.connections, name='connections'),
    path('configuration/', views.configuration, name='configuration'),
    
    # Utilities
    path('flasher/', views.flasher, name='flasher'),
    
    # API endpoints
    path('api/status/', views.api_status, name='api_status'),
    path('api/nodes/', views.api_nodes, name='api_nodes'),
    path('api/messages/', views.api_messages, name='api_messages'),
    
    # Device connection APIs
    path('api/scan/serial/', scan_serial_ports, name='api_scan_serial'),
    path('api/scan/bluetooth/', scan_bluetooth_devices, name='api_scan_bluetooth'),
    path('api/device/create/', create_device_connection, name='api_create_device'),
    path('api/device/<str:device_id>/connect/', connect_device, name='api_connect_device'),
    path('api/device/<str:device_id>/disconnect/', disconnect_device, name='api_disconnect_device'),
    path('api/device/<str:device_id>/delete/', delete_device, name='api_delete_device'),
    path('api/device/<str:device_id>/test/', test_device_connection, name='api_test_device'),
    
    # Flasher helper APIs
    path('api/flasher/scan-ports/', scan_serial_ports, name='api_flasher_scan_ports'),
    
    # Configuration APIs
    path('api/config/test-mqtt/', test_mqtt_connection, name='api_test_mqtt'),
    path('api/config/test-serial/', test_serial_connection, name='api_test_serial'),
    path('api/config/save/', save_configuration, name='api_save_config'),
    path('api/config/get/', get_configuration, name='api_get_config'),
    path('api/config/reload/', reload_bridge_config, name='api_reload_config'),
    path('api/bridge/logs/', get_bridge_logs, name='api_bridge_logs'),
    
    # Multimedia
    path('media/', media_gallery, name='media_gallery'),
    path('media/upload/image/', upload_image, name='upload_image'),
    path('media/upload/voice/', upload_voice, name='upload_voice'),
    path('media/<str:file_id>/', media_detail, name='media_detail'),
    path('media/<str:file_id>/send/', send_media, name='send_media'),
    path('media/<str:file_id>/delete/', delete_media, name='delete_media'),
    path('api/media/<str:file_id>/status/', api_media_status, name='api_media_status'),
    path('gallery/create/', create_gallery, name='create_gallery'),
    path('gallery/<int:gallery_id>/', gallery_detail, name='gallery_detail'),
]
