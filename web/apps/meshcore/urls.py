from django.urls import path
from . import views
from .views_multimedia import (media_gallery, upload_image, upload_voice, 
                                media_detail, send_media, delete_media, 
                                api_media_status, create_gallery, gallery_detail)

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
    
    # API endpoints
    path('api/status/', views.api_status, name='api_status'),
    path('api/nodes/', views.api_nodes, name='api_nodes'),
    path('api/messages/', views.api_messages, name='api_messages'),
    
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
