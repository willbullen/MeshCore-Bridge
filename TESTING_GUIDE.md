# MeshCore-Bridge Testing Guide

This guide covers testing all functionality of the MeshCore-Bridge application.

## Prerequisites

1. **Database Setup**
   ```bash
   # If using Docker (recommended)
   docker-compose up -d postgres redis
   
   # Apply migrations
   docker exec -it meshcore-web python manage.py migrate
   
   # Create superuser
   docker exec -it meshcore-web python manage.py createsuperuser
   ```

2. **Development Server**
   ```bash
   # Start all services
   docker-compose up -d
   
   # Or run Django locally
   cd web
   python manage.py runserver
   ```

## Testing Each Page

### 1. Dashboard (`/meshcore/`)

**Expected Functionality:**
- Display bridge status (running/stopped)
- Show connection status for Serial, MQTT, RAK4631
- Display node counts (total and online)
- Show message counts (24h)
- List recent messages
- Show message type breakdown

**Test Steps:**
1. Navigate to `/meshcore/`
2. Verify all statistics are displayed
3. Check that refresh button works
4. Verify recent messages show (if any in database)

**Pass Criteria:**
- ✅ No "dummy data" warnings
- ✅ Statistics show 0 if no data (not errors)
- ✅ Bridge status cards display correctly
- ✅ Auto-refresh works (every 10 seconds)

---

### 2. Device Connections (`/meshcore/connections/`)

**Expected Functionality:**
- Scan for serial ports (USB)
- Scan for Bluetooth devices
- Add new device connections
- Connect/disconnect devices
- Delete device connections
- View saved connections

**Test Steps:**

#### Serial Port Scanning:
1. Click "New Connection" button
2. Modal should auto-scan for serial ports
3. Verify serial ports appear in dropdown
4. MeshCore devices should be marked with ⭐

#### Manual Serial Port Addition:
1. Click "Scan Ports" button
2. Select a port from dropdown
3. Enter device name (optional)
4. Enable "Auto-connect on startup" if desired
5. Click "Connect Device"

#### Bluetooth Scanning:
1. Select "Bluetooth" connection type
2. Click "Scan Devices" button
3. Browser popup should request permission
4. Selected device name should populate field

#### HTTP/TCP Connections:
1. Select "HTTP" or "TCP"
2. Enter appropriate URL/host/port
3. Save device configuration

**Pass Criteria:**
- ✅ Serial port scanning works and shows actual ports
- ✅ Can create device connections
- ✅ Devices appear in "Active Devices" list
- ✅ Connect/Disconnect buttons functional
- ✅ Delete confirmation works
- ✅ No "Device Manager Coming Soon" messages

---

### 3. Firmware Flasher (`/meshcore/flasher/`)

**Expected Functionality:**
- Display device selection grid
- Show firmware role options
- Scan for serial/USB ports when flashing ESP32
- Request USB device access for nRF52
- Flash firmware to devices
- Show progress and logs
- Open serial console after flashing

**Test Steps:**

#### ESP32 Device Flashing:
1. Navigate to `/meshcore/flasher/`
2. Select an ESP32 device (e.g., Heltec V3)
3. Select firmware role (e.g., "Client GUI")
4. Choose firmware version
5. Click "Flash Firmware"
6. Browser should prompt for serial port selection
7. Verify scanning shows available ports
8. Select port and wait for flashing to complete

#### nRF52 Device Flashing (RAK4631):
1. Select "RAK WisBlock 4631"
2. Select firmware role (e.g., "Companion Radio Bluetooth")
3. Read DFU mode instructions
4. Put device in DFU mode (double-press RESET)
5. Click "Connect to Device (DFU Mode)"
6. Browser should show USB device picker
7. Select "nRF52 DFU" device
8. Click "Flash Firmware"

**Pass Criteria:**
- ✅ Device images load correctly
- ✅ Serial port scanning works (ESP32)
- ✅ USB device picker shows (nRF52)
- ✅ Firmware downloads from GitHub
- ✅ Progress indicator updates
- ✅ Flash log shows detailed output
- ✅ Success/error states display correctly
- ✅ Console opens after successful flash

