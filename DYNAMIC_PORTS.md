# Dynamic COM Port Solution

## 🎯 **Your Question: What if COM Port Changes?**

**Answer**: The bridge now supports **COM1 through COM10** - so you can use ANY of them!

---

## **✅ How It Works Now**

### **Multiple COM Ports Passed Through**

```yaml
# docker-compose.yml
bridge:
  devices:
    - //./COM1://./COM1
    - //./COM2://./COM2
    - //./COM3://./COM3
    - //./COM4://./COM4
    - //./COM5://./COM5
    - //./COM6://./COM6    ← Your current port
    - //./COM7://./COM7    ← If it changes to this
    - //./COM8://./COM8    ← Or this
    - //./COM9://./COM9
    - //./COM10://./COM10
```

**Result**: The bridge container can access **any** of these ports!

---

## **🔄 When Your Port Changes**

### **Scenario: Device Moves from COM6 → COM7**

**What you do**:
1. Check Device Manager → Now shows COM7
2. Go to Configuration page: http://localhost:8000/meshcore/configuration/
3. Change "COM6" to "COM7" in the Serial Port field
4. Click **"Test Serial Connection"**
5. Click **"Save Configuration"**
6. Bridge reconnects in 10 seconds to COM7

**No restart needed!** ✅

### **Why It Works**

```
┌─────────────────────────────┐
│  docker-compose.yml         │
│  COM1-COM10 available       │ ← All ports passed through
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Database Configuration     │
│  serial_port: "COM6"        │ ← You configure which one
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Bridge Service             │
│  Connects to COM6           │ ← Uses the one from database
└─────────────────────────────┘
```

**The bridge can access COM1-COM10, but only connects to the one YOU specify in the web UI!**

---

## **💡 Key Benefits**

### **1. Dynamic Port Selection**
- ✅ Change ports anytime through web UI
- ✅ No docker-compose.yml editing needed
- ✅ No container restart needed
- ✅ Bridge auto-reconnects

### **2. Flexible for Multiple Devices**
- Device on COM3? ✅ Supported
- Device on COM6? ✅ Supported
- Device moves to COM7? ✅ Supported
- Multiple devices? ✅ Just switch in web UI

### **3. Zero Downtime**
- Change COM6 → COM7 in web UI
- Save configuration
- Wait 10 seconds
- Bridge reconnects
- **No service interruption!**

---

## **📋 Common Scenarios**

### **Scenario 1: Port Changes After Unplug**

**Before**:
```
Device Manager: "USB Serial Device (COM6)"
```

**After unplugging/replugging**:
```
Device Manager: "USB Serial Device (COM7)"
```

**What to do**:
1. Configuration page → Change COM6 to COM7
2. Test (browser will ask you to select device - select it)
3. Save
4. **Done!** Bridge reconnects to COM7

**Time**: 30 seconds

---

### **Scenario 2: Different USB Ports**

**Front USB**: COM3  
**Back USB**: COM6  
**USB Hub**: COM8  

**What to do**:
- Just update the port number in Configuration page
- All ports (COM1-COM10) are available
- Bridge connects to whichever you specify

---

### **Scenario 3: Multiple RAK4631 Devices**

**Device 1**: COM3  
**Device 2**: COM6  

**What to do**:
1. **Primary device** (for bridge): Configure in Configuration page
2. **Other devices** (for testing/flashing): Add in Device Connections page
3. Both work simultaneously!

---

## **🔧 If You Need COM Ports Above 10**

If your device is on COM11, COM12, etc., just add them to `docker-compose.yml`:

```yaml
devices:
  # ... existing COM1-COM10 ...
  - //./COM11://./COM11
  - //./COM12://./COM12
  - //./COM15://./COM15
  # Add as many as you need
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

---

## **🎯 Recommended Workflow**

### **For Regular Use**

1. **Plug in your RAK4631**
2. **Check Device Manager** → Note COM port (e.g., COM6)
3. **Go to Configuration page** → Type COM6
4. **Test** → ✅ Success
5. **Save** → Bridge connects

**If port changes later**:
- Repeat steps 2-5 with new COM port
- Takes 30 seconds
- No container restart!

---

### **For Development (Multiple Devices)**

**Configuration Page**:
- Set your primary RAK4631 (e.g., COM6)
- This runs continuously in background

**Device Connections Page**:
- Add other devices as needed (COM3, COM4, etc.)
- Connect when flashing firmware
- Disconnect when done

---

## **🚀 Complete Setup Example**

### **Your RAK4631 is on COM6**

1. **Configuration Page**
   ```
   ☑️ Enable Serial Connection
   Serial Port: COM6
   Baud Rate: 115200
   [Test Serial Connection] ← Click, select device in popup
   ✅ Success!
   [Save Configuration] ← Click
   ```

2. **Wait ~10 Seconds**

3. **Check Bridge Logs**
   ```bash
   docker logs meshcore-bridge --tail 10
   ```
   
   Should see:
   ```
   ✅ Configuration changed, reloading...
   ✅ Connecting to serial port COM6 at 115200 baud...
   ✅ Serial connection established
   ✅ Bridge running, waiting for packets...
   ```

4. **View Dashboard**
   - Go to: http://localhost:8000/meshcore/
   - Bridge Status → RAK4631: 🟢 Connected

**Success!** 🎉

---

### **Tomorrow, Device Moves to COM7**

1. **Configuration Page**
   ```
   Change: COM6 → COM7
   [Test Serial Connection]
   ✅ Success!
   [Save Configuration]
   ```

2. **Done!**
   - Bridge disconnects from COM6
   - Connects to COM7
   - No restart needed!

---

## **⚡ Pro Tips**

### **Force COM Port to Stay Same**

**In Device Manager**:
1. Right-click your device → Properties
2. Port Settings tab → Advanced
3. Set COM Port Number → Choose COM3 (or any preferred)
4. Click OK

**Now your device always uses the same COM port!**

---

### **Quick Port Check**

**Add this PowerShell function to your profile**:
```powershell
function Get-MeshCorePort {
    Get-WmiObject Win32_SerialPort | 
    Where-Object {$_.Name -like "*USB*" -or $_.Name -like "*nRF*"} |
    Select-Object Name, DeviceID
}
```

Then just run:
```powershell
Get-MeshCorePort
```

---

## **📊 Summary**

### **Problem Solved**
✅ COM ports can change → Bridge supports COM1-COM10  
✅ Just update in web UI → No docker-compose editing  
✅ Bridge auto-reconnects → No restart needed  

### **Current Status**
✅ Bridge has access to COM1-COM10  
✅ You configure which one via web UI  
✅ Change anytime, takes effect in 10 seconds  
✅ Works with any port in the range  

### **What You Do**
1. Check Device Manager for current port
2. Update in Configuration page
3. Test & Save
4. **Done!**

**No matter which COM port Windows assigns, it will work!** 🎊

---

**Bottom Line**: 
- Your device can be on COM3, COM6, COM7, COM9, etc.
- Just update the number in the web UI
- Bridge reconnects automatically
- **No config file editing ever!**

**Status**: ✅ Dynamic Port Support Enabled  
**Range**: COM1-COM10 (expandable)  
**Update Method**: Web UI only  
**Restart Required**: Never!
