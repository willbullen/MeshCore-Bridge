"""
MeshCore to MQTT Bridge
Connects to RAK4631 via serial and publishes messages to MQTT
Configuration is loaded from database
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
from config_loader import ConfigLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MeshCoreBridge:
    """Bridge between MeshCore (serial) and MQTT"""
    
    def __init__(self):
        self.parser = MeshCoreParser()
        self.config_loader = ConfigLoader()
        self.config = None
        
        # Serial connection
        self.serial_port = ''
        self.serial_baud = 115200
        self.serial_enabled = False
        self.serial_conn: Optional[serial.Serial] = None
        
        # MQTT connection
        self.mqtt_broker = ''
        self.mqtt_port = 1883
        self.mqtt_username = ''
        self.mqtt_password = ''
        self.mqtt_topic_prefix = 'meshcore'
        self.mqtt_enabled = False
        self.mqtt_client: Optional[mqtt.Client] = None
        
        # State
        self.running = False
        self.serial_connected = False
        self.mqtt_connected = False
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
        
        # Configuration reload
        self.config_check_interval = 10  # Check for config changes every 10 seconds
        self.last_config_check = time.time()
    
    def load_configuration(self):
        """Load configuration from database"""
        logger.info("Loading configuration from database...")
        self.config = self.config_loader.load_config()
        
        if self.config:
            # Update settings from config
            self.serial_port = self.config.get('serial_port', '')
            self.serial_baud = self.config.get('serial_baud', 115200)
            self.serial_enabled = self.config.get('serial_enabled', False)
            
            self.mqtt_broker = self.config.get('mqtt_broker', '')
            self.mqtt_port = self.config.get('mqtt_port', 1883)
            self.mqtt_username = self.config.get('mqtt_username', '')
            self.mqtt_password = self.config.get('mqtt_password', '')
            self.mqtt_topic_prefix = self.config.get('mqtt_topic_prefix', 'meshcore')
            self.mqtt_enabled = self.config.get('mqtt_enabled', False)
            
            logger.info(f"Configuration loaded - Serial: {'enabled' if self.serial_enabled else 'disabled'}, MQTT: {'enabled' if self.mqtt_enabled else 'disabled'}")
        else:
            logger.warning("No configuration loaded, using defaults")
    
    def check_config_changes(self):
        """Check if configuration has changed and reload if needed"""
        if time.time() - self.last_config_check < self.config_check_interval:
            return False
        
        self.last_config_check = time.time()
        
        if self.config_loader.has_config_changed():
            logger.info("Configuration changed, reloading...")
            old_config = self.config
            self.load_configuration()
            
            # Check if serial settings changed
            if (old_config.get('serial_enabled') != self.serial_enabled or
                old_config.get('serial_port') != self.serial_port):
                logger.info("Serial configuration changed, reconnecting...")
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                    self.serial_connected = False
            
            # Check if MQTT settings changed
            if (old_config.get('mqtt_enabled') != self.mqtt_enabled or
                old_config.get('mqtt_broker') != self.mqtt_broker):
                logger.info("MQTT configuration changed, reconnecting...")
                if self.mqtt_client:
                    self.mqtt_client.loop_stop()
                    self.mqtt_client.disconnect()
                    self.mqtt_connected = False
            
            return True
        
        return False
    
    def connect_serial(self) -> bool:
        """Connect to serial port"""
        # Skip if serial not enabled
        if not self.serial_enabled:
            logger.debug("Serial connection not enabled in configuration")
            self.serial_connected = False
            self.config_loader.update_connection_status(serial_connected=False)
            return False
        
        # Skip if no serial port configured
        if not self.serial_port or self.serial_port.strip() == '':
            logger.info("Serial port not configured, skipping serial connection")
            self.serial_connected = False
            self.config_loader.update_connection_status(serial_connected=False)
            return False
            
        try:
            logger.info(f"Connecting to serial port {self.serial_port} at {self.serial_baud} baud...")
            self.serial_conn = serial.Serial(
                port=self.serial_port,
                baudrate=self.serial_baud,
                timeout=1.0,
                write_timeout=1.0
            )
            logger.info("Serial connection established")
            self.serial_connected = True
            self.config_loader.update_connection_status(serial_connected=True)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to serial port: {e}")
            self.serial_connected = False
            self.config_loader.update_connection_status(serial_connected=False)
            return False
    
    def connect_mqtt(self) -> bool:
        """Connect to MQTT broker"""
        # Skip if MQTT not enabled
        if not self.mqtt_enabled:
            logger.debug("MQTT connection not enabled in configuration")
            self.mqtt_connected = False
            self.config_loader.update_connection_status(mqtt_connected=False)
            return False
        
        try:
            # Skip MQTT if broker is not configured
            if not self.mqtt_broker or self.mqtt_broker.strip() == '':
                logger.info("MQTT broker not configured, skipping MQTT connection")
                self.mqtt_connected = False
                self.config_loader.update_connection_status(mqtt_connected=False)
                return False
                
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
            self.mqtt_connected = True
            self.config_loader.update_connection_status(mqtt_connected=True)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.mqtt_connected = False
            self.config_loader.update_connection_status(mqtt_connected=False)
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
        logger.info("Starting MeshCore Bridge (Database-Driven Configuration)...")
        
        # Load configuration from database
        self.load_configuration()
        
        # Connect to serial (only if enabled)
        if self.serial_enabled:
            if not self.connect_serial():
                logger.warning(f"Serial connection failed. Will retry periodically.")
        else:
            logger.info("Serial connection disabled in configuration")
        
        # Connect to MQTT (only if enabled)
        if self.mqtt_enabled:
            if not self.connect_mqtt():
                logger.warning("MQTT connection failed. Will retry periodically.")
        else:
            logger.info("MQTT connection disabled in configuration")
        
        # If neither connection is available, keep running but log a warning
        if not self.serial_connected and not self.mqtt_connected:
            logger.warning("Neither serial nor MQTT is connected.")
            logger.warning("Bridge will stay running and check for configuration changes.")
        
        self.running = True
        self.stats['started_at'] = datetime.now().isoformat()
        
        # Start stats publishing thread
        stats_thread = threading.Thread(target=self._stats_loop, daemon=True)
        stats_thread.start()
        
        logger.info("Bridge running, waiting for packets...")
        logger.info("Configuration will be checked every 10 seconds for changes")
        
        try:
            while self.running:
                # Check for configuration changes
                if self.check_config_changes():
                    logger.info("Configuration reloaded, attempting to reconnect...")
                    if self.serial_enabled and not self.serial_connected:
                        self.connect_serial()
                    if self.mqtt_enabled and not self.mqtt_connected:
                        self.connect_mqtt()
                
                # Read packet from serial (only if enabled and connected)
                if self.serial_enabled and self.serial_connected:
                    packet_data = self.read_serial_packet()
                    
                    if packet_data:
                        self.process_packet(packet_data)
                    else:
                        # Small delay to avoid busy-waiting
                        time.sleep(0.01)
                else:
                    # If no serial connection, just keep the service alive
                    time.sleep(5)
                    
                    # Try to reconnect if enabled but not connected
                    if self.serial_enabled and not self.serial_connected:
                        if not self.serial_conn or not self.serial_conn.is_open:
                            logger.debug("Attempting to reconnect to serial port...")
                            self.connect_serial()
                
                # Periodically try to reconnect MQTT if enabled but not connected
                if self.mqtt_enabled and not self.mqtt_connected:
                    time.sleep(10)  # Check less frequently for MQTT
                    self.connect_mqtt()
                    
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


def main():
    """Main entry point"""
    logger.info("MeshCore Bridge - Configuration from Database")
    logger.info("Settings are managed through the web interface at /meshcore/configuration/")
    
    bridge = MeshCoreBridge()
    bridge.run()


if __name__ == '__main__':
    main()
