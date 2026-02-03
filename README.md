# 🦓 Zebra ZPL Linux CLI: The Label Printing Survival Kit

> *"Because we've all been hurt by a label printer before."*

## The Nightmare of Label Printing on Linux
If you are here, you probably know the pain. You bought a Zebra GK420t (or similar), plugged it into Fedora/Ubuntu/Linux Mint, and... chaos ensued.
- The CUPS driver scales your 2x1" label into oblivion.
- The font looks fuzzy or rotated 90 degrees for no reason.
- You print, nothing happens, and you find a "Job Completed" status for a ghost job.

**Stop fighting the driver.**

This tool is a **ZPL Bridge**. Instead of relying on a confused OS driver to render an image, we speak the printer's native language (ZPL II). We calculate the exact dots, handle the heating curves, and talk directly to the hardware. **What you see is exactly what you get.**

---

## 🚀 Key Features

### 📏 Math? We Do That (mm-to-Dots Precision)
Your label is 50mm wide. The printer prints at 203 DPI. How many dots is that? 
Don't reach for the calculator. This tool accepts all inputs in **Millimeters** and converts them to precise printer dots ($1mm \approx 8 dots$) automatically.  
- **You enter:** `50mm x 25mm`
- **We send:** `^PW406 ^LL203`

### 🔥 Anti-Fading & Cold-Start Fixes
Thermal printers are like espresso machines—they need to warm up. The first label is often faded on the left side because the printhead was cold.
We give you direct control over:
- **Darkness (`~SD`)**: The base heat.
- **Speed (`^PR`)**: Slower = hotter and sharper.
- **Offsets**: Shift the print 1-2mm to the right to bypass that cold left edge.

### 🛠️ The "Stress Test" Frame
Unsure if your printhead is dying or just dirty?
Use the **"Print Test Frame"** feature. It generates a perfect 1mm thick black border around the edge of your label. If the lines are broken or uneven, you have a mechanical pressure issue, not a software bug.

---

## 📦 Setup Guide (Linux)

### 1. Install Dependencies
You likely have these, but let's be safe. We need `cups` for the transport and `usbutils` for the hardware check.
```bash
sudo dnf install cups usbutils python3
```

### 2. Permissions (The #1 Cause of Failure)
Your user needs permission to talk to printers.
```bash
sudo usermod -aG lp $USER
# LOG OUT and LOG BACK IN for this to take effect!
```

### 3. Add the Raw Printer
Don't use the "Zebra ZPL Label Printer" driver. Use **Raw Queue**.
```bash
# Find your USB URI
lpinfo -v | grep usb

# Add printer (replace URI with yours)
sudo lpadmin -p ZTC-GK420t -E -v usb://Zebra/GK420t... -m raw
```

### 4. Run the Tool
```bash
python3 zebra.py
```
*Your settings will auto-save to `config.json` after the first run.*

---

## 🔧 Troubleshooting

### "The left side of my label is faded."
**The Cause:** Cold printhead or uneven mechanical pressure.
**The Fix:** 
1. Lower the Speed to **2 ips**.
2. Increase **Darkness** slightly (start at 25).
3. Use the **X Offset** setting to move the print 2mm to the right (`2.0`), pushing the content into the heated zone.

### "The text is rotated 90 degrees!"
**The Cause:** Linux drivers trying to be "smart" and matching portrait/landscape.
**The Fix:** **You are safe here.** This script generates raw `^XA`...`^XZ` ZPL code. We define the page orientation explicitly. If your dimensions are correct (e.g., Width > Height), the printer will print exactly as configured.

### "Permission Denied / Printer not found"
**The Fix:** Did you log out after adding yourself to the `lp` group?
Run `groups` and check if `lp` is in the list. if not, reboot.

---

## 📝 License
Open Source. Hack it, fork it, fix it.
