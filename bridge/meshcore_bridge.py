"""
MeshCore to MQTT Bridge
Connects to RAK4631 via serial and publishes messages to MQTT
"""
import os
import sys
import time
import json
import logging
import serial
import paho.mqtt.client as mqtt
from datetime import datetime
from typing import Optional
import threading
import queue

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meshcore_parser import MeshCoreParser, PayloadType, RouteType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MeshCoreBridge:
    """Bridge between MeshCore (serial) and MQTT"""
    
    def __init__(self, config: dict):
        self.config = config
        self.parser = MeshCoreParser()
        
        # Serial connection
        self.serial_port = config.get('serial_port', '/dev/ttyACM0')
        self.serial_baud = config.get('serial_baud', 115200)
        self.serial_conn: Optional[serial.Serial] = None
        
        # MQTT connection
        self.mqtt_broker = config.get('mqtt_broker', 'localhost')
        self.mqtt_port = config.get('mqtt_port', 1883)
        self.mqtt_username = config.get('mqtt_username')
        self.mqtt_password = config.get('mqtt_password')
        self.mqtt_topic_prefix = config.get('mqtt_topic_prefix', 'meshcore')
        self.mqtt_client: Optional[mqtt.Client] = None
        
        # State
        self.running = False
        self.packet_queue = queue.Queue()
        self.stats = {
            'packets_received': 0,
            'packets_parsed': 0,
            'packets_published': 0,
            'errors': 0,
            'started_at': None
        }
        
        # Known nodes (cache)
        self.known_nodes = {}
    
    def connect_serial(self) -> bool:
        """Connect to serial port"""
        try:
            logger.info(f"Connecting to serial port {self.serial_port} at {self.serial_baud} baud...")
            self.serial_conn = serial.Serial(
                port=self.serial_port,
                baudrate=self.serial_baud,
                timeout=1.0,
                write_timeout=1.0
            )
            logger.info("Serial connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to serial port: {e}")
            return False
    
    def connect_mqtt(self) -> bool:
        """Connect to MQTT broker"""
        try:
            logger.info(f"Connecting to MQTT broker {self.mqtt_broker}:{self.mqtt_port}...")
            
            self.mqtt_client = mqtt.Client(client_id="meshcore_bridge")
            
            if self.mqtt_username and self.mqtt_password:
                self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
            
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
            self.mqtt_client.on_message = self._on_mqtt_message
            
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            logger.info("MQTT connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            logger.info("MQTT connected successfully")
            # Subscribe to command topics
            client.subscribe(f"{self.mqtt_topic_prefix}/command/#")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        if rc != 0:
            logger.warning(f"MQTT disconnected unexpectedly (code {rc})")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            logger.info(f"Received MQTT message on {msg.topic}: {msg.payload}")
            # Handle commands from MQTT (future implementation)
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def read_serial_packet(self) -> Optional[bytes]:
        """
        Read a packet from serial port
        This is a simplified implementation - actual protocol may use framing
        """
        try:
            if not self.serial_conn or not self.serial_conn.is_open:
                return None
            
            # Look for packet start marker or read fixed-size chunks
            # This depends on how MeshCore companion firmware sends packets
            # For now, we'll read line-by-line and look for hex-encoded packets
            
            line = self.serial_conn.readline()
            if not line:
                return None
            
            # Try to decode as hex (common format for serial output)
            try:
                line_str = line.decode('utf-8', errors='ignore').strip()
                
                # Look for hex packet (format: "RX: <hex>")
                if line_str.startswith('RX:') or line_str.startswith('PKT:'):
                    hex_data = line_str.split(':', 1)[1].strip()
                    packet_data = bytes.fromhex(hex_data)
                    return packet_data
                
                # Or just try to parse as hex directly
                if all(c in '0123456789abcdefABCDEF ' for c in line_str):
                    packet_data = bytes.fromhex(line_str.replace(' ', ''))
                    if len(packet_data) > 0:
                        return packet_data
                        
            except:
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading from serial: {e}")
            return None
    
    def process_packet(self, packet_data: bytes):
        """Process a received packet"""
        try:
            self.stats['packets_received'] += 1
            
            # Parse packet
            packet = self.parser.parse_packet(packet_data)
            if not packet:
                logger.warning("Failed to parse packet")
                self.stats['errors'] += 1
                return
            
            self.stats['packets_parsed'] += 1
            
            logger.info(f"Parsed packet: {packet.header.payload_type.name} via {packet.header.route_type.name}")
            
            # Handle different payload types
            if packet.parsed_payload:
                self._handle_parsed_payload(packet)
            
            # Publish to MQTT
            self._publish_to_mqtt(packet)
            
        except Exception as e:
            logger.error(f"Error processing packet: {e}", exc_info=True)
            self.stats['errors'] += 1
    
    def _handle_parsed_payload(self, packet):
        """Handle parsed payload data"""
        payload = packet.parsed_payload
        
        if payload.get('type') == 'advertisement':
            # Update known nodes
            node_hash = payload['node_hash']
            self.known_nodes[node_hash] = {
                'public_key': payload['public_key'],
                'node_hash': node_hash,
                'last_seen': datetime.now().isoformat(),
                'appdata': payload.get('appdata', {})
            }
            logger.info(f"Node advertisement: {node_hash} - {payload.get('appdata', {}).get('name', 'Unknown')}")
        
        elif payload.get('type') == 'text_message':
            logger.info(f"Text message: {payload['source_hash']} → {payload['destination_hash']}")
        
        elif payload.get('type') == 'group_text':
            logger.info(f"Group message on channel {payload['channel_hash']}")
    
    def _publish_to_mqtt(self, packet):
        """Publish packet to MQTT"""
        try:
            if not self.mqtt_client:
                return
            
            # Create MQTT message
            message = {
                'timestamp': datetime.now().isoformat(),
                'route_type': packet.header.route_type.name,
                'payload_type': packet.header.payload_type.name,
                'path': [p.hex() for p in packet.path],
                'hop_count': len(packet.path),
                'parsed': packet.parsed_payload
            }
            
            # Publish to different topics based on payload type
            payload_type = packet.header.payload_type.name.lower()
            topic = f"{self.mqtt_topic_prefix}/packets/{payload_type}"
            
            self.mqtt_client.publish(topic, json.dumps(message), qos=1)
            self.stats['packets_published'] += 1
            
            # Also publish to general packet topic
            self.mqtt_client.publish(
                f"{self.mqtt_topic_prefix}/packets/all",
                json.dumps(message),
                qos=0
            )
            
        except Exception as e:
            logger.error(f"Error publishing to MQTT: {e}")
            self.stats['errors'] += 1
    
    def publish_stats(self):
        """Publish bridge statistics to MQTT"""
        try:
            if not self.mqtt_client:
                return
            
            stats = {
                **self.stats,
                'timestamp': datetime.now().isoformat(),
                'known_nodes': len(self.known_nodes),
                'serial_connected': self.serial_conn and self.serial_conn.is_open,
                'mqtt_connected': self.mqtt_client and self.mqtt_client.is_connected()
            }
            
            self.mqtt_client.publish(
                f"{self.mqtt_topic_prefix}/bridge/stats",
                json.dumps(stats),
                qos=1,
                retain=True
            )
            
        except Exception as e:
            logger.error(f"Error publishing stats: {e}")
    
    def run(self):
        """Main bridge loop"""
        logger.info("Starting MeshCore Bridge...")
        
        # Connect to serial
        if not self.connect_serial():
            logger.error("Failed to connect to serial port, exiting")
            return
        
        # Connect to MQTT
        if not self.connect_mqtt():
            logger.error("Failed to connect to MQTT broker, exiting")
            return
        
        self.running = True
        self.stats['started_at'] = datetime.now().isoformat()
        
        # Start stats publishing thread
        stats_thread = threading.Thread(target=self._stats_loop, daemon=True)
        stats_thread.start()
        
        logger.info("Bridge running, waiting for packets...")
        
        try:
            while self.running:
                # Read packet from serial
                packet_data = self.read_serial_packet()
                
                if packet_data:
                    self.process_packet(packet_data)
                else:
                    # Small delay to avoid busy-waiting
                    time.sleep(0.01)
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def _stats_loop(self):
        """Periodically publish statistics"""
        while self.running:
            time.sleep(30)  # Publish every 30 seconds
            self.publish_stats()
    
    def shutdown(self):
        """Shutdown the bridge"""
        logger.info("Shutting down bridge...")
        self.running = False
        
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("Serial connection closed")
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT connection closed")
        
        logger.info("Bridge shutdown complete")


def load_config():
    """Load configuration from environment variables"""
    return {
        'serial_port': os.getenv('SERIAL_PORT', '/dev/ttyACM0'),
        'serial_baud': int(os.getenv('SERIAL_BAUD', '115200')),
        'mqtt_broker': os.getenv('MQTT_BROKER', 'localhost'),
        'mqtt_port': int(os.getenv('MQTT_PORT', '1883')),
        'mqtt_username': os.getenv('MQTT_USERNAME'),
        'mqtt_password': os.getenv('MQTT_PASSWORD'),
        'mqtt_topic_prefix': os.getenv('MQTT_TOPIC_PREFIX', 'meshcore'),
    }


def main():
    """Main entry point"""
    config = load_config()
    bridge = MeshCoreBridge(config)
    bridge.run()


if __name__ == '__main__':
    main()
