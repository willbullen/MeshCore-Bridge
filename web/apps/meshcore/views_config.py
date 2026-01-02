"""
Configuration Management Views and APIs
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import BridgeConfiguration

logger = logging.getLogger(__name__)


@require_http_methods(['POST'])
@csrf_exempt
def test_mqtt_connection(request):
    """
    Test MQTT broker connection
    """
    try:
        data = json.loads(request.body)
        
        broker = data.get('mqtt_broker', '').strip()
        port = int(data.get('mqtt_port', 1883))
        username = data.get('mqtt_username', '').strip()
        password = data.get('mqtt_password', '').strip()
        
        if not broker:
            return JsonResponse({
                'success': False,
                'error': 'MQTT broker address is required'
            })
        
        # Test MQTT connection
        try:
            import paho.mqtt.client as mqtt
            
            test_result = {'connected': False, 'error': None}
            
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    test_result['connected'] = True
                else:
                    test_result['error'] = f"Connection failed with code {rc}"
            
            client = mqtt.Client(client_id="meshcore_test", clean_session=True)
            client.on_connect = on_connect
            
            if username and password:
                client.username_pw_set(username, password)
            
            # Set timeout
            client.connect(broker, port, keepalive=5)
            client.loop_start()
            
            # Wait up to 5 seconds for connection
            import time
            for _ in range(50):  # 5 seconds total
                if test_result['connected'] or test_result['error']:
                    break
                time.sleep(0.1)
            
            client.loop_stop()
            client.disconnect()
            
            if test_result['connected']:
                # Update configuration
                config = BridgeConfiguration.objects.first()
                if config:
                    config.mqtt_connected = True
                    config.mqtt_last_test = timezone.now()
                    config.mqtt_last_error = ''
                    config.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully connected to {broker}:{port}'
                })
            else:
                error_msg = test_result['error'] or 'Connection timeout after 5 seconds'
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                })
                
        except ImportError:
            return JsonResponse({
                'success': False,
                'error': 'paho-mqtt library not installed'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Connection failed: {str(e)}'
            })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        logger.error(f'Error testing MQTT connection: {e}', exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(['POST'])
@csrf_exempt
def test_serial_connection(request):
    """
    Test serial port connection
    """
    try:
        data = json.loads(request.body)
        
        port = data.get('serial_port', '').strip()
        baudrate = int(data.get('serial_baud', 115200))
        
        if not port:
            return JsonResponse({
                'success': False,
                'error': 'Serial port is required'
            })
        
        # Test serial connection
        try:
            import serial
            
            # Try to open the port
            ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1.0,
                write_timeout=1.0
            )
            
            # Check if port is actually open
            if ser.is_open:
                port_name = ser.name
                ser.close()
                
                # Update configuration
                config = BridgeConfiguration.objects.first()
                if config:
                    config.serial_connected = True
                    config.serial_last_test = timezone.now()
                    config.serial_last_error = ''
                    config.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully connected to {port_name} at {baudrate} baud'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to open serial port'
                })
                
        except ImportError:
            return JsonResponse({
                'success': False,
                'error': 'pyserial library not installed'
            })
        except serial.SerialException as e:
            error_msg = str(e)
            
            # Update configuration with error
            config = BridgeConfiguration.objects.first()
            if config:
                config.serial_connected = False
                config.serial_last_test = timezone.now()
                config.serial_last_error = error_msg
                config.save()
            
            return JsonResponse({
                'success': False,
                'error': f'Serial port error: {error_msg}'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Connection failed: {str(e)}'
            })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        logger.error(f'Error testing serial connection: {e}', exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(['POST'])
@csrf_exempt
def save_configuration(request):
    """
    Save bridge configuration to database
    """
    try:
        data = json.loads(request.body)
        
        # Get or create configuration
        config = BridgeConfiguration.objects.first()
        if not config:
            config = BridgeConfiguration.objects.create()
        
        # Update MQTT settings
        config.mqtt_broker = data.get('mqtt_broker', '').strip()
        config.mqtt_port = int(data.get('mqtt_port', 1883))
        config.mqtt_username = data.get('mqtt_username', '').strip()
        config.mqtt_password = data.get('mqtt_password', '').strip()
        config.mqtt_topic_prefix = data.get('mqtt_topic_prefix', 'meshcore').strip()
        config.mqtt_enabled = data.get('mqtt_enabled', False)
        
        # Update serial settings
        config.serial_port = data.get('serial_port', '').strip()
        config.serial_baud = int(data.get('serial_baud', 115200))
        config.serial_enabled = data.get('serial_enabled', False)
        
        # Update behavior settings
        config.auto_acknowledge = data.get('auto_acknowledge', True)
        config.store_packets = data.get('store_packets', True)
        config.forward_to_mqtt = data.get('forward_to_mqtt', True)
        
        config.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Configuration saved successfully',
            'config': {
                'id': config.id,
                'mqtt_enabled': config.mqtt_enabled,
                'serial_enabled': config.serial_enabled,
                'mqtt_status': config.mqtt_status,
                'serial_status': config.serial_status,
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        logger.error(f'Error saving configuration: {e}', exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(['GET'])
def get_configuration(request):
    """
    Get current bridge configuration
    """
    try:
        config = BridgeConfiguration.objects.first()
        if not config:
            config = BridgeConfiguration.objects.create()
        
        return JsonResponse({
            'success': True,
            'config': {
                'mqtt_broker': config.mqtt_broker,
                'mqtt_port': config.mqtt_port,
                'mqtt_username': config.mqtt_username,
                'mqtt_password': config.mqtt_password,
                'mqtt_topic_prefix': config.mqtt_topic_prefix,
                'mqtt_enabled': config.mqtt_enabled,
                'mqtt_connected': config.mqtt_connected,
                'mqtt_last_test': config.mqtt_last_test.isoformat() if config.mqtt_last_test else None,
                'mqtt_last_error': config.mqtt_last_error,
                'mqtt_status': config.mqtt_status,
                
                'serial_port': config.serial_port,
                'serial_baud': config.serial_baud,
                'serial_enabled': config.serial_enabled,
                'serial_connected': config.serial_connected,
                'serial_last_test': config.serial_last_test.isoformat() if config.serial_last_test else None,
                'serial_last_error': config.serial_last_error,
                'serial_status': config.serial_status,
                
                'auto_acknowledge': config.auto_acknowledge,
                'store_packets': config.store_packets,
                'forward_to_mqtt': config.forward_to_mqtt,
            }
        })
    
    except Exception as e:
        logger.error(f'Error getting configuration: {e}', exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(['POST'])
@csrf_exempt
def reload_bridge_config(request):
    """
    Signal the bridge service to reload configuration from database
    """
    try:
        # Update bridge status to trigger config reload
        from .models import BridgeStatus
        bridge_status = BridgeStatus.objects.first()
        if bridge_status:
            bridge_status.save()  # This will trigger updated_at
        
        return JsonResponse({
            'success': True,
            'message': 'Bridge configuration reload signal sent'
        })
    
    except Exception as e:
        logger.error(f'Error reloading bridge config: {e}', exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})
