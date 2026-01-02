# MeshCore-Bridge - Windows Setup Guide

## Understanding Configuration vs Device Connections

You've noticed two different places for device configuration. Here's the **important difference**:

### 1. **Configuration Page** (`/meshcore/configuration/`)

**Purpose**: Backend MeshCore Bridge Service Settings

- This configures the **background bridge service** (meshcore-bridge container)
- Used for **continuous data collection** from ONE primary device
- Bridges data from serial device → Database → MQTT
- Runs automatically in the background
- **This is what's showing the error in your logs**

**Use this when**:
- You have a RAK4631 permanently connected to collect mesh network data
- You want automatic packet parsing and database storage
- You need MQTT publishing for external systems

**Settings**:
- Serial Port (e.g., COM3, COM4)
- MQTT broker configuration
- Auto-acknowledge settings
- Packet filters

---

### 2. **Device Connections Page** (`/meshcore/connections/`)

**Purpose**: Web UI Device Management

- This is for **interactive device management** through the web interface
- Can manage **MULTIPLE devices**
- Used for:
  - Testing connections
  - Firmware flashing
  - Manual device interaction
  - Temporary connections

**Use this when**:
- You want to flash firmware to a device
- You need to test multiple devices
- You want manual control over connections
- You're working with different device types

**Features**:
- Serial, Bluetooth, HTTP, TCP connections
- Port scanning
- Connect/disconnect on demand
- No automatic background processing

---

## The Error You're Seeing

```
meshcore-bridge | ERROR - Failed to connect to serial port: 
[Errno 2] could not open port /dev/ttyACM0: 
[Errno 2] No such file or directory: '/dev/ttyACM0'
```

**Issue**: The bridge service is trying to use `/dev/ttyACM0` (Linux port) instead of `COM3`, `COM4`, etc. (Windows ports).

**This is the CONFIGURATION page / bridge service trying to connect**

---

## Fixing for Windows

### Option 1: Update Environment Variables (Recommended)

1. **Find your COM port**:
   - Open Device Manager (Win + X → Device Manager)
   - Expand "Ports (COM & LPT)"
   - Look for your RAK4631 or USB-Serial device
   - Note the COM port (e.g., COM3, COM4)

2. **Update docker-compose.yml**:

Find this line (around line 112):
```yaml
- SERIAL_PORT=${SERIAL_PORT:-/dev/ttyACM0}
```

Change to:
```yaml
- SERIAL_PORT=${SERIAL_PORT:-COM3}
```
*(Replace COM3 with your actual port)*

3. **Enable device passthrough** (Windows + Docker):

Uncomment and update these lines (around lines 120-122):
```yaml
devices:
  - //./COM3://./COM3
privileged: true
```

**Note**: Windows COM port syntax in Docker is `//./COMx`

4. **Rebuild and restart**:
```bash
docker-compose down
docker-compose build bridge
docker-compose up -d
```

---

### Option 2: Disable Bridge Service (If Not Needed)

If you're **not using the automatic bridge service**, you can disable it:

**In docker-compose.yml**, comment out or remove the bridge service:
```yaml
# bridge:
#   build:
#     context: ./bridge
#     dockerfile: Dockerfile
#   container_name: meshcore-bridge
#   # ... rest of config
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

**When to do this**:
- You only want to use the web UI for device management
- You don't need automatic packet collection
- You're just testing/flashing firmware

---

## Complete Windows Configuration Example

### docker-compose.yml (bridge section)

```yaml
# MeshCore Bridge (Serial to MQTT)
bridge:
  build:
    context: ./bridge
    dockerfile: Dockerfile
  container_name: meshcore-bridge
  environment:
    - SERIAL_PORT=COM3              # ← Windows COM port
    - SERIAL_BAUD=115200
    - MQTT_BROKER=                  # ← Empty = disabled
    - MQTT_PORT=1883
    - MQTT_USERNAME=
    - MQTT_PASSWORD=
    - MQTT_TOPIC_PREFIX=meshcore
  # Windows serial port passthrough
  devices:
    - //./COM3://./COM3             # ← Windows device syntax
  privileged: true                  # ← Required for device access
  networks:
    - meshcore-network
  restart: unless-stopped
  depends_on:
    - web
