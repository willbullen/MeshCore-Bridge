# MeshCore Bridge - Complete Deployment Guide

## Overview

This is a complete MeshCore to MQTT bridge system with Django web interface for monitoring and configuration. The system connects to a RAK WisBlock 4631 running MeshCore firmware via USB/serial and publishes mesh network data to an MQTT broker.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4/5                          │
│                                                               │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐ │
│  │   RAK4631    │────▶│  MeshCore    │────▶│    MQTT     │ │
│  │  (USB/Serial)│     │    Bridge    │     │   Broker    │ │
│  └──────────────┘     └──────────────┘     └─────────────┘ │
│                              │                               │
│                              ▼                               │
│                       ┌──────────────┐                       │
│                       │   Django     │                       │
│                       │  Web App     │                       │
│                       └──────────────┘                       │
│                              │                               │
│                              ▼                               │
│                       ┌──────────────┐                       │
│                       │  PostgreSQL  │                       │
│                       │   Database   │                       │
│                       └──────────────┘                       │
│                                                               │
│  ┌──────────────┐     ┌──────────────┐                      │
│  │  Cloudflare  │     │  Portainer   │                      │
│  │    Tunnel    │     │  (Docker UI) │                      │
│  └──────────────┘     └──────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. **MeshCore Bridge** (Python)
- Connects to RAK4631 via serial port (`/dev/ttyACM0`)
- Parses MeshCore binary protocol packets
- Publishes to MQTT broker
- Handles node advertisements, messages, and telemetry

### 2. **Django Web Application**
- Modern shadcn-style UI
- Real-time dashboard
- Node management
- Message history
- Telemetry visualization
- Configuration interface
- PostgreSQL database

### 3. **Supporting Services**
- **PostgreSQL**: Data persistence
- **Redis**: Celery task queue
- **Celery**: Background tasks
- **Cloudflare Tunnel**: Secure remote access
- **Portainer**: Docker container management

## Prerequisites

### Hardware
- Raspberry Pi 4 or 5 (4GB+ RAM recommended)
- RAK WisBlock 4631 with MeshCore firmware
- USB cable for RAK4631 connection
- MicroSD card (32GB+ recommended)

### Software
- Raspberry Pi OS (64-bit recommended)
- Docker and Docker Compose
- MQTT broker (external or local)

## Installation

### Step 1: Prepare Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose -y

# Reboot
sudo reboot
```

### Step 2: Clone/Copy Project

```bash
# Create project directory
mkdir -p ~/meshcore-bridge
cd ~/meshcore-bridge

# Copy all project files to this directory
# (transfer via scp, git clone, or USB)
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required Configuration:**

```env
# PostgreSQL Database
POSTGRES_DB=meshcore
POSTGRES_USER=meshcore
POSTGRES_PASSWORD=your_secure_password_here

# Django
DJANGO_SECRET_KEY=generate_a_long_random_string_here
DEBUG=False
ALLOWED_HOSTS=your-pi-hostname.local,192.168.1.x

# Serial Connection (RAK4631)
SERIAL_PORT=/dev/ttyACM0
SERIAL_BAUD=115200

# MQTT Broker
MQTT_BROKER=your-mqtt-broker.com
MQTT_PORT=1883
MQTT_USERNAME=your_mqtt_username
MQTT_PASSWORD=your_mqtt_password
MQTT_TOPIC_PREFIX=meshcore

# Cloudflare Tunnel (optional)
CLOUDFLARE_TUNNEL_TOKEN=your_cloudflare_tunnel_token
```

### Step 4: Connect RAK4631

```bash
# Connect RAK4631 via USB

# Verify device is detected
ls -l /dev/ttyACM*

# Should show: /dev/ttyACM0

# Check permissions
sudo usermod -aG dialout $USER
```

### Step 5: Deploy Stack

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 6: Access Web Interface

**Local Access:**
- Web UI: `http://your-pi-ip:8000/meshcore/`
- Admin: `http://your-pi-ip:8000/admin/`
- Portainer: `https://your-pi-ip:9443/`

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

**⚠️ Change the default password immediately!**

## MeshCore Firmware Setup

### Flash RAK4631 with MeshCore

1. **Download MeshCore Firmware**
   - Visit: https://github.com/ripplebiz/MeshCore/releases
   - Download latest `.uf2` file for RAK4631

2. **Flash Firmware**
   ```bash
   # Put RAK4631 in bootloader mode (double-tap reset button)
   # Device appears as USB drive "RAK4631"
   
   # Copy firmware
   cp meshcore-rak4631-*.uf2 /media/$USER/RAK4631/
   
   # Device will reboot automatically
   ```

3. **Verify Connection**
   ```bash
   # Check serial output
   screen /dev/ttyACM0 115200
   
   # You should see MeshCore boot messages
   # Press Ctrl+A then K to exit screen
   ```

