# Database-Driven Configuration System

## 🎉 Major Architecture Change

The MeshCore-Bridge now uses **100% database-driven configuration**. No more editing `.env` files or `docker-compose.yml`!

---

## **How It Works Now**

### **Everything Configured Through Web Interface**

```
┌──────────────────────────────────────┐
│  Configuration Page (/configuration)  │
│  Save settings to database            │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  PostgreSQL Database                  │
│  meshcore_bridgeconfiguration table  │
└────────────┬─────────────────────────┘
             │ ◄── Polled every 10 seconds
             ▼
┌──────────────────────────────────────┐
│  Bridge Service (meshcore-bridge)     │
│  Auto-reloads when config changes    │
└──────────────────────────────────────┘
```

---

## **The Two Configuration Systems Explained**

### 1. **Configuration Page** (`/meshcore/configuration/`)

**Purpose**: Configure the background MeshCore Bridge service

**What it controls**:
- ✅ **MQTT Broker Settings** (enable/disable, broker address, credentials)
- ✅ **RAK4631 Serial Connection** (enable/disable, COM port, baud rate)
- ✅ **Bridge Behavior** (auto-acknowledge, store packets, forward to MQTT)

**When to use**:
- Set up automatic data collection from your primary RAK4631
- Configure MQTT publishing for external systems
- Production/monitoring setup

**Features**:
- 🔌 Test MQTT connection before saving
- 🔌 Test Serial connection before saving
- 💾 All settings saved to database
- ⚡ Bridge auto-reloads configuration (10s polling)
- ✅ No restart required!

---

### 2. **Device Connections Page** (`/meshcore/connections/`)

**Purpose**: Interactive device management for testing and firmware flashing

**What it controls**:
- ✅ **Multiple Devices** (Serial, Bluetooth, HTTP, TCP)
- ✅ **On-Demand Connections** (connect when needed, disconnect when done)
- ✅ **Firmware Flashing** (use Web Serial API to flash devices)

**When to use**:
- Flash firmware to devices
- Test multiple devices
- Quick connection testing
- Manual device interaction

**Features**:
- 🔍 Scan for serial ports
- 🔍 Scan for Bluetooth devices
- 💾 Save connection configurations
- ⚡ Connect/disconnect on demand
- 🔧 Perfect for development/testing

---

## **Key Differences Summary**

| Feature | Configuration Page | Connections Page |
|---------|-------------------|------------------|
| **Controls** | Background bridge service | Interactive web UI |
| **Devices** | 1 primary RAK4631 | Multiple any devices |
| **Storage** | Database (auto-reloads) | Database (manual connection) |
| **Auto-Runs** | Yes, continuously | No, on-demand only |
| **MQTT** | Yes, can publish | No |
| **Use Case** | Production monitoring | Development/flashing |

---

## **How to Use (Step by Step)**

### **Configure Background Bridge Service**

1. **Go to Configuration Page**
   - Navigate to: http://localhost:8000/meshcore/configuration/

2. **Configure MQTT (Optional)**
   - Check "Enable MQTT Connection"
   - Enter broker address (e.g., `mqtt.example.com` or `192.168.1.100`)
   - Set port (default: 1883)
   - Enter credentials if required
   - Click **"Test MQTT Connection"**
   - ✅ Should show "Successfully connected"

3. **Configure Serial Port for RAK4631**
   - Check "Enable Serial Connection"
   - Click **"Scan Ports"** to find COM ports
   - Select your RAK4631 port (marked with ⭐)
   - Choose baud rate (default: 115200)
   - Click **"Test Serial Connection"**
   - ✅ Should show "Successfully connected"

4. **Configure Bridge Behavior**
   - Enable "Auto-Acknowledge Messages" (recommended)
   - Enable "Store Packets in Database" (recommended)
   - Enable "Forward to MQTT" (if MQTT is configured)

5. **Save Configuration**
   - Click **"Save Configuration"** button (top right)
   - ✅ Should show "Configuration saved successfully!"
   - 🔄 Bridge will reload configuration within 10 seconds
   - ✅ Check bridge logs to see it reconnect

---

### **Use Device Connections for Testing**

1. **Go to Device Connections Page**
   - Navigate to: http://localhost:8000/meshcore/connections/

