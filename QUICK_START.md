# MeshCore-Bridge Quick Start Guide

Get up and running with MeshCore-Bridge in minutes.

## Option 1: Docker Deployment (Recommended)

### Prerequisites
- Docker and Docker Compose installed
- RAK4631 or ESP32 device with MeshCore firmware (optional)

### Steps

1. **Clone or Download the Repository**
   ```bash
   cd /your/desired/location
   git clone <repository-url>
   cd MeshCore-Bridge
   ```

2. **Configure Environment**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit environment variables
   nano .env
   ```
   
   Key variables to configure:
   ```env
   # Database
   POSTGRES_PASSWORD=your_secure_password_here
   
   # Serial Connection (update for your device)
   SERIAL_PORT=/dev/ttyACM0  # Linux/Mac
   SERIAL_PORT=COM3          # Windows
   
   # MQTT (optional - can leave default for testing)
   MQTT_BROKER=localhost
   MQTT_PORT=1883
   ```

3. **Start Services**
   ```bash
   # Start all services
   docker-compose up -d
   
   # Check status
   docker-compose ps
   
   # View logs
   docker-compose logs -f web
   ```

4. **Run Database Migrations**
   ```bash
   docker exec -it meshcore-web python manage.py migrate
   ```

5. **Create Admin User**
   ```bash
   docker exec -it meshcore-web python manage.py createsuperuser
   ```
   
   Follow prompts to set username and password.

6. **Access the Application**
   - **Web UI**: http://localhost:8000/meshcore/
   - **Admin Panel**: http://localhost:8000/admin/
   
   Login with the credentials you just created.

---

## Option 2: Local Development Setup

### Prerequisites
- Python 3.10 or higher
- PostgreSQL (or use Docker for PostgreSQL only)
- Redis (or use Docker for Redis only)

### Steps

1. **Install Python Dependencies**
   ```bash
   cd MeshCore-Bridge/web
   pip install -r requirements.txt
   ```

2. **Setup Database (if not using Docker)**
   ```bash
   # Install PostgreSQL
   # Create database
   createdb meshcore
   
   # Or use Docker for database only
   docker run -d \
     --name meshcore-postgres \
     -e POSTGRES_DB=meshcore \
     -e POSTGRES_USER=meshcore \
     -e POSTGRES_PASSWORD=meshcore \
     -p 5432:5432 \
     postgres:15
   ```

3. **Configure Django Settings**
   ```bash
   cd web
   
   # Copy local settings template
   cp valentia_backend/settings_local.py.example valentia_backend/settings_local.py
   
   # Edit settings
   nano valentia_backend/settings_local.py
   ```

4. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

8. **Access Application**
   - Visit: http://localhost:8000/meshcore/

---

## First-Time Setup

### 1. Add Your First Device

1. Navigate to **Connections** page
2. Click **"New Connection"** button
3. Select connection type:
   - **Serial (USB)**: For RAK4631 or ESP32 connected via USB
   - **Bluetooth**: For BLE devices
   - **HTTP/TCP**: For network-connected devices
4. For Serial:
   - Click **"Scan Ports"** to find your device
   - Select the port (MeshCore devices marked with ⭐)
   - Choose baud rate (115200 for most devices)
   - Give it a friendly name
5. Click **"Connect Device"**

### 2. Flash Firmware (Optional)

If you need to flash firmware to a new device:

1. Navigate to **Flasher** utility
2. Select your device type (RAK4631, Heltec V3, T-Deck, etc.)
3. Choose firmware role:
   - **Companion (Bluetooth/USB)**: For chat applications
   - **Repeater**: For extending mesh range
   - **Room Server**: For local mesh rooms
4. Select firmware version (latest recommended)
5. Connect device and follow on-screen instructions
6. Wait for flashing to complete

**Note**: Firmware flasher requires Chrome or Edge browser for Web Serial/USB APIs.

### 3. Configure Bridge (Optional)

1. Navigate to **Configuration** page
2. Update settings:
   - **MQTT Broker**: If publishing to external MQTT
   - **Serial Port**: Your RAK4631 connection
   - **Filters**: Which message types to process
3. Click **Save**

---

## Verify Everything Works

### Check Dashboard
- Go to Dashboard
- Verify bridge status shows "Running"
- Check connection indicators:
  - Serial: Should be green if device connected
  - MQTT: Green if broker configured and reachable
  - RAK4631: Green if device connected

### View Nodes
- Navigate to **Nodes** page
- If devices are transmitting, you should see nodes appear
- Online nodes show green indicator

### Monitor Messages
- Go to **Messages** page
- Messages from mesh network will appear here
- Use filters to sort by type

---

## Common Issues

### Issue: Port permission denied (Linux/Mac)
```bash
# Add user to dialout group
sudo usermod -aG dialout $USER

# Log out and back in for changes to take effect

# Or run with sudo (not recommended)
sudo docker-compose up -d
```

### Issue: Can't find serial port (Windows)
1. Open Device Manager
2. Check "Ports (COM & LPT)"
3. Look for your device
4. Install drivers if needed:
   - RAK4631: Nordic USB drivers
   - ESP32: CP210x or CH340 drivers

### Issue: Web Serial API not available
- Use Chrome or Edge browser (required)
- Ensure you're using HTTPS or localhost
- Check browser version (must be recent)

### Issue: Database connection error
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart database
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### Issue: Static files not loading
```bash
# Collect static files
docker exec -it meshcore-web python manage.py collectstatic --noinput

# Or if running locally
python manage.py collectstatic --noinput
```

---

## Next Steps

1. **Explore Features**
   - Try different connection types
   - Send messages between devices
   - View telemetry data
   - Use the map view

2. **Remote Access** (Optional)
   - Setup Cloudflare Tunnel for remote access
   - See DEPLOYMENT_GUIDE.md for details

3. **MQTT Integration** (Optional)
   - Connect to external MQTT broker
   - Publish mesh data to other systems
   - See README.md for MQTT topics

4. **Read Documentation**
   - TESTING_GUIDE.md - Testing all features
   - DEPLOYMENT_GUIDE.md - Production deployment
   - README.md - Full feature overview

---

## Production Deployment

For production use:

1. Change default passwords in `.env`
2. Set `DEBUG=False` in Django settings
3. Configure proper SECRET_KEY
4. Setup HTTPS (required for Web Serial/USB)
5. Configure firewall rules
6. Setup automated backups
7. Enable monitoring

See DEPLOYMENT_GUIDE.md for full details.

---

## Getting Help

- Check logs: `docker-compose logs -f`
- View specific service: `docker-compose logs -f web`
- Restart services: `docker-compose restart`
- Stop all: `docker-compose down`

For issues:
1. Check TESTING_GUIDE.md
2. Review logs for errors
3. Consult MeshCore documentation
4. Check GitHub issues

---

## Success!

You now have a fully functional MeshCore-Bridge installation!

- Dashboard shows real-time mesh network activity
- Device connections can be managed
- Firmware can be flashed to devices
- All features use actual data (no dummy data)

Happy meshing! 📡
