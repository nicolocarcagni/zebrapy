#!/usr/bin/env python3
import subprocess
import os
import json
import shutil
import time

class ZebraPrinterManager:
    CONFIG_FILE = "config.json"
    DOTS_PER_MM = 8  # 203 DPI approximation

    def __init__(self):
        self.settings = self.load_settings()
        self.usb_online = False
        self.printer_verified = False
        self.check_hardware_connection()

    def load_settings(self):
        default_settings = {
            "printer_name": "ZTC-GK420t",
            "text": "nicolocarcagni.dev",
            "darkness": 30,           # 0-30
            "media_darkness": 15,     # ^MD -30 to 30
            "speed": 2,               # 2-5 ips
            "label_width_mm": 50.0,   # ~2 inches
            "label_height_mm": 25.0,  # ~1 inch
            "font_h_mm": 4.0,         # Default 4mm height (readable)
            "font_w_mm": 4.0,         # Default 4mm width (square)
            "offset_x_mm": 2.0,       # Left margin
            "offset_y_mm": 2.0,       # Top margin
            "print_method": "direct_thermal"
        }
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                    
                    return {**default_settings, **loaded}
            except json.JSONDecodeError:
                print("Error loading config.json, using defaults.")
                return default_settings
        return default_settings

    def save_settings(self):
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
            print("Settings saved to config.json.")
        except IOError as e:
            print(f"Error saving settings: {e}")

    def mm_to_dots(self, mm):
        """Converts millimeters to dots."""
        try:
            return int(float(mm) * self.DOTS_PER_MM)
        except ValueError:
            return 0

    def check_hardware_connection(self):
        """Checks if a Zebra device is physically connected via USB."""
        self.usb_online = False
        if not shutil.which('lsusb'):
            self.usb_online = True # Assume true to avoid blocking
            return

        try:
            result = subprocess.run(['lsusb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if "Zebra" in result.stdout or "0a5f:" in result.stdout:
                self.usb_online = True
            else:
                self.usb_online = False
        except Exception:
            self.usb_online = False
        self.check_cups_status()

    def check_cups_status(self):
        printer = self.settings['printer_name']
        if not shutil.which('lpstat'):
            self.printer_verified = False
            return

        try:
            result = subprocess.run(['lpstat', '-p'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if printer in result.stdout:
                self.printer_verified = True
            else:
                self.printer_verified = False
        except Exception:
            self.printer_verified = False

    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')

    def get_input(self, prompt, cast_type=str, valid_range=None, default=None):
        while True:
            user_input = input(prompt)
            if not user_input and default is not None:
                return default
            try:
                value = cast_type(user_input)
                if valid_range and value not in valid_range:
                    print(f"Value must be between {min(valid_range)} and {max(valid_range)}.")
                    continue
                return value
            except ValueError:
                print(f"Invalid input. Please enter a valid {cast_type.__name__}.")

    def clear_print_queue(self):
        printer = self.settings['printer_name']
        print(f"\n🗑️  Clearing print queue for '{printer}'...")
        try:
            subprocess.run(['cancel', '-a', printer], check=False)
            print("✅ Queue cleared.")
        except FileNotFoundError:
            print("❌ Error: 'cancel' command not found.")
        input("Press Enter to continue...")

    def configure_fonts(self):
        s = self.settings
        print("\n --- FONT SETTINGS (Zebra Scalable Font 0) ---")
        print(" ℹ️  Font 0 is the standard internal scalable font.")
        print(" ℹ️  Increasing height/width in mm directly affects legibility.")
        print(" ℹ️  Standard Readable Size: 3mm - 6mm.")
        
        # Height
        current_h = s.get('font_h_mm', 4.0)
        max_h = s['label_height_mm'] - 2 # Margin safety
        print(f"\n Current Size: {s['font_h_mm']}mm x {s['font_w_mm']}mm")
        
        new_h = self.get_input(f" Enter New Height (mm) [Max {max_h}]: ", float)
        if new_h > max_h:
            print(f"⚠️  Warning: {new_h}mm might be too tall for this label!")
        
        s['font_h_mm'] = new_h
        
        # Proportional Width
        prop = input(" Keep proportional (Square Font)? [Y/n]: ").lower()
        if prop != 'n':
            s['font_w_mm'] = new_h
            print(f" Width automatically set to {new_h}mm (Square).")
        else:
            s['font_w_mm'] = self.get_input(" Enter New Width (mm): ", float)
        
        input("Fonts updated. Press Enter...")

    def generate_zpl(self, test_pattern=False):
        s = self.settings
        width_dots = self.mm_to_dots(s['label_width_mm'])
        height_dots = self.mm_to_dots(s['label_height_mm'])
        offset_x_dots = self.mm_to_dots(s['offset_x_mm'])
        offset_y_dots = self.mm_to_dots(s['offset_y_mm'])
        
        # Font Calculations
        font_h_dots = self.mm_to_dots(s['font_h_mm'])
        font_w_dots = self.mm_to_dots(s['font_w_mm'])
        
        zpl = [
            f"~SD{s['darkness']}",
            "^XA",
            "^MTD",             # Force Direct Thermal
            f"^PR{s['speed']}",
            f"^MD{s['media_darkness']}",
            f"^PW{width_dots}",
            f"^LL{height_dots}",
            "^CI28"
        ]

        if test_pattern:
            # 1mm thick black border = ~8 dots
            border_thickness = self.mm_to_dots(1) 
            zpl.append(f"^FO0,0^GB{width_dots},{height_dots},{border_thickness},B,0^FS")
            # Text inside
            zpl.append(f"^FO{width_dots//4},{height_dots//3}^A0N,30,30^FDTEST FRAME^FS")
        else:
            zpl.append(f"^FO{offset_x_dots},{offset_y_dots}")
            # Use Zebra Font 0 (^A0)
            zpl.append(f"^A0N,{font_h_dots},{font_w_dots}")
            zpl.append(f"^FD{s['text']}^FS")

        zpl.append("^XZ")
        return "\n".join(zpl)

    def print_label(self, test_pattern=False):
        # 1. Hardware Check
        self.check_hardware_connection()
        if not self.usb_online:
            print("\n❌ CRITICAL HARDWARE ERROR: Printer not detected on USB!")
            print("   Please check the USB cable connectivity.")
            input("\nPress Enter to return to menu...")
            return

        zpl = self.generate_zpl(test_pattern)
        printer_name = self.settings['printer_name']
        
        print(f"\nSending job to '{printer_name}'...")
        
        try:
            cmd = ['lp', '-d', printer_name, '-o', 'raw', '-']
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input=zpl)
            
            if process.returncode == 0:
                print("✅ SENT: Print job submitted successfully.")
            else:
                print("❌ FAILED: The print system returned an error.")
                print(f"    Error Details: {stderr.strip()}")
        except FileNotFoundError:
            print("❌ SYSTEM ERROR: 'lp' command not found. Install CUPS.")
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {e}")
        
        input("\n[Press Enter to continue]")

    def print_header(self):
        self.clear_screen()
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                   ZEBRA GK420t CLI MANAGER                   ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        
        # Status Bar
        usb_status = "🔌 USB: CONNECTED" if self.usb_online else "🔌 USB: DISCONNECTED"
        p_status = "🖨️  CUPS: ONLINE" if self.printer_verified else "🖨️  CUPS: NOT FOUND"
        
        print(f" PRINTER: {self.settings['printer_name']:<18} | {usb_status} | {p_status}")
        print("────────────────────────────────────────────────────────────────")

    def main_menu(self):
        while True:
            # Refresh connectivity occasionally
            self.check_hardware_connection()
            
            self.print_header()
            s = self.settings
            
            # Table formatting
            w1, w2, w3 = 18, 22, 30
            r1c1 = f"W: {s['label_width_mm']} mm"
            r1c2 = f"Speed: {s['speed']} ips"
            r1c3 = f"Text: {s['text']}"
            if len(r1c3) > w3: r1c3 = r1c3[:w3-3] + "..."

            r2c1 = f"H: {s['label_height_mm']} mm"
            r2c2 = f"Dark:  {s['darkness']} (~SD)"
            # Update Font Display to MM
            r2c3 = f"Font: Zebra 0 ({s['font_h_mm']}x{s['font_w_mm']}mm)"

            r3c1 = ""
            r3c2 = f"M-Dark:{s['media_darkness']} (^MD)"
            r3c3 = f"Off: X={s['offset_x_mm']} Y={s['offset_y_mm']}"

            print(" CURRENT SETTINGS:")
            print(f" ┌─{'─'*w1}─┬─{'─'*w2}─┬─{'─'*w3}─┐")
            print(f" │ {r1c1:<{w1}} │ {r1c2:<{w2}} │ {r1c3:<{w3}} │")
            print(f" │ {r2c1:<{w1}} │ {r2c2:<{w2}} │ {r2c3:<{w3}} │")
            print(f" │ {r3c1:<{w1}} │ {r3c2:<{w2}} │ {r3c3:<{w3}} │")
            print(f" └─{'─'*w1}─┴─{'─'*w2}─┴─{'─'*w3}─┘")
            
            print("\n ACTIONS:")
            print("  1. 🖨️  PRINT LABEL")
            print("  2. 🛠️  PRINT TEST FRAME (Check Margins)")
            print("\n CONFIGURATION:")
            print("  3. 📝 Set Text")
            print("  4. 📏​ Set Dimensions (mm)")
            print("  5. 📍 Set Offsets (Fix Fading)")
            print("  6. ⚙️  Calibrate (Darkness & Speed)")
            print("  7. 🔠 Font Settings (Size in mm)")
            print("  8. 🔁 Change Printer Name")
            print("  9. 🗑️  Clear Print Queue")
            print("\n  0. 💾 Save & Exit")
            
            choice = input("\n ➤ Select Option: ")

            if choice == "1":
                self.print_label(False)
            elif choice == "2":
                self.print_label(True)
            elif choice == "3":
                s['text'] = input(" Enter New Text: ")
            elif choice == "4":
                print("\n --- LABEL DIMENSIONS (mm) ---")
                print(" ℹ️  Measure your label with a ruler. Exact dimensions prevent skipping.")
                s['label_width_mm'] = self.get_input(" Width (mm): ", float)
                s['label_height_mm'] = self.get_input(" Height (mm): ", float)
            elif choice == "5":
                print("\n --- PRINT OFFSETS (mm) ---")
                print(" ℹ️  X Offset: Shifts print right. Use 1-2mm if left side is fading (cold start).")
                print(" ℹ️  Y Offset: Shifts print down. Use if top is cut off.")
                s['offset_x_mm'] = self.get_input(" Left X Offset (mm): ", float)
                s['offset_y_mm'] = self.get_input(" Top Y Offset (mm): ", float)
            elif choice == "6":
                print("\n --- MECHANICS & THERMAL ---")
                print(" ℹ️  Darkness (~SD 0-30): Higher = Darker. Too high = Head wear & smudging.")
                print(" ℹ️  Media Darkness (^MD -30..30): Fine-tune darkness per label.")
                print(" ℹ️  Speed (2-5 ips): Lower (2) = Better quality & darkness. Higher = Faster.")
                s['darkness'] = self.get_input(" Darkness (~SD 0-30): ", int, range(0, 31))
                s['media_darkness'] = self.get_input(" Media Darkness (^MD -30 to 30): ", int, range(-30, 31))
                s['speed'] = self.get_input(" Speed (2-5 ips): ", int, range(2, 7))
            elif choice == "7":
                self.configure_fonts()
            elif choice == "8":
                s['printer_name'] = input(" Enter CUPS Printer Name: ")
                self.check_cups_status()
            elif choice == "9":
                self.clear_print_queue()
            elif choice == "0":
                self.save_settings()
                print(" Goodbye!")
                break
            else:
                 input(" Invalid Selection. Press Enter...")

if __name__ == "__main__":
    try:
        app = ZebraPrinterManager()
        app.main_menu()
    except KeyboardInterrupt:
        print("\n Aborted.")
