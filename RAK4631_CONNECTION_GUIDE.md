# RAK4631 Serial Connection - Complete Process & Flow

## 🔄 **Complete Connection Flow**

```
┌──────────────────────────────────────────────────────────────┐
│ 1. PHYSICAL CONNECTION                                       │
│    Plug RAK4631 into USB port                                │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. WINDOWS ASSIGNS COM PORT                                  │
│    Device Manager shows: "USB Serial Device (COM6)"          │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. YOU CONFIGURE VIA WEB UI                                  │
│    http://localhost:8000/meshcore/configuration/             │
│    - Enable Serial Connection ☑️                             │
│    - Enter: COM6                                              │
│    - Test (browser opens port)                                │
│    - Save to database                                         │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. DATABASE STORES CONFIGURATION                             │
│    meshcore_bridgeconfiguration:                             │
│      serial_enabled = true                                    │
│      serial_port = "COM6"                                     │
│      serial_baud = 115200                                     │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. BRIDGE POLLS DATABASE (every 10 seconds)                  │
│    - Reads serial_enabled = true                             │
│    - Reads serial_port = "COM6"                              │
│    - Sees configuration changed                              │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. BRIDGE CONNECTS TO COM6                                   │
│    - Opens serial port COM6 at 115200 baud                   │
│    - Connection established                                   │
│    - Updates database: serial_connected = true               │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 7. BRIDGE RECEIVES DATA                                      │
│    - Reads MeshCore packets from RAK4631                     │
│    - Parses packets                                           │
│    - Stores in database                                       │
│    - Publishes to MQTT (if enabled)                          │
└──────────────────────────────────────────────────────────────┘
```

---

## ✅ **Step-by-Step Configuration Process**

### **Step 1: Ensure RAK4631 is Connected**

**Check Device Manager**:
1. Press `Win + X` → Device Manager
2. Expand "Ports (COM & LPT)"
3. Look for:
   - "USB Serial Device (COMx)"
   - "nRF52 USB Device (COMx)"  
   - "Segger J-Link (COMx)"

**Note the COM port number** (e.g., COM6)

---

### **Step 2: Configure in Web Interface**

**Open Configuration Page**:
```
http://localhost:8000/meshcore/configuration/
```

**Fill in the form**:
1. **Enable Serial Connection**: ☑️ Check the box
2. **Serial Port**: Type `COM6` (your port from Step 1)
3. **Baud Rate**: Leave as `115200` (default for RAK4631)

---

### **Step 3: Test Connection (Client-Side)**

**Click "Test Serial Connection" button**:

**What happens**:
1. Browser shows popup: "localhost wants to connect to a serial port"
2. List shows all your serial devices
3. **Select your RAK4631** (might show as "USB Serial Device" or "nRF52")
4. Click "Connect" in the popup

**If successful**:
- ✅ Message: "Successfully opened COM6 at 115200 baud - Port is accessible!"
- Status badge turns green: 🟢 Connected

**If fails**:
- ❌ Error message explains why
- Common issues:
  - Port already open in another program
  - Wrong COM port number
  - Device not properly connected

---

### **Step 4: Save Configuration**

**Click "Save Configuration" button** (top right)

**What happens**:
1. Configuration saved to PostgreSQL database
2. Success message appears
3. Shows what was saved:
   ```
   Serial: COM6
   MQTT: disabled (or your MQTT broker)
   Bridge will reload configuration within 10 seconds...
   ```

---

### **Step 5: Bridge Auto-Reconnects**

**Watch the "Live Bridge Traffic" section** (bottom of page):

**Within 10 seconds, you should see**:
```
INFO - Configuration changed, reloading...
INFO - Serial configuration changed, reconnecting...
INFO - Connecting to serial port COM6 at 115200 baud...
INFO - Serial connection established
INFO - Bridge running, waiting for packets...
```

**If you don't see this**:
- Click "Enable Auto-Refresh" button
- Logs update every 2 seconds
- Watch for connection messages

---

### **Step 6: Verify Connection**

**Three ways to verify**:

**Method 1: Live Traffic Logs** (on Configuration page)
- Enable Auto-Refresh
- Should see: "Serial connection established"
- Should see: "Bridge running, waiting for packets..."

**Method 2: Dashboard**
- Go to: http://localhost:8000/meshcore/
- Bridge Status card → RAK4631: 🟢 Connected

**Method 3: Docker Logs**
```bash
docker logs meshcore-bridge --tail 20
```

---

## 🔧 **Troubleshooting Each Step**

### **Issue: "Serial port not configured, skipping serial connection"**

**Cause**: Database has empty serial_port field

**Debug**:
```bash
docker exec meshcore-web python manage.py show_config
```

**Check**:
- Is `Serial Port:` empty or showing "(empty)"?
- Is `Serial Enabled:` False?

**Fix**:
1. Open Configuration page
2. Verify serial_port field has a value (e.g., "COM6")
3. Verify "Enable Serial Connection" is checked
4. Click "Save Configuration" again
5. **Open browser console (F12)** and check for errors
6. Look for console.log messages showing what's being saved

---

### **Issue: Configuration saves but bridge doesn't connect**

**Possible causes**:

**A. Bridge hasn't reloaded yet**
- Wait 10 seconds (it polls database every 10s)
- Watch Live Traffic logs for "Configuration changed"

**B. COM port not accessible to Docker**
- Check `docker-compose.yml` has your COM port in devices list
- Restart containers: `docker-compose down && docker-compose up -d`

