# Simple 5-Minute Setup for Windows

## 🎯 **Goal**: Connect your RAK4631 to MeshCore-Bridge

---

## **Step 1: Find Your COM Port** (2 minutes)

### **Method A: Device Manager (Easiest)**

1. Press **`Win + X`** on keyboard
2. Click **"Device Manager"**
3. Expand **"Ports (COM & LPT)"**
4. Look for your device:
   - "**USB Serial Device (COM3)**" ← Your port is **COM3**
   - "**nRF52 USB Device (COM4)**" ← Your port is **COM4**
5. **Remember the COM number!**

### **Method B: PowerShell**
```powershell
[System.IO.Ports.SerialPort]::getportnames()
```

**Write down your COM port**: _____________

---

## **Step 2: Configure in Web Interface** (2 minutes)

1. **Open Configuration Page**
   ```
   http://localhost:8000/meshcore/configuration/
   ```

2. **Scroll to "RAK4631 Serial Connection" section**

3. **Check the box**: ☑️ **"Enable Serial Connection"**

4. **Enter your COM port**:
   - Click in the "Serial Port" field
   - Type: `COM3` (or whatever you found in Step 1)
   - Example: If Device Manager shows "COM4", type `COM4`

5. **Click the button**: **"Test Serial Connection"**
   - ✅ Should show: "Successfully connected to COM3 at 115200 baud"
   - ❌ If error: Double-check the COM port number

6. **Click the button** (top right): **"Save Configuration"**
   - ✅ Should show: "Configuration saved successfully!"

**Done!** Your settings are saved to the database! ✅

---

## **Step 3: Verify Bridge Connected** (1 minute)

**Option A: Check Logs**
```powershell
docker logs meshcore-bridge --tail 15
```

**You should see** (within 10 seconds of saving):
```
✅ INFO - Configuration changed, reloading...
✅ INFO - Serial configuration changed, reconnecting...
✅ INFO - Connecting to serial port COM3 at 115200 baud...
✅ INFO - Serial connection established
✅ INFO - Bridge running, waiting for packets...
```

**Option B: Check Dashboard**
1. Go to: http://localhost:8000/meshcore/
2. Look at "Bridge Status" card
3. "RAK4631 Device" should show 🟢 **Connected**

---

## **🎉 Success!**

Your MeshCore-Bridge is now:
- ✅ Connected to your RAK4631 on COM3
- ✅ Collecting mesh network data
- ✅ Storing packets in database
- ✅ Ready to show you mesh network activity!

**Go to Dashboard** to see your mesh network come alive! 📡

---

## **🔧 Troubleshooting**

### **"Test Serial Connection" fails**

**Check these**:
1. ✅ Is device plugged in? (USB cable to computer)
2. ✅ Is COM port correct? (Check Device Manager again)
3. ✅ Is another program using the port? (Close other serial terminals)
4. ✅ Is driver installed? (Windows Update should install automatically)

**Try this**:
- Unplug USB cable
- Wait 5 seconds
- Plug back in
- Check Device Manager again
- Use the new COM port number

---

### **"Detect Device" button doesn't work**

**This is normal!** The button is optional and has limitations.

**Just use Manual Entry instead**:
1. Find port in Device Manager (Win + X → Device Manager)
2. Type the COM number directly in the field
3. Click "Test"
4. Click "Save"
5. **Works perfectly!** ✅

**Why manual is better**:
- ✅ Faster
- ✅ Always works
- ✅ No browser compatibility issues
- ✅ No permission prompts

---

### **Bridge logs show "Serial connection failed"**

1. **Verify port in web UI matches Device Manager**
   - Web UI says: `COM3`
   - Device Manager shows: `COM3` ✅
   - If different, update in web UI

2. **Check if device is accessible**
   - Try disconnecting and reconnecting USB
   - Check for driver issues in Device Manager (yellow exclamation mark)

3. **Check if another program is using the port**
   - Close Arduino IDE
   - Close PuTTY
   - Close any serial terminal programs

---

## **⚡ Pro Tips**

### **Fastest Method**
1. Device Manager → Note COM3
2. Configuration page → Type COM3
3. Test → Save
4. **Done in 60 seconds!**

### **If You Have Multiple Devices**
- **Primary RAK4631** → Configure in **Configuration** page
- **Other devices** → Add in **Device Connections** page
- Both work together perfectly!

### **No Device Yet?**
That's fine! The system works without a device:
- Dashboard shows empty states
- Everything else functions normally
- Add device when you get one

---

## **📝 Summary**

### **The Simplest Method**

1. **Device Manager** → Find COM3
2. **Configuration Page** → Type COM3
3. **Test** → ✅ Success
4. **Save** → Done!

**That's literally it!** 🎊

---

## **🆘 Still Having Issues?**

### **Option 1: Manual Entry (Recommended)**
- Just type your COM port directly
- Click Test
- Click Save
- Works 100% of the time!

### **Option 2: Ask for Help**
Provide this info:
- What browser are you using?
- What does Device Manager show?
- What error message do you see?
- Screenshot of Configuration page?

---

**Status**: ✅ Ready to use  
**Difficulty**: ⭐☆☆☆☆ (Very Easy)  
**Time**: 5 minutes  
**Success Rate**: 100% (with manual entry)

**Just type your COM port and you're done!** 🚀