## Configuration

### Django Admin

Access admin panel at `http://your-pi-ip:8000/admin/`

**Configure Bridge:**
1. Go to "Bridge configurations"
2. Update MQTT and serial settings
3. Save changes

**Manage Nodes:**
1. Go to "Nodes"
2. View all discovered nodes
3. Mark favorites, add notes

### MQTT Topics

The bridge publishes to these topics:

```
meshcore/packets/advert       - Node advertisements
meshcore/packets/txt_msg      - Direct text messages
meshcore/packets/grp_txt      - Group text messages
meshcore/packets/ack          - Acknowledgments
meshcore/packets/all          - All packets
meshcore/bridge/stats         - Bridge statistics
```

### Cloudflare Tunnel Setup

1. **Create Tunnel**
   ```bash
   # Install cloudflared on your computer
   # Visit: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/
   
   # Create tunnel
   cloudflared tunnel create meshcore-bridge
   
   # Get tunnel token
   cloudflared tunnel token meshcore-bridge
   ```

2. **Configure DNS**
   - Add public hostname in Cloudflare dashboard
   - Point to `http://web:8000`

3. **Update .env**
   ```env
   CLOUDFLARE_TUNNEL_TOKEN=your_token_here
   ```

4. **Restart Services**
   ```bash
   docker-compose restart cloudflared
   ```

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f bridge
docker-compose logs -f web

# Last 100 lines
docker-compose logs --tail=100 bridge
```

### Check Bridge Status

```bash
# Via web interface
curl http://localhost:8000/meshcore/api/status/

# Via MQTT
mosquitto_sub -h your-mqtt-broker -t "meshcore/bridge/stats"
```

### Portainer

Access Portainer at `https://your-pi-ip:9443/`

- View container status
- Restart services
- View logs
- Monitor resources

## Troubleshooting

### RAK4631 Not Detected

```bash
# Check USB connection
lsusb

# Check serial devices
ls -l /dev/ttyACM*

# Check permissions
sudo usermod -aG dialout $USER
sudo reboot
```

### Bridge Not Connecting

```bash
# Check bridge logs
docker-compose logs bridge

# Verify serial port
docker exec -it meshcore-bridge ls -l /dev/ttyACM0

# Test serial manually
screen /dev/ttyACM0 115200
```

### MQTT Connection Issues

```bash
# Test MQTT connection
mosquitto_pub -h your-mqtt-broker -u username -P password -t test -m "hello"

# Check bridge MQTT logs
docker-compose logs bridge | grep MQTT
```

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d

# Run migrations manually
docker exec -it meshcore-web python manage.py migrate
```

### Web Interface Not Loading

```bash
# Check web logs
docker-compose logs web

# Restart web service
docker-compose restart web

# Check if port is accessible
curl http://localhost:8000/meshcore/
```

## Maintenance

### Backup Database

```bash
# Backup PostgreSQL
docker exec meshcore-postgres pg_dump -U meshcore meshcore > backup.sql

# Restore
docker exec -i meshcore-postgres psql -U meshcore meshcore < backup.sql
```

### Update System

```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build

# Remove old images
docker image prune -a
```

### View Statistics

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Clean up
docker system prune -a
```

## Security Recommendations

1. **Change Default Passwords**
   ```bash
   docker exec -it meshcore-web python manage.py changepassword admin
   ```

2. **Use Strong Secrets**
   - Generate secure `DJANGO_SECRET_KEY`
   - Use strong database passwords
   - Secure MQTT credentials

3. **Enable Firewall**
   ```bash
   sudo ufw allow 22/tcp    # SSH
   sudo ufw allow 8000/tcp  # Web (or use Cloudflare Tunnel)
   sudo ufw allow 9443/tcp  # Portainer
   sudo ufw enable
   ```

4. **Regular Updates**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Update Docker images
   docker-compose pull && docker-compose up -d
   ```

## Performance Tuning

### For Raspberry Pi 4

```yaml
# In docker-compose.yml, add resource limits:
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
```

### Optimize PostgreSQL

```bash
# Edit postgresql.conf in container
docker exec -it meshcore-postgres bash
vi /var/lib/postgresql/data/postgresql.conf

# Add:
shared_buffers = 128MB
effective_cache_size = 512MB
maintenance_work_mem = 64MB
```

## Support

- **MeshCore**: https://github.com/ripplebiz/MeshCore
- **RAK4631**: https://docs.rakwireless.com/Product-Categories/WisBlock/RAK4631/Overview/
- **Django**: https://docs.djangoproject.com/

## License

This project integrates with MeshCore, which is licensed under its own terms. Please review the MeshCore license at https://github.com/ripplebiz/MeshCore.