2. **Add a Device**
   - Click **"New Connection"**
   - Choose connection type
   - Scan for ports or enter manually
   - Click **"Connect Device"**

3. **Use for Firmware Flashing**
   - Add device via Connections page
   - Go to Flasher page
   - Flash firmware using Web Serial API

---

## **Windows COM Port Configuration**

### **Finding Your COM Port**

**Method 1: Device Manager**
1. Press `Win + X` → Device Manager
2. Expand "Ports (COM & LPT)"
3. Look for your device (e.g., "USB Serial Device (COM3)")

**Method 2: PowerShell**
```powershell
[System.IO.Ports.SerialPort]::getportnames()
```

**Method 3: Web Interface**
1. Go to Configuration page
2. Enable Serial Connection
3. Click **"Scan Ports"**
4. Your ports appear in dropdown

---

## **What Changed from Old System**

### **Before** (Environment Variables)
```yaml
# docker-compose.yml
environment:
  - SERIAL_PORT=/dev/ttyACM0  # ❌ Hard-coded, Linux-only
  - MQTT_BROKER=mqtt.example.com  # ❌ Must restart to change
```

Problems:
- ❌ Must edit files
- ❌ Must rebuild containers
- ❌ Must restart services
- ❌ Linux paths don't work on Windows
- ❌ No way to test before applying

### **After** (Database-Driven)
```
Configuration Page → Database → Bridge Service
```

Benefits:
- ✅ Edit through web UI
- ✅ Test before saving
- ✅ No restart needed (auto-reloads)
- ✅ Works on Windows/Linux/Mac
- ✅ Change takes effect in ~10 seconds
- ✅ Connection status updated in real-time

---

## **Technical Details**

### **How Auto-Reload Works**

1. User saves configuration in web UI
2. Configuration saved to `meshcore_bridgeconfiguration` table
3. Bridge service polls database every 10 seconds
4. If `updated_at` changed, bridge reloads configuration
5. If settings changed, bridge reconnects automatically
6. Connection status updated in database

### **Database Schema**

```sql
CREATE TABLE meshcore_bridgeconfiguration (
    id INTEGER PRIMARY KEY,
    
    -- MQTT Settings
    mqtt_broker VARCHAR(255),
    mqtt_port INTEGER DEFAULT 1883,
    mqtt_username VARCHAR(255),
    mqtt_password VARCHAR(255),
    mqtt_topic_prefix VARCHAR(255) DEFAULT 'meshcore',
    mqtt_enabled BOOLEAN DEFAULT FALSE,
    mqtt_connected BOOLEAN DEFAULT FALSE,
    mqtt_last_test TIMESTAMP,
    mqtt_last_error TEXT,
    
    -- Serial Settings
    serial_port VARCHAR(255),
    serial_baud INTEGER DEFAULT 115200,
    serial_enabled BOOLEAN DEFAULT FALSE,
    serial_connected BOOLEAN DEFAULT FALSE,
    serial_last_test TIMESTAMP,
    serial_last_error TEXT,
    
    -- Behavior
    auto_acknowledge BOOLEAN DEFAULT TRUE,
    store_packets BOOLEAN DEFAULT TRUE,
    forward_to_mqtt BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### **New Components**

1. **`config_loader.py`** (Bridge Service)
   - Reads configuration from PostgreSQL
   - Polls for changes
   - Updates connection status

2. **`views_config.py`** (Django App)
   - API endpoints for testing connections
   - Configuration save/load
   - Status updates

3. **Updated Configuration Page**
   - Test buttons for both connections
   - Real-time status badges
   - Port scanning integration
   - User-friendly form

---

## **API Endpoints**

### Test MQTT Connection
```http
POST /meshcore/api/config/test-mqtt/
Content-Type: application/json

{
  "mqtt_broker": "mqtt.example.com",
  "mqtt_port": 1883,
  "mqtt_username": "user",
  "mqtt_password": "pass"
}

Response:
{
  "success": true,
  "message": "Successfully connected to mqtt.example.com:1883"
}
```

### Test Serial Connection
```http
POST /meshcore/api/config/test-serial/
Content-Type: application/json

{
  "serial_port": "COM3",
  "serial_baud": 115200
}

Response:
{
  "success": true,
  "message": "Successfully connected to COM3 at 115200 baud"
}
```

### Save Configuration
```http
POST /meshcore/api/config/save/
Content-Type: application/json

