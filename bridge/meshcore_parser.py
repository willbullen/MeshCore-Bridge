"""
MeshCore Packet Parser
Parses binary packets according to MeshCore protocol specification
"""
import struct
import hashlib
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class RouteType(IntEnum):
    """Route type values from packet header"""
    TRANSPORT_FLOOD = 0x00
    FLOOD = 0x01
    DIRECT = 0x02
    TRANSPORT_DIRECT = 0x03


class PayloadType(IntEnum):
    """Payload type values from packet header"""
    REQ = 0x00
    RESPONSE = 0x01
    TXT_MSG = 0x02
    ACK = 0x03
    ADVERT = 0x04
    GRP_TXT = 0x05
    GRP_DATA = 0x06
    ANON_REQ = 0x07
    PATH = 0x08
    TRACE = 0x09
    MULTIPART = 0x0A
    CONTROL = 0x0B
    RAW_CUSTOM = 0x0F


class NodeType(IntEnum):
    """Node type flags from advertisement appdata"""
    CHAT = 0x01
    REPEATER = 0x02
    ROOM_SERVER = 0x03
    SENSOR = 0x04


class AppdataFlags(IntEnum):
    """Appdata flags from advertisement"""
    IS_CHAT = 0x01
    IS_REPEATER = 0x02
    IS_ROOM_SERVER = 0x03
    IS_SENSOR = 0x04
    HAS_LOCATION = 0x10
    HAS_FEATURE1 = 0x20
    HAS_FEATURE2 = 0x40
    HAS_NAME = 0x80


@dataclass
class PacketHeader:
    """Parsed packet header"""
    route_type: RouteType
    payload_type: PayloadType
    payload_version: int
    
    @classmethod
    def from_byte(cls, header_byte: int):
        """Parse header byte into components"""
        route_type = RouteType(header_byte & 0x03)
        payload_type = PayloadType((header_byte >> 2) & 0x0F)
        payload_version = (header_byte >> 6) & 0x03
        return cls(route_type, payload_type, payload_version)


@dataclass
class MeshCorePacket:
    """Parsed MeshCore packet"""
    header: PacketHeader
    transport_codes: Optional[Tuple[int, int]]
    path: List[bytes]
    payload: bytes
    
    # Parsed payload data (if applicable)
    parsed_payload: Optional[dict] = None


@dataclass
class NodeAdvertisement:
    """Parsed node advertisement payload"""
    public_key: bytes
    timestamp: int
    signature: bytes
    appdata: Optional[dict] = None


@dataclass
class TextMessage:
    """Parsed text message payload"""
    destination_hash: int
    source_hash: int
    cipher_mac: int
    ciphertext: bytes
    timestamp: Optional[int] = None
    txt_type: Optional[int] = None
    message: Optional[str] = None


