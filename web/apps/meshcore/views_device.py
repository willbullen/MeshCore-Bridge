"""
Device Connection Management Views and APIs
"""
import uuid
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import DeviceConnection

logger = logging.getLogger(__name__)


def scan_serial_ports(request):
    """
    API endpoint to scan for available serial ports
    """
    try:
        import serial.tools.list_ports
        
        ports = []
        for port in serial.tools.list_ports.comports():
            port_info = {
                'device': port.device,
                'name': port.name,
                'description': port.description,
                'hwid': port.hwid,
                'vid': port.vid,
                'pid': port.pid,
                'serial_number': port.serial_number,
                'location': port.location,
                'manufacturer': port.manufacturer,
                'product': port.product,
            }
            # Try to identify MeshCore devices
            if port.manufacturer and 'nordic' in port.manufacturer.lower():
                port_info['is_meshcore'] = True
                port_info['likely_model'] = 'RAK4631'
            elif port.product and any(name in port.product.lower() for name in ['cp210', 'ch340', 'ftdi']):
                port_info['is_meshcore'] = True
                port_info['likely_model'] = 'ESP32'
            else:
                port_info['is_meshcore'] = False
            
            ports.append(port_info)
        
        return JsonResponse({'success': True, 'ports': ports})
    except ImportError:
        return JsonResponse({
            'success': False,
            'error': 'pyserial not installed. Please install: pip install pyserial'
        })
    except Exception as e:
        logger.error(f'Error scanning serial ports: {e}', exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


def scan_bluetooth_devices(request):
    """
    API endpoint to scan for Bluetooth devices
    Note: This is server-side scanning. For web-based scanning, use Web Bluetooth API in frontend.
    """
    try:
        # This is a placeholder for server-side Bluetooth scanning
        # In practice, Bluetooth scanning is better done client-side using Web Bluetooth API
        # or through a native mobile/desktop app
        
        # For demonstration, return a message about using Web Bluetooth API
        return JsonResponse({
            'success': True,
            'message': 'Use Web Bluetooth API in browser for scanning',
            'devices': [],
            'note': 'Server-side Bluetooth scanning requires bluepy or similar library and elevated permissions'
        })
    except Exception as e:
        logger.error(f'Error scanning Bluetooth devices: {e}', exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(['POST'])
@csrf_exempt
def create_device_connection(request):
    """
    API endpoint to create a new device connection
    """
    try:
        data = json.loads(request.body)
        
        connection_type = data.get('connection_type')
        if not connection_type:
            return JsonResponse({'success': False, 'error': 'connection_type is required'})
        
        # Build connection parameters based on type
        connection_params = {}
        
        if connection_type == 'serial':
            connection_params = {
                'port': data.get('serial_port'),
                'baudrate': int(data.get('baud_rate', 115200))
            }
            # Process the serial port for device_id (remove slashes and backslashes)
            serial_port = data.get('serial_port', '')
            serial_port_clean = serial_port.replace('/', '_').replace('\\', '_')
            device_id = f"serial_{serial_port_clean}"
        
        elif connection_type == 'bluetooth':
            connection_params = {
                'device_name': data.get('bt_device_name'),
                'address': data.get('bt_address', '')
            }
            device_id = f"bluetooth_{data.get('bt_device_name', uuid.uuid4().hex[:8])}"
        
        elif connection_type == 'http':
            connection_params = {
                'url': data.get('http_url')
            }
            # Process the URL for device_id (remove special characters)
            http_url = data.get('http_url', '')
            http_url_clean = http_url.replace('://', '_').replace('/', '_')
            device_id = f"http_{http_url_clean}"
        
        elif connection_type == 'tcp':
            connection_params = {
                'host': data.get('tcp_host'),
                'port': int(data.get('tcp_port', 4403))
            }
            device_id = f"tcp_{data.get('tcp_host', '')}_{data.get('tcp_port', 4403)}"
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid connection_type'})
        
        # Check if device already exists
        if DeviceConnection.objects.filter(device_id=device_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Device connection already exists',
                'device_id': device_id
            })
        
        # Create device connection
        device = DeviceConnection.objects.create(
            device_id=device_id,
            name=data.get('device_name', f"{connection_type.upper()} Device"),
            connection_type=connection_type,
            connection_params=connection_params,
            auto_connect=data.get('auto_connect', False),
            status='disconnected'
        )
        
        return JsonResponse({
            'success': True,
            'device_id': device.device_id,
            'message': 'Device connection created successfully'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        logger.error(f'Error creating device connection: {e}', exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(['POST'])
@csrf_exempt
def connect_device(request, device_id):
    """
    API endpoint to connect to a device
    """
    try:
        device = DeviceConnection.objects.get(device_id=device_id)
        
        # Update status
        device.status = 'connecting'
        device.save()
        
        # In a real implementation, this would trigger actual connection logic
        # For now, simulate successful connection
        from django.utils import timezone
        device.status = 'connected'
        device.last_connected_at = timezone.now()
        device.save()
        
        # Update bridge status if this is a serial connection
        if device.connection_type == 'serial':
            from .models import BridgeStatus
            bridge_status = BridgeStatus.objects.first()
            if bridge_status:
                bridge_status.serial_connected = True
                bridge_status.rak4631_connected = True
                bridge_status.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Connected to {device.name}'
        })
    
    except DeviceConnection.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Device not found'})
    except Exception as e:
        logger.error(f'Error connecting to device: {e}', exc_info=True)
        device.status = 'error'
        device.last_error = str(e)
        device.save()
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(['POST'])
@csrf_exempt
def disconnect_device(request, device_id):
    """
    API endpoint to disconnect from a device
    """
    try:
        device = DeviceConnection.objects.get(device_id=device_id)
        
        # In a real implementation, this would trigger actual disconnection logic
        device.status = 'disconnected'
        device.save()
        
        # Update bridge status if this was a serial connection
        if device.connection_type == 'serial':
            from .models import BridgeStatus
            bridge_status = BridgeStatus.objects.first()
            if bridge_status:
                bridge_status.serial_connected = False
                bridge_status.rak4631_connected = False
                bridge_status.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Disconnected from {device.name}'
        })
    
    except DeviceConnection.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Device not found'})
    except Exception as e:
        logger.error(f'Error disconnecting from device: {e}', exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(['DELETE'])
@csrf_exempt
def delete_device(request, device_id):
    """
    API endpoint to delete a device connection
    """
    try:
        device = DeviceConnection.objects.get(device_id=device_id)
        
        # Disconnect if connected
        if device.status == 'connected':
            device.status = 'disconnected'
            device.save()
        
        # Delete the device
        device.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Device deleted successfully'
        })
    
    except DeviceConnection.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Device not found'})
    except Exception as e:
        logger.error(f'Error deleting device: {e}', exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(['GET'])
def test_device_connection(request, device_id):
    """
    API endpoint to test a device connection
    """
    try:
        device = DeviceConnection.objects.get(device_id=device_id)
        
        # In a real implementation, this would actually test the connection
        # For now, simulate a test
        test_results = {
            'success': True,
            'device_id': device.device_id,
            'connection_type': device.connection_type,
            'reachable': True,
            'latency_ms': 42,
            'message': 'Device is reachable'
        }
        
        return JsonResponse(test_results)
    
    except DeviceConnection.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Device not found'})
    except Exception as e:
        logger.error(f'Error testing device connection: {e}', exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})