{
  "mqtt_enabled": true,
  "mqtt_broker": "mqtt.example.com",
  "mqtt_port": 1883,
  "serial_enabled": true,
  "serial_port": "COM3",
  "serial_baud": 115200,
  "auto_acknowledge": true,
  "store_packets": true,
  "forward_to_mqtt": true
}

Response:
{
  "success": true,
  "message": "Configuration saved successfully"
}
```

---

## **Testing the New System**

### **1. Access Configuration Page**
http://localhost:8000/meshcore/configuration/

### **2. Test MQTT Connection**
1. Check "Enable MQTT Connection"
2. Enter broker details
3. Click **"Test MQTT Connection"**
4. ✅ Should show success or error message
5. Status badge updates (Connected/Disconnected)

### **3. Test Serial Connection**
1. Check "Enable Serial Connection"
2. Click **"Scan Ports"** button
3. Select your COM port from dropdown
4. Click **"Test Serial Connection"**
5. ✅ Should show success or error message
6. Status badge updates (Connected/Disconnected)

### **4. Save Configuration**
1. Click **"Save Configuration"** (top right)
2. ✅ Success message appears
3. Bridge service reloads within 10 seconds
4. Check bridge logs to see reconnection

### **5. Verify Bridge Picked Up Changes**
```bash
docker logs meshcore-bridge --tail 20
```

Should see:
```
INFO - Configuration changed, reloading...
INFO - Serial configuration changed, reconnecting...
INFO - Connecting to serial port COM3 at 115200 baud...
INFO - Serial connection established
```

---

## **Advantages of New System**

### **For Users**
✅ No file editing  
✅ No container restarts  
✅ Test before applying  
✅ Real-time status feedback  
✅ Works on all platforms (Windows/Linux/Mac)  
✅ User-friendly interface  

### **For Developers**
✅ Configuration in database  
✅ Auto-reload mechanism  
✅ Connection status tracking  
✅ Error logging  
✅ API-driven  
✅ Testable  

### **For Production**
✅ No downtime for config changes  
✅ Configuration history in database  
✅ Centralized management  
✅ Remote configuration possible  
✅ Status monitoring built-in  

---

## **Migration from Old System**

### **Old Way (Deprecated)**
```bash
# Edit .env file
nano .env
# Change: SERIAL_PORT=COM3