---

### 4. Nodes List (`/meshcore/nodes/`)

**Expected Functionality:**
- List all nodes in mesh network
- Filter by online/offline status
- Filter by node type
- Show node details (name, hash, battery, signal)
- Navigate to node detail page

**Test Steps:**
1. Navigate to `/meshcore/nodes/`
2. Verify nodes display (or empty state if no nodes)
3. Click "Online" filter
4. Click "Offline" filter
5. Click on a node to view details

**Pass Criteria:**
- ✅ Nodes display from database
- ✅ Empty state shows if no nodes
- ✅ Filters work correctly
- ✅ Node cards show accurate information
- ✅ Status indicators (online/offline) correct

---

### 5. Messages List (`/meshcore/messages/`)

**Expected Functionality:**
- Display all received messages
- Filter by message type
- Filter by channel
- Show sender/recipient information
- Display signal strength (SNR/RSSI)
- Show timestamp

**Test Steps:**
1. Navigate to `/meshcore/messages/`
2. Verify messages display (or empty state)
3. Use type filter dropdown
4. Check timestamp formatting
5. Verify MQTT published indicator

**Pass Criteria:**
- ✅ Messages display from database
- ✅ Empty state shows if no messages
- ✅ Filters work correctly
- ✅ All message fields display accurately
- ✅ No template errors

---

### 6. Map View (`/meshcore/map/`)

**Expected Functionality:**
- Display interactive map
- Show nodes with GPS coordinates
- Display node markers on map
- Show node info on marker click

**Test Steps:**
1. Navigate to `/meshcore/map/`
2. Verify map loads
3. Check for node markers (if nodes have coordinates)
4. Click on markers to see node info

**Pass Criteria:**
- ✅ Map initializes correctly
- ✅ Nodes with coordinates appear as markers
- ✅ Marker popups show node information
- ✅ No JavaScript errors

---

### 7. Telemetry (`/meshcore/telemetry/`)

**Expected Functionality:**
- Display node telemetry data
- Show battery levels
- Display signal metrics
- Show packet counts
- Display uptime statistics

**Test Steps:**
1. Navigate to `/meshcore/telemetry/`
2. Verify telemetry cards display
3. Check for accurate data representation

**Pass Criteria:**
- ✅ Telemetry data displays from database
- ✅ Empty state if no telemetry
- ✅ Charts/graphs render correctly
- ✅ Values are accurate

---

### 8. Channels (`/meshcore/channels/`)

**Expected Functionality:**
- List all mesh channels
- Show channel statistics
- Display active/inactive status

**Test Steps:**
1. Navigate to `/meshcore/channels/`
2. Verify channels display
3. Check channel details

**Pass Criteria:**
- ✅ Channels display from database
- ✅ Empty state if no channels
- ✅ Channel information accurate

---

### 9. Configuration (`/meshcore/configuration/`)

**Expected Functionality:**
- Display bridge configuration
- Edit MQTT settings
- Edit serial port settings
- Save configuration changes

**Test Steps:**
1. Navigate to `/meshcore/configuration/`
2. Update MQTT broker settings
3. Update serial port
4. Click Save
5. Verify changes persist

**Pass Criteria:**
- ✅ Configuration form displays
- ✅ Current settings populated
- ✅ Save functionality works
- ✅ Validation errors display

---

### 10. Media Gallery (`/meshcore/media/`)

**Expected Functionality:**
- Display media files
- Upload images
- Upload voice messages
- Send media to mesh network
- View media details

**Test Steps:**
1. Navigate to `/meshcore/media/`
2. Try uploading an image
3. Try uploading audio
4. View media details
5. Test send functionality

**Pass Criteria:**
- ✅ Media gallery displays
- ✅ Upload works
- ✅ Media files appear in gallery
- ✅ Send functionality works

---

## API Endpoints Testing

### Device Connection APIs