```

---

## Recommended Windows Workflow

### For Most Users (Testing/Development):

1. **Disable or don't configure the bridge service**
   - Let it fail to connect (it's optional)
   - Or remove it from docker-compose.yml

2. **Use Device Connections page for everything**
   - Go to `/meshcore/connections/`
   - Click "Scan Ports" to find COM ports
   - Connect when you need to flash firmware or test
   - Disconnect when done

### For Advanced Users (Data Collection):

1. **Configure bridge service properly**
   - Set correct COM port in docker-compose.yml
   - Enable device passthrough
   - Configure MQTT if needed

2. **Use Configuration page** (`/meshcore/configuration/`)
   - Set the same COM port
   - Configure data collection settings

3. **Use Device Connections for other tasks**
   - Flash firmware to other devices
   - Test connections
   - Manage multiple devices

---

## Quick Fix Right Now

**To stop the errors immediately**:

### Method 1: Comment out bridge in docker-compose.yml

```yaml
# bridge:
#   build:
#     context: ./bridge
#   # ... (comment out entire section)
```

Then:
```bash
docker-compose down
docker-compose up -d
```

### Method 2: Set empty serial port

In docker-compose.yml line 112:
```yaml
- SERIAL_PORT=
```

This will make the bridge service run but not try to connect to any port.

---

## Windows COM Port Tips

### Finding Your Port
```powershell
# In PowerShell
Get-WmiObject Win32_SerialPort | Select-Object Name, DeviceID

# Or use Device Manager GUI
# Win + X → Device Manager → Ports (COM & LPT)
```

### Common Windows Ports
- **COM3** - Most common for USB devices
- **COM4** - Second USB device
- **COM1/COM2** - Usually onboard serial ports
- **Higher numbers** - USB-to-Serial adapters

### Driver Issues
If your RAK4631 doesn't show up:
1. Install **Nordic USB driver** or **Segger J-Link driver**
2. Try a different USB cable (must be data cable, not charge-only)
3. Check Windows Update for drivers

---

## Testing Your Setup

### 1. Check if port exists in Windows
```powershell
[System.IO.Ports.SerialPort]::getportnames()
```

### 2. Test from web UI
1. Go to: http://localhost:8000/meshcore/connections/
2. Click "New Connection"
3. Click "Scan Ports"
4. Your COM ports should appear
5. Select one and test connection

### 3. Check bridge logs
```bash
docker logs meshcore-bridge
```

Should see:
- ✅ "Serial connection established" (if configured correctly)
- ⚠️ "Serial port not available" (acceptable if disabled)
- ❌ "could not open port /dev/ttyACM0" (needs fixing)

---

## Summary

**Two Different Systems**:

| Feature | Configuration Page | Device Connections Page |
|---------|-------------------|------------------------|
| **Purpose** | Background service | Interactive management |
| **Devices** | 1 primary device | Multiple devices |
| **Usage** | Automatic collection | Manual/on-demand |
| **Data Storage** | Saves to database | Testing only |
| **MQTT** | Can publish | No |
| **When to Use** | Production/monitoring | Development/flashing |

**For Windows**:
- Use `COM3`, `COM4`, etc. (not `/dev/ttyACM0`)
- Device syntax: `//./COMx` in Docker
- Most users: Just use Device Connections page
- Advanced users: Configure both for full functionality

**Quick Fix**:
- Update `SERIAL_PORT=COM3` in docker-compose.yml
- Or disable bridge service if not needed
- Rebuild: `docker-compose down && docker-compose up -d`

---

## Need Help?

1. Check Device Manager for your COM port
2. Test connection via web UI first
3. Configure bridge service only if needed
4. Check logs: `docker logs meshcore-bridge`

The web application will work fine even if the bridge service fails - they're independent systems!
