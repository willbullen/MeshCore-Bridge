# MeshCore Bridge

A complete MeshCore mesh networking bridge with Django web interface for Raspberry Pi and RAK WisBlock 4631.

## Features

✨ **MeshCore Protocol Support**
- Binary packet parsing
- Ed25519 cryptography
- Node advertisements
- Direct and group messaging
- Telemetry collection

🌐 **Modern Web Interface**
- Real-time dashboard
- Node management and visualization
- Message history
- Interactive map
- Telemetry monitoring
- Configuration interface

🔌 **Connectivity**
- Serial/USB connection to RAK4631
- MQTT publishing
- Cloudflare Tunnel support
- Remote access via Portainer

🐳 **Docker-Based**
- Complete Docker Compose stack
- PostgreSQL database
- Redis task queue
- Celery workers
- Easy deployment

## Quick Start

### 1. Prerequisites

- Raspberry Pi 4/5 with Docker installed
- RAK WisBlock 4631 with MeshCore firmware
- MQTT broker (local or remote)

### 2. Setup

```bash
# Clone/copy project
cd ~/meshcore-bridge

# Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# Connect RAK4631 via USB

# Deploy
docker-compose up -d
```

### 3. Access

- **Web UI**: http://your-pi-ip:8000/meshcore/
- **Admin**: http://your-pi-ip:8000/admin/
- **Portainer**: https://your-pi-ip:9443/

**Default Login:**
- Username: `admin`
- Password: `admin123`

## Architecture

```
RAK4631 (USB) → MeshCore Bridge → MQTT Broker
                       ↓
                Django Web App → PostgreSQL
                       ↓
            Cloudflare Tunnel + Portainer
```

## Components

- **MeshCore Bridge**: Python application parsing MeshCore packets
- **Django Web App**: Modern UI with shadcn-style design
- **PostgreSQL**: Data persistence
- **Redis + Celery**: Background tasks
- **Cloudflare Tunnel**: Secure remote access
- **Portainer**: Docker management UI

## Documentation

- [Complete Deployment Guide](DEPLOYMENT_GUIDE.md)
- [MeshCore Protocol](https://github.com/ripplebiz/MeshCore)
- [RAK4631 Documentation](https://docs.rakwireless.com/Product-Categories/WisBlock/RAK4631/Overview/)

## Project Structure

```
meshcore-bridge/
├── bridge/                 # MeshCore bridge application
│   ├── meshcore_parser.py  # Binary packet parser
│   ├── meshcore_bridge.py  # Main bridge application
│   ├── Dockerfile
│   └── requirements.txt
├── web/                    # Django web application
│   ├── apps/
│   │   └── meshcore/       # MeshCore Django app
│   ├── templates/          # UI templates
│   ├── valentia_backend/   # Django settings
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml      # Complete stack definition
├── .env.example            # Environment template
├── DEPLOYMENT_GUIDE.md     # Detailed deployment instructions
└── README.md               # This file
```

## Configuration

### Environment Variables

```env
# Database
POSTGRES_DB=meshcore
POSTGRES_USER=meshcore
POSTGRES_PASSWORD=your_password

# Serial Connection
SERIAL_PORT=/dev/ttyACM0
SERIAL_BAUD=115200

# MQTT
MQTT_BROKER=mqtt.example.com
MQTT_PORT=1883
MQTT_USERNAME=username
MQTT_PASSWORD=password

# Cloudflare Tunnel
CLOUDFLARE_TUNNEL_TOKEN=your_token
```

### MQTT Topics

```
meshcore/packets/advert     # Node advertisements
meshcore/packets/txt_msg    # Direct messages
meshcore/packets/grp_txt    # Group messages
meshcore/packets/ack        # Acknowledgments
meshcore/packets/all        # All packets
meshcore/bridge/stats       # Bridge statistics
```

## Development

### Local Development

```bash
# Start database only
docker-compose up -d postgres redis

# Run Django locally
cd web
python manage.py runserver

# Run bridge locally
cd bridge
python meshcore_bridge.py
```

### Testing

```bash
# Django tests
docker exec -it meshcore-web python manage.py test

# Check bridge logs
docker-compose logs -f bridge
```

## Troubleshooting

### Common Issues

**RAK4631 not detected:**
```bash
ls -l /dev/ttyACM*
sudo usermod -aG dialout $USER
```

**Bridge not connecting:**
```bash
docker-compose logs bridge
docker exec -it meshcore-bridge ls -l /dev/ttyACM0
```

**Web interface not loading:**
```bash
docker-compose logs web
docker-compose restart web
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed troubleshooting.

## Screenshots

### Dashboard
Modern shadcn-style dashboard with real-time statistics, node status, and recent messages.

### Map View
Interactive map showing node locations with real-time updates.

### Telemetry
Comprehensive telemetry monitoring with battery, signal, and environmental data.

### Connections
Device connection management with support for Serial, Bluetooth, HTTP, and TCP.

## Contributing

This project integrates with MeshCore. For MeshCore protocol improvements, please contribute to:
https://github.com/ripplebiz/MeshCore

## License

This project integrates with MeshCore. Please review the MeshCore license at:
https://github.com/ripplebiz/MeshCore

## Acknowledgments

- **MeshCore Team**: For the excellent mesh networking protocol
- **RAKwireless**: For the RAK4631 hardware
- **shadcn/ui**: For design inspiration

## Support

For issues and questions:
1. Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. Review MeshCore documentation
3. Check Docker logs: `docker-compose logs`

## Roadmap

- [ ] Ed25519 signature verification
- [ ] Message encryption/decryption
- [ ] WebSocket real-time updates
- [ ] Mobile app integration
- [ ] Room server functionality
- [ ] Advanced routing visualization
- [ ] Network topology mapping
- [ ] Performance metrics dashboard