```bash
# Scan serial ports
curl http://localhost:8000/meshcore/api/scan/serial/

# Create device connection
curl -X POST http://localhost:8000/meshcore/api/device/create/ \
  -H "Content-Type: application/json" \
  -d '{"connection_type":"serial","serial_port":"/dev/ttyACM0","baud_rate":115200,"device_name":"My Device"}'

# Connect to device
curl -X POST http://localhost:8000/meshcore/api/device/serial_dev_ttyACM0/connect/

# Disconnect from device
curl -X POST http://localhost:8000/meshcore/api/device/serial_dev_ttyACM0/disconnect/

# Delete device
curl -X DELETE http://localhost:8000/meshcore/api/device/serial_dev_ttyACM0/delete/
```

### Status API

```bash
# Get bridge status
curl http://localhost:8000/meshcore/api/status/

# Get nodes
curl http://localhost:8000/meshcore/api/nodes/

# Get messages
curl http://localhost:8000/meshcore/api/messages/
```

---

## Browser Compatibility

Test the following features in each browser:

### Chrome/Edge (Recommended)
- ✅ Web Serial API (for ESP32 flashing)
- ✅ Web USB API (for nRF52 flashing)
- ✅ Web Bluetooth API (for device scanning)
- ✅ All standard features

### Firefox
- ⚠️ Web Serial API not supported
- ⚠️ Web USB API not supported
- ✅ All other features work

### Safari
- ⚠️ Web Serial API not supported
- ⚠️ Web USB API not supported
- ⚠️ Some CSS features may differ
- ✅ Basic functionality works

---

## Common Issues & Solutions

### Issue: "No module named 'corsheaders'"
**Solution:**
```bash
pip install django-cors-headers
```

### Issue: "pyserial not installed"
**Solution:**
```bash
pip install pyserial
```

### Issue: Web Serial/USB API not available
**Solution:**
- Use Chrome or Edge browser
- Ensure HTTPS (or localhost)
- Check browser flags if needed

### Issue: Serial ports not detected
**Solution (Linux/Mac):**
```bash
ls -l /dev/ttyACM* /dev/ttyUSB*
sudo usermod -aG dialout $USER
# Log out and back in
```

**Solution (Windows):**
- Open Device Manager
- Check "Ports (COM & LPT)"
- Install drivers if needed

### Issue: Database migrations not applied
**Solution:**
```bash
python manage.py migrate
```

---

## Production Testing Checklist

Before deploying to production:

- [ ] All migrations applied
- [ ] Superuser created
- [ ] Static files collected
- [ ] Environment variables configured
- [ ] Database connection tested
- [ ] MQTT broker configured (if using)
- [ ] Serial port permissions set
- [ ] Cloudflare tunnel configured (if using remote access)
- [ ] All pages load without errors
- [ ] Device connections work
- [ ] Firmware flasher functional
- [ ] API endpoints respond correctly
- [ ] No dummy/test data visible
- [ ] Security settings enabled (DEBUG=False)
- [ ] HTTPS enabled (for Web USB/Serial)

---

## Automated Testing

Future enhancements:

```python
# Example test case (to be implemented)
from django.test import TestCase, Client

class DeviceConnectionTests(TestCase):
    def test_scan_serial_ports(self):
        client = Client()
        response = client.get('/meshcore/api/scan/serial/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_create_device_connection(self):
        client = Client()
        response = client.post('/meshcore/api/device/create/', {
            'connection_type': 'serial',
            'serial_port': '/dev/ttyACM0',
            'baud_rate': 115200
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
```

---

## Performance Testing

Monitor these metrics:

1. **Page Load Times**: < 2 seconds
2. **API Response Times**: < 500ms
3. **WebSocket Latency**: < 100ms
4. **Database Query Times**: < 100ms
5. **Memory Usage**: < 512MB

---

## Conclusion

All functionality should work with actual data from the database. There should be no:
- "Coming Soon" placeholders
- Dummy/test data
- Non-functional buttons
- Template errors
- JavaScript console errors

Report any issues found during testing.
