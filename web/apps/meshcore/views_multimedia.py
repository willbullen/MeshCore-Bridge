"""
MeshCore Multimedia Views
Handles image upload/gallery and voice recording
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile
from .models import Node
from .models_multimedia import MediaFile, MediaGallery, MultiPartPacket
import uuid
import json
from datetime import datetime


def media_gallery(request):
    """Media gallery view showing all images and voice messages"""
    images = MediaFile.objects.filter(media_type='image').order_by('-created_at')
    voice_messages = MediaFile.objects.filter(media_type='voice').order_by('-created_at')
    galleries = MediaGallery.objects.all()
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        images = images.filter(status=status_filter)
        voice_messages = voice_messages.filter(status=status_filter)
    
    context = {
        'images': images,
        'voice_messages': voice_messages,
        'galleries': galleries,
        'status_filter': status_filter,
    }
    return render(request, 'meshcore/media_gallery.html', context)


@require_http_methods(["POST"])
def upload_image(request):
    """Handle image upload"""
    if 'image' not in request.FILES:
        return JsonResponse({'error': 'No image file provided'}, status=400)
    
    image_file = request.FILES['image']
    recipient_hash = request.POST.get('recipient')
    channel_hash = request.POST.get('channel', '')
    
    # Get sender node (for demo, use first node)
    sender = Node.objects.first()
    if not sender:
        return JsonResponse({'error': 'No nodes available'}, status=400)
    
    # Get recipient if specified
    recipient = None
    if recipient_hash:
        try:
            recipient = Node.objects.get(node_hash=recipient_hash)
        except Node.DoesNotExist:
            return JsonResponse({'error': 'Recipient not found'}, status=404)
    
    # Create media file record
    file_id = uuid.uuid4().hex[:16]
    session_id = int(datetime.now().timestamp() * 1000) % (2**31)  # 32-bit session ID
    
    media_file = MediaFile.objects.create(
        file_id=file_id,
        session_id=session_id,
        media_type='image',
        filename=image_file.name,
        original_size=image_file.size,
        sender=sender,
        recipient=recipient,
        channel_hash=channel_hash,
        status='uploading',
        original_file=image_file,
    )
    
    return JsonResponse({
        'success': True,
        'file_id': file_id,
        'session_id': session_id,
        'filename': image_file.name,
        'size': image_file.size,
    })


@require_http_methods(["POST"])
def upload_voice(request):
    """Handle voice message upload"""
    if 'voice' not in request.FILES:
        return JsonResponse({'error': 'No voice file provided'}, status=400)
    
    voice_file = request.FILES['voice']
    recipient_hash = request.POST.get('recipient')
    channel_hash = request.POST.get('channel', '')
    duration = request.POST.get('duration', 0)
    
    # Get sender node
    sender = Node.objects.first()
    if not sender:
        return JsonResponse({'error': 'No nodes available'}, status=400)
    
    # Get recipient if specified
    recipient = None
    if recipient_hash:
        try:
            recipient = Node.objects.get(node_hash=recipient_hash)
        except Node.DoesNotExist:
            return JsonResponse({'error': 'Recipient not found'}, status=404)
    
    # Create media file record
    file_id = uuid.uuid4().hex[:16]
    session_id = int(datetime.now().timestamp() * 1000) % (2**31)
    
    media_file = MediaFile.objects.create(
        file_id=file_id,
        session_id=session_id,
        media_type='voice',
        filename=voice_file.name,
        original_size=voice_file.size,
        sender=sender,
        recipient=recipient,
        channel_hash=channel_hash,
        status='uploading',
        original_file=voice_file,
        metadata={'duration': float(duration)},
    )
    
    return JsonResponse({
        'success': True,
        'file_id': file_id,
        'session_id': session_id,
        'filename': voice_file.name,
        'size': voice_file.size,
        'duration': duration,
    })


def media_detail(request, file_id):
    """View details of a specific media file"""
    media_file = get_object_or_404(MediaFile, file_id=file_id)
    packets = media_file.packets.all()
    
    context = {
        'media_file': media_file,
        'packets': packets,
    }
    return render(request, 'meshcore/media_detail.html', context)


@require_http_methods(["POST"])
def send_media(request, file_id):
    """Trigger sending of a media file"""
    media_file = get_object_or_404(MediaFile, file_id=file_id)
    
    # Update status to sending
    media_file.status = 'sending'
    media_file.save()
    
    # TODO: Trigger bridge to start sending packets
    # This would be handled by the bridge application
    
    return JsonResponse({
        'success': True,
        'file_id': file_id,
        'status': 'sending',
    })


@require_http_methods(["DELETE"])
def delete_media(request, file_id):
    """Delete a media file"""
    media_file = get_object_or_404(MediaFile, file_id=file_id)
    
    # Delete associated files
    if media_file.original_file:
        media_file.original_file.delete()
    if media_file.compressed_file:
        media_file.compressed_file.delete()
    if media_file.thumbnail:
        media_file.thumbnail.delete()
    
    media_file.delete()
    
    return JsonResponse({'success': True})


def api_media_status(request, file_id):
    """Get status of a media file transfer"""
    media_file = get_object_or_404(MediaFile, file_id=file_id)
    
    return JsonResponse({
        'file_id': media_file.file_id,
        'filename': media_file.filename,
        'status': media_file.status,
        'progress': media_file.progress,
        'total_packets': media_file.total_packets,
        'received_packets': media_file.received_packets,
    })


def create_gallery(request):
    """Create a new media gallery"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        # Get creator node
        creator = Node.objects.first()
        if not creator:
            return JsonResponse({'error': 'No nodes available'}, status=400)
        
        gallery = MediaGallery.objects.create(
            name=name,
            description=description,
            created_by=creator,
        )
        
        return redirect('media_gallery')
    
    return render(request, 'meshcore/create_gallery.html')


def gallery_detail(request, gallery_id):
    """View a specific gallery"""
    gallery = get_object_or_404(MediaGallery, id=gallery_id)
    
    context = {
        'gallery': gallery,
    }
    return render(request, 'meshcore/gallery_detail.html', context)