# Rebuild and restart
docker-compose down
docker-compose up -d
# Wait for restart...
```

### **New Way (Current)**
```bash
# Just use the web interface!
1. Go to http://localhost:8000/meshcore/configuration/
2. Click "Scan Ports"
3. Select COM3
4. Click "Test"
5. Click "Save"
# Configuration applied in 10 seconds!
```

---

## **Windows-Specific Notes**

### **COM Port Format**
- ✅ Use: `COM3`, `COM4`, `COM5`, etc.
- ❌ Don't use: `/dev/ttyACM0` (Linux format)

### **Scanning Works!**
The **"Scan Ports"** button will detect all available COM ports on Windows and show:
- Port name (COM3, COM4, etc.)
- Device description
- ⭐ MeshCore devices automatically identified

### **No Special Docker Configuration Needed**
- Bridge service doesn't need direct device access anymore
- The **web container** handles port scanning
- The **bridge service** just reads from database
- Configuration is platform-independent!

---

## **Troubleshooting**

### **"Test MQTT Connection" fails**
- Check broker address is correct
- Verify broker is running and reachable
- Check credentials if required
- Ensure port 1883 is open

### **"Test Serial Connection" fails**
- Verify device is plugged in
- Check Device Manager for COM port
- Try different USB cable
- Install drivers if needed

### **Bridge not reconnecting after save**
- Wait 10 seconds (configuration check interval)
- Check bridge logs: `docker logs meshcore-bridge`
- Verify configuration was saved (reload page)
- Check connection status badges

### **"Scan Ports" shows no ports**
- Check Device Manager for COM ports
- Ensure device is connected
- Try different USB port
- Restart container if needed

---

## **Best Practices**

### **Recommended Workflow**

1. **Always test before saving**
   - Use "Test MQTT Connection" button
   - Use "Test Serial Connection" button
   - Only save if tests pass

2. **Monitor bridge logs**
   ```bash
   docker logs -f meshcore-bridge
   ```
   Watch for configuration reloads and connection status

3. **Use status badges**
   - Green = Connected
   - Red = Disconnected
   - Gray = Disabled

4. **Enable only what you need**
   - Don't enable MQTT if you're not using it
   - Don't enable Serial if device isn't connected
   - Disabled connections don't cause errors

---

## **Configuration Scenarios**

### **Scenario 1: Just Testing (Most Users)**
```
MQTT: Disabled ⚫
Serial: Disabled ⚫
```

Use **Device Connections** page for all device interaction.

**Why**: No background service needed, everything on-demand.

---

### **Scenario 2: Local Monitoring (No Cloud)**
```
MQTT: Disabled ⚫
Serial: Enabled ✅ → COM3
```

Bridge collects data from RAK4631, stores in local database only.

**Why**: Monitor mesh network locally without external dependencies.

---

### **Scenario 3: Full Production (Cloud Integration)**
```
MQTT: Enabled ✅ → mqtt.yourserver.com
Serial: Enabled ✅ → COM3
```

Bridge collects from RAK4631, publishes to MQTT, stores in database.

**Why**: Full integration with external systems, cloud dashboards, etc.

---

### **Scenario 4: MQTT Only (Remote Device)**
```
MQTT: Enabled ✅ → mqtt.example.com
Serial: Disabled ⚫
```

Bridge subscribes to MQTT for mesh data from remote bridge.

**Why**: Multiple bridge instances, centralized MQTT broker.

---

## **Files Changed**

### **New Files**
1. ✅ `bridge/config_loader.py` - Database configuration loader
2. ✅ `web/apps/meshcore/views_config.py` - Configuration APIs
3. ✅ `web/apps/meshcore/templates/meshcore/configuration.html` - New UI
4. ✅ `web/apps/meshcore/migrations/0004_update_bridge_configuration.py`

### **Modified Files**
1. ✅ `bridge/meshcore_bridge.py` - Database integration
2. ✅ `bridge/Dockerfile` - Include config_loader.py
3. ✅ `bridge/requirements.txt` - Added psycopg2-binary
4. ✅ `web/apps/meshcore/models.py` - Enhanced BridgeConfiguration
5. ✅ `web/apps/meshcore/urls.py` - Added configuration APIs
6. ✅ `docker-compose.yml` - DATABASE_URL instead of individual env vars
7. ✅ `.env` - Removed SERIAL_PORT override

---

## **Quick Start Guide**

### **1. Access the Application**
http://localhost:8000/meshcore/

### **2. Go to Configuration**
Click "Configuration" in the sidebar (or go to `/meshcore/configuration/`)

### **3. Find Your COM Port**
- Check "Enable Serial Connection"
- Click **"Scan Ports"**
- Your Windows COM ports appear in dropdown
- MeshCore devices marked with ⭐

### **4. Test Connection**
- Select your port (e.g., COM3)
- Click **"Test Serial Connection"**
- ✅ Should show success message
- Status badge turns green

### **5. Save & Done!**
- Click **"Save Configuration"**
- Bridge reconnects within 10 seconds
- No restart needed!

---

## **Monitoring**

### **Check Bridge Status**
```bash
# View logs
docker logs -f meshcore-bridge

# Should see:
INFO - Configuration loaded - Serial: enabled, MQTT: disabled
INFO - Connecting to serial port COM3 at 115200 baud...
INFO - Serial connection established
INFO - Bridge running, waiting for packets...
```

### **Check Connection Status in Web UI**
- Go to Dashboard
- Bridge Status card shows:
  - Serial: 🟢 Connected / 🔴 Disconnected
  - MQTT: 🟢 Connected / 🔴 Disconnected
  - RAK4631: 🟢 Connected / 🔴 Disconnected

---

## **Success!**

You now have a **fully database-driven configuration system**:

✅ **No more .env file editing**  
✅ **No more container restarts**  
✅ **Test connections before saving**  
✅ **Auto-reload configuration**  
✅ **Works perfectly on Windows**  
✅ **User-friendly web interface**  

Configure everything through the web UI at:  
**http://localhost:8000/meshcore/configuration/**

---

**Last Updated**: January 2, 2026  
**Status**: ✅ Production Ready