class MeshCoreParser:
    """Parser for MeshCore binary packets"""
    
    MAX_PATH_SIZE = 64
    MAX_PACKET_PAYLOAD = 184
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_packet(self, data: bytes) -> Optional[MeshCorePacket]:
        """
        Parse a complete MeshCore packet from binary data
        
        Args:
            data: Raw packet bytes
            
        Returns:
            Parsed MeshCorePacket or None if parsing fails
        """
        try:
            if len(data) < 2:
                self.logger.warning(f"Packet too short: {len(data)} bytes")
                return None
            
            offset = 0
            
            # Parse header (1 byte)
            header = PacketHeader.from_byte(data[offset])
            offset += 1
            
            # Parse transport codes (4 bytes, optional)
            transport_codes = None
            if header.route_type in (RouteType.TRANSPORT_FLOOD, RouteType.TRANSPORT_DIRECT):
                if len(data) < offset + 4:
                    self.logger.warning("Packet too short for transport codes")
                    return None
                code1, code2 = struct.unpack('<HH', data[offset:offset+4])
                transport_codes = (code1, code2)
                offset += 4
            
            # Parse path length (1 byte)
            if len(data) < offset + 1:
                self.logger.warning("Packet too short for path length")
                return None
            path_len = data[offset]
            offset += 1
            
            # Parse path
            if len(data) < offset + path_len:
                self.logger.warning(f"Packet too short for path: need {path_len}, have {len(data) - offset}")
                return None
            
            path = []
            for i in range(path_len):
                path.append(data[offset:offset+1])
                offset += 1
            
            # Remaining data is payload
            payload = data[offset:]
            
            if len(payload) > self.MAX_PACKET_PAYLOAD:
                self.logger.warning(f"Payload too large: {len(payload)} bytes")
            
            packet = MeshCorePacket(
                header=header,
                transport_codes=transport_codes,
                path=path,
                payload=payload
            )
            
            # Try to parse payload based on type
            packet.parsed_payload = self._parse_payload(packet)
            
            return packet
            
        except Exception as e:
            self.logger.error(f"Error parsing packet: {e}", exc_info=True)
            return None
    
    def _parse_payload(self, packet: MeshCorePacket) -> Optional[dict]:
        """Parse payload based on payload type"""
        try:
            payload_type = packet.header.payload_type
            payload = packet.payload
            
            if payload_type == PayloadType.ADVERT:
                return self._parse_advertisement(payload)
            elif payload_type == PayloadType.TXT_MSG:
                return self._parse_text_message(payload)
            elif payload_type == PayloadType.GRP_TXT:
                return self._parse_group_text(payload)
            elif payload_type == PayloadType.ACK:
                return self._parse_acknowledgment(payload)
            else:
                return {'raw': payload.hex()}
                
        except Exception as e:
            self.logger.error(f"Error parsing payload: {e}", exc_info=True)
            return None
    
    def _parse_advertisement(self, payload: bytes) -> dict:
        """Parse node advertisement payload"""
        if len(payload) < 100:  # 32 + 4 + 64 = 100 minimum
            return {'error': 'Advertisement too short'}
        
        offset = 0
        
        # Public key (32 bytes)
        public_key = payload[offset:offset+32]
        offset += 32
        
        # Timestamp (4 bytes, little endian)
        timestamp = struct.unpack('<I', payload[offset:offset+4])[0]
        offset += 4
        
        # Signature (64 bytes)
        signature = payload[offset:offset+64]
        offset += 64
        
        # Appdata (optional)
        appdata = None
        if len(payload) > offset:
            appdata = self._parse_appdata(payload[offset:])
        
        node_hash = format(public_key[0], '02x')
        
        return {
            'type': 'advertisement',
            'public_key': public_key.hex(),
            'node_hash': node_hash,
            'timestamp': timestamp,
            'signature': signature.hex(),
            'appdata': appdata
        }
    
    def _parse_appdata(self, appdata: bytes) -> dict:
        """Parse advertisement appdata"""
        if len(appdata) < 1:
            return {}
        
        offset = 0
        flags = appdata[offset]
        offset += 1
        
        result = {'flags': flags}
        
        # Determine node type
        if flags & AppdataFlags.IS_ROOM_SERVER:
            result['node_type'] = 'room_server'
        elif flags & AppdataFlags.IS_REPEATER:
            result['node_type'] = 'repeater'
        elif flags & AppdataFlags.IS_SENSOR:
            result['node_type'] = 'sensor'
        elif flags & AppdataFlags.IS_CHAT:
            result['node_type'] = 'chat'
        else:
            result['node_type'] = 'unknown'
        
        # Parse location (if present)
        if flags & AppdataFlags.HAS_LOCATION:
            if len(appdata) >= offset + 8:
                lat_raw, lon_raw = struct.unpack('<ii', appdata[offset:offset+8])
                result['latitude'] = lat_raw / 1000000.0
                result['longitude'] = lon_raw / 1000000.0
                offset += 8
        
        # Skip feature fields if present
        if flags & AppdataFlags.HAS_FEATURE1:
            offset += 2
        if flags & AppdataFlags.HAS_FEATURE2:
            offset += 2
        
        # Parse name (if present)
        if flags & AppdataFlags.HAS_NAME:
            if len(appdata) > offset:
                try:
                    name = appdata[offset:].decode('utf-8', errors='ignore').rstrip('\x00')
                    result['name'] = name
                except:
                    pass
        
        return result
    
    def _parse_text_message(self, payload: bytes) -> dict:
        """Parse text message payload"""
        if len(payload) < 4:
            return {'error': 'Text message too short'}
        
        offset = 0
        
        # Destination hash (1 byte)
        dest_hash = format(payload[offset], '02x')
        offset += 1
        
        # Source hash (1 byte)
        src_hash = format(payload[offset], '02x')
        offset += 1
        
        # Cipher MAC (2 bytes)
        cipher_mac = struct.unpack('<H', payload[offset:offset+2])[0]
        offset += 2
        
        # Ciphertext (rest of payload)
        ciphertext = payload[offset:]
        
        return {
            'type': 'text_message',
            'destination_hash': dest_hash,
            'source_hash': src_hash,
            'cipher_mac': cipher_mac,
            'ciphertext': ciphertext.hex(),
            'encrypted': True
        }
    
    def _parse_group_text(self, payload: bytes) -> dict:
        """Parse group text message payload"""
        if len(payload) < 3:
            return {'error': 'Group text too short'}
        
        offset = 0
        
        # Channel hash (1 byte)
        channel_hash = format(payload[offset], '02x')
        offset += 1
        
        # Cipher MAC (2 bytes)
        cipher_mac = struct.unpack('<H', payload[offset:offset+2])[0]
        offset += 2
        
        # Ciphertext (rest of payload)
        ciphertext = payload[offset:]
        
        return {
            'type': 'group_text',
            'channel_hash': channel_hash,
            'cipher_mac': cipher_mac,
            'ciphertext': ciphertext.hex(),
            'encrypted': True
        }
    
    def _parse_acknowledgment(self, payload: bytes) -> dict:
        """Parse acknowledgment payload"""
        if len(payload) < 4:
            return {'error': 'ACK too short'}
        
        # Checksum (4 bytes)
        checksum = struct.unpack('<I', payload[0:4])[0]
        
        return {
            'type': 'acknowledgment',
            'checksum': format(checksum, '08x')
        }
    
    @staticmethod
    def calculate_node_hash(public_key: bytes) -> str:
        """Calculate node hash from public key (first byte)"""
        return format(public_key[0], '02x')
    
    @staticmethod
    def calculate_channel_hash(shared_key: bytes) -> str:
        """Calculate channel hash from shared key (first byte of SHA256)"""
        sha256 = hashlib.sha256(shared_key).digest()
        return format(sha256[0], '02x')