**C. Another program using the port**
- Close Arduino IDE
- Close PuTTY or serial terminals
- Check Task Manager for programs accessing COM ports

---

### **Issue: Test works, but save doesn't**

**Debug the save**:
1. Open Configuration page
2. Press F12 (Developer Console)
3. Go to Console tab
4. Fill in Serial Port: COM6
5. Click "Save Configuration"
6. **Check console for**:
   ```
   Saving configuration...
   Serial Enabled: true
   Serial Port: COM6
   Config to save: {serial_port: "COM6", ...}
   Save response: {success: true, ...}
   ```

**If you see errors**:
- Screenshot and share
- Check Network tab for failed requests

---

## 📊 **Current Status Check**

Run this to see what's actually in the database:

```bash
docker exec meshcore-web python manage.py show_config
```

**Should show**:
```
Serial Enabled: True
Serial Port: COM6         ← Must have a value!
Serial Baud: 115200
Serial Connected: True    ← After bridge connects

MQTT Enabled: True/False
MQTT Broker: (your broker or empty)
```

**If Serial Port is empty**:
- Configuration didn't save properly
- Check browser console for JavaScript errors
- Try saving again with F12 console open

---

## 🎯 **Complete Working Example**

### **From Start to Finish**

**1. Physical Setup**
```
✅ RAK4631 plugged into USB
✅ Device Manager shows: "USB Serial Device (COM6)"
```

**2. Web Configuration**
```
✅ http://localhost:8000/meshcore/configuration/
✅ Enable Serial Connection: ☑️
✅ Serial Port: COM6
✅ Test: Browser popup → Select device → ✅ Success
✅ Save: Configuration saved successfully!
```

**3. Database Check**
```bash
docker exec meshcore-web python manage.py show_config
```
```
✅ Serial Enabled: True
✅ Serial Port: COM6  ← NOT empty!
```

**4. Bridge Connects (within 10s)**
```
✅ Live Traffic shows: "Serial connection established"
✅ Dashboard shows: RAK4631 🟢 Connected
```

**5. Data Flows**
```
✅ Bridge receives packets from RAK4631
✅ Packets stored in database
✅ Nodes appear in Nodes page
✅ Messages appear in Messages page
```

---

## 🐛 **Common Issues & Solutions**

### **Issue: Serial Port field shows value but database is empty**

**This means JavaScript isn't sending the data correctly**

**Debug**:
1. Open page, press F12
2. Go to Console tab
3. Type: `document.getElementById('serial_port').value`
4. Should show: "COM6"
5. Click "Save Configuration"
6. Watch console logs

**Possible fixes**:
- Clear browser cache
- Hard refresh (Ctrl + F5)
- Try different browser
- Check for JavaScript errors in console

---

### **Issue: Bridge says "Serial port not configured"**

**Step-by-step debug**:

```bash
# 1. Check database
docker exec meshcore-web python manage.py show_config

# Expected: Serial Port: COM6
# If empty: Configuration didn't save

# 2. Check bridge is reading database
docker logs meshcore-bridge --tail 30

# Expected: "Configuration loaded - Serial: enabled, MQTT: ..."
# If shows "disabled": Bridge read empty config

# 3. Verify docker-compose has COM6
docker-compose config | grep -A 20 "bridge:"

# Should see: - //./COM6://./COM6
```

---

## 💡 **Pro Tips**

### **Use Browser Console for Debugging**

Open Configuration page with F12 console open:
- See exactly what's being saved
- Catch JavaScript errors
- Verify API responses

### **Monitor Bridge Logs in Real-Time**

On Configuration page:
1. Scroll to "Live Bridge Traffic"
2. Click "Enable Auto-Refresh"
3. Watch logs update every 2 seconds
4. See exactly when bridge connects

### **Force Configuration Reload**

If bridge seems stuck:
```bash
docker-compose restart bridge
```

Bridge will immediately read latest config from database.

---

## ✅ **Success Indicators**

### **You know it's working when**:

**1. Database shows configuration**
```bash
$ docker exec meshcore-web python manage.py show_config
Serial Port: COM6  ← Has value!
```

**2. Bridge logs show connection**
```
INFO - Configuration loaded - Serial: enabled, MQTT: ...
INFO - Connecting to serial port COM6 at 115200 baud...
INFO - Serial connection established
```

**3. Live Traffic shows activity**
```
Configuration page → Live Bridge Traffic section
Shows: "Serial connection established"
Shows: "Bridge running, waiting for packets..."
```

**4. Dashboard shows status**
```
Dashboard → Bridge Status card
RAK4631 Device: 🟢 Connected
```

---

## 🎯 **Next Steps for You**

### **Right Now**:

1. **Open Configuration page**: http://localhost:8000/meshcore/configuration/

2. **Open Browser Console**: Press F12

3. **Configure Serial**:
   - Enable Serial Connection ☑️
   - Enter: `COM6`
   - Click "Save Configuration"

4. **Watch Console**: Should see:
   ```
   Saving configuration...
   Serial Enabled: true
   Serial Port: COM6
   Config to save: {serial_port: "COM6", ...}
   Save response: {success: true}
   ```

5. **Wait 10 seconds**

6. **Check Live Traffic logs**: Should show "Serial connection established"

---

**If it still doesn't work, send me**:
1. Screenshot of browser console (F12) when you click Save
2. Output of: `docker exec meshcore-web python manage.py show_config`
3. Output of: `docker logs meshcore-bridge --tail 20`

I'll help you debug it!

---

**Status**: ✅ Enhanced with live logs and debugging  
**Next**: Test the complete flow with browser console open
