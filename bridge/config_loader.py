"""
Configuration loader for MeshCore Bridge
Reads configuration from PostgreSQL database
"""
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load configuration from database"""
    
    def __init__(self):
        self.db_config = self._get_db_config()
        self.last_config_id = None
        self.last_updated = None
    
    def _get_db_config(self):
        """Get database configuration from environment"""
        database_url = os.getenv('DATABASE_URL', 'postgresql://meshcore:meshcore123@postgres:5432/meshcore')
        
        # Parse DATABASE_URL
        # Format: postgresql://user:password@host:port/database
        if database_url.startswith('postgresql://'):
            parts = database_url.replace('postgresql://', '').split('@')
            user_pass = parts[0].split(':')
            host_db = parts[1].split('/')
            host_port = host_db[0].split(':')
            
            return {
                'dbname': host_db[1] if len(host_db) > 1 else 'meshcore',
                'user': user_pass[0] if len(user_pass) > 0 else 'meshcore',
                'password': user_pass[1] if len(user_pass) > 1 else 'meshcore123',
                'host': host_port[0] if len(host_port) > 0 else 'postgres',
                'port': host_port[1] if len(host_port) > 1 else '5432'
            }
        else:
            # Fallback defaults
            return {
                'dbname': os.getenv('POSTGRES_DB', 'meshcore'),
                'user': os.getenv('POSTGRES_USER', 'meshcore'),
                'password': os.getenv('POSTGRES_PASSWORD', 'meshcore123'),
                'host': os.getenv('DB_HOST', 'postgres'),
                'port': os.getenv('DB_PORT', '5432')
            }
    
    def load_config(self):
        """Load configuration from database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get the first (and should be only) configuration record
            cursor.execute("""
                SELECT id, mqtt_broker, mqtt_port, mqtt_username, mqtt_password,
                       mqtt_topic_prefix, mqtt_enabled, mqtt_connected,
                       serial_port, serial_baud, serial_enabled, serial_connected,
                       auto_acknowledge, store_packets, forward_to_mqtt,
                       updated_at
                FROM meshcore_bridgeconfiguration
                ORDER BY id ASC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                config = dict(row)
                self.last_config_id = config['id']
                self.last_updated = config['updated_at']
                return config
            else:
                logger.warning("No bridge configuration found in database, using defaults")
                return self._get_default_config()
        
        except Exception as e:
            logger.error(f"Error loading configuration from database: {e}")
            logger.warning("Using default configuration")
            return self._get_default_config()
    
    def has_config_changed(self):
        """Check if configuration has been updated in database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT updated_at
                FROM meshcore_bridgeconfiguration
                WHERE id = %s
            """, (self.last_config_id,))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row and row[0] != self.last_updated:
                return True
            return False
        
        except Exception as e:
            logger.error(f"Error checking configuration changes: {e}")
            return False
    
    def _get_default_config(self):
        """Return default configuration"""
        return {
            'mqtt_broker': '',
            'mqtt_port': 1883,
            'mqtt_username': '',
            'mqtt_password': '',
            'mqtt_topic_prefix': 'meshcore',
            'mqtt_enabled': False,
            'mqtt_connected': False,
            
            'serial_port': '',
            'serial_baud': 115200,
            'serial_enabled': False,
            'serial_connected': False,
            
            'auto_acknowledge': True,
            'store_packets': True,
            'forward_to_mqtt': True,
        }
    
    def update_connection_status(self, mqtt_connected=None, serial_connected=None):
        """Update connection status in database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if mqtt_connected is not None:
                updates.append("mqtt_connected = %s")
                params.append(mqtt_connected)
            
            if serial_connected is not None:
                updates.append("serial_connected = %s")
                params.append(serial_connected)
            
            if updates and self.last_config_id:
                query = f"UPDATE meshcore_bridgeconfiguration SET {', '.join(updates)} WHERE id = %s"
                params.append(self.last_config_id)
                
                cursor.execute(query, params)
                conn.commit()
            
            cursor.close()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error updating connection status: {e}")
