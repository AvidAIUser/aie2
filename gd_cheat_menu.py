import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
import win32gui
import win32con
import win32api
import ctypes
from PIL import Image, ImageGrab
import cv2
import numpy as np
import pynput.keyboard
import pynput.mouse

# --- Configuration ---
CONFIG_FILE = "gd_cheat_config.json"
HOTKEY_TOGGLE = "insert"  # Key to show/hide menu

class CheatConfig:
    def __init__(self):
        self.click_delay = 10  # ms
        self.color_tolerance = 30
        self.target_color = None  # (R, G, B)
        self.click_region = None  # (x1, y1, x2, y2) relative to screen
        self.is_running = False
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.click_delay = data.get('click_delay', 10)
                    self.color_tolerance = data.get('color_tolerance', 30)
                    self.target_color = tuple(data['target_color']) if data.get('target_color') else None
                    self.click_region = tuple(data['click_region']) if data.get('click_region') else None
            except: pass

    def save(self):
        data = {
            'click_delay': self.click_delay,
            'color_tolerance': self.color_tolerance,
            'target_color': self.target_color,
            'click_region': self.click_region
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f)

class GDClickbotCheat:
    def __init__(self):
        self.config = CheatConfig()
        self.root = None
        self.is_visible = True
        self.is_click_through = False
        self.drag_active = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        
        # Runtime state
        self.cps = 0
        self.last_click_time = 0
        self.click_count = 0
        self.running = False
        self.gd_hwnd = None
        
        # Threads
        self.click_thread = None
        self.monitor_thread = None
        self.stop_event = threading.Event()

        self.setup_hotkey()
        self.create_gui()
        
        # Try to find GD immediately
        self.find_gd_window()

    def setup_hotkey(self):
        def on_press(key):
            try:
                if key.char == HOTKEY_TOGGLE or str(key) == f"<Key.{HOTKEY_TOGGLE}>":
                    self.toggle_menu()
            except AttributeError:
                if str(key) == f"<Key.{HOTKEY_TOGGLE}>":
                    self.toggle_menu()
        
        listener = pynput.keyboard.Listener(on_press=on_press)
        listener.start()

    def find_gd_window(self):
        """Finds Geometry Dash window and stores handle"""
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Geometry Dash" in title:
                    self.gd_hwnd = hwnd
                    return False
            return True
        
        try:
            win32gui.EnumWindows(callback, None)
            if self.gd_hwnd:
                self.log(f"Attached to Geometry Dash (HWND: {self.gd_hwnd})")
                self.snap_to_gd()
            else:
                self.log("GD not found. Launch the game to attach.")
        except Exception as e:
            self.log(f"Error finding GD: {e}")

    def snap_to_gd(self):
        """Moves the cheat menu to the top-right of the GD window"""
        if not self.gd_hwnd or not self.root:
            return
        
        try:
            rect = win32gui.GetWindowRect(self.gd_hwnd)
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top
            
            # Position menu at top-right inside the game window
            # Offset by 10px from edge
            menu_w = 320
            menu_h = 450
            
            x = left + width - menu_w - 10
            y = top + 10
            
            self.root.geometry(f"{menu_w}x{menu_h}+{int(x)}+{int(y)}")
            self.log("Menu snapped to GD window.")
        except Exception as e:
            self.log(f"Snap failed: {e}")

    def toggle_menu(self):
        self.is_visible = not self.is_visible
        if self.is_visible:
            self.root.deiconify()
            self.set_click_through(False) # Become interactive when opened
            self.find_gd_window() # Re-scan for GD
        else:
            self.root.withdraw()

    def set_click_through(self, enable):
        """Makes the window click-through except for the title bar logic handled in WM_NCHITTEST"""
        self.is_click_through = enable
        
        ex_style = win32gui.GetWindowLong(self.root.winfo_id(), win32con.GWL_EXSTYLE)
        
        if enable:
            # Add Transparent and Layered
            ex_style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
            # Set opacity (200/255)
            ctypes.windll.user32.SetLayeredWindowAttributes(
                self.root.winfo_id(), 
                0, 
                200, 
                win32con.LWA_ALPHA
            )
        else:
            # Remove Transparent
            ex_style &= ~win32con.WS_EX_TRANSPARENT
            
        win32gui.SetWindowLong(self.root.winfo_id(), win32con.GWL_EXSTYLE, ex_style)

    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("GD Clickbot")
        self.root.overrideredirect(True) # Borderless
        self.root.attributes('-topmost', True)
        
        # Initial size
        self.root.geometry("320x450")
        
        # Colors
        self.bg_color = "#1a1a1d"
        self.header_color = "#2d2d30"
        self.accent_color = "#00ff9d" # Cyber green
        self.text_color = "#ffffff"
        self.frame_color = "#3e3e42"

        # Main Frame (acts as the whole window)
        self.main_frame = tk.Frame(self.root, bg=self.bg_color, highlightthickness=0)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Title Bar (Draggable & Always Interactive) ---
        self.title_bar = tk.Frame(self.main_frame, bg=self.header_color, height=30)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        self.title_bar.pack_propagate(False)
        
        # Title Label
        lbl_title = tk.Label(self.title_bar, text="☠ GD CHEAT MENU", 
                             bg=self.header_color, fg=self.accent_color, 
                             font=("Consolas", 10, "bold"), anchor="w", padx=10)
        lbl_title.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Close Button
        btn_close = tk.Label(self.title_bar, text="✕", bg=self.header_color, fg="#ff5555",
                             font=("Arial", 12, "bold"), cursor="hand2", padx=8)
        btn_close.pack(side=tk.RIGHT)
        btn_close.bind("<Button-1>", lambda e: self.root.quit())
        
        # Drag Logic (Only on Title Bar)
        self.title_bar.bind("<ButtonPress-1>", self.start_drag)
        self.title_bar.bind("<B1-Motion>", self.do_drag)
        lbl_title.bind("<ButtonPress-1>", self.start_drag)
        lbl_title.bind("<B1-Motion>", self.do_drag)

        # --- Content Area (Click-through when not hovering controls) ---
        self.content_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Status Panel
        status_frame = tk.Frame(self.content_frame, bg=self.frame_color, pady=5)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_lbl = tk.Label(status_frame, text="● STOPPED", bg=self.frame_color, fg="#ff5555", font=("Consolas", 9, "bold"))
        self.status_lbl.pack(side=tk.LEFT, padx=10)
        
        self.cps_lbl = tk.Label(status_frame, text="CPS: 0", bg=self.frame_color, fg=self.text_color, font=("Consolas", 9))
        self.cps_lbl.pack(side=tk.RIGHT, padx=10)

        # Controls
        self.create_control("Click Delay (ms)", "delay", 1, 100, self.config.click_delay)
        self.create_control("Color Tolerance", "tolerance", 0, 100, self.config.color_tolerance)
        
        # Buttons Row 1
        btn_frame1 = tk.Frame(self.content_frame, bg=self.bg_color)
        btn_frame1.pack(fill=tk.X, pady=5)
        
        self.btn_pick_region = tk.Button(btn_frame1, text="🎯 Pick Region", command=self.pick_region,
                                         bg=self.frame_color, fg=self.text_color, activebackground=self.accent_color,
                                         font=("Consolas", 9), relief=tk.FLAT, cursor="hand2")
        self.btn_pick_region.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.btn_pick_color = tk.Button(btn_frame1, text="🎨 Pick Color", command=self.pick_color,
                                        bg=self.frame_color, fg=self.text_color, activebackground=self.accent_color,
                                        font=("Consolas", 9), relief=tk.FLAT, cursor="hand2")
        self.btn_pick_color.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Info Labels
        self.info_region = tk.Label(self.content_frame, text="Region: Not Set", bg=self.bg_color, fg="#888", font=("Consolas", 8), anchor="w")
        self.info_region.pack(fill=tk.X, pady=(2,0))
        
        self.info_color = tk.Label(self.content_frame, text="Color: Not Set", bg=self.bg_color, fg="#888", font=("Consolas", 8), anchor="w")
        self.info_color.pack(fill=tk.X, pady=(2,10))

        # Start/Stop Button
        self.btn_toggle = tk.Button(self.content_frame, text="START BOT", command=self.toggle_bot,
                                    bg="#2d2d30", fg="#00ff9d", activebackground="#00ff9d", activeforeground="#000",
                                    font=("Consolas", 12, "bold"), relief=tk.FLAT, cursor="hand2", pady=10)
        self.btn_toggle.pack(fill=tk.X, pady=10)

        # Attach Button
        btn_attach = tk.Button(self.content_frame, text="📎 Snap to GD", command=self.snap_to_gd,
                               bg=self.frame_color, fg="#aaa", activebackground=self.accent_color,
                               font=("Consolas", 9), relief=tk.FLAT, cursor="hand2")
        btn_attach.pack(fill=tk.X, pady=5)

        # Helper Text
        lbl_help = tk.Label(self.content_frame, text=f"Press [{HOTKEY_TOGGLE.upper()}] to Toggle Menu\nDrag Title Bar to Move", 
                            bg=self.bg_color, fg="#555", font=("Consolas", 7), justify=tk.CENTER)
        lbl_help.pack(side=tk.BOTTOM, pady=5)

        # Make controls interactive (remove click-through when hovering them)
        widgets = [self.btn_pick_region, self.btn_pick_color, self.btn_toggle, btn_attach, 
                   self.status_lbl, self.cps_lbl, self.info_region, self.info_color]
        for w in widgets:
            w.bind("<Enter>", lambda e: self.set_click_through(False))
            w.bind("<Leave>", lambda e: self.set_click_through(True))
            
        # Initial state
        self.set_click_through(True)
        
        # Start monitor loop
        self.root.after(100, self.update_monitor)

    def create_control(self, label_text, var_name, min_val, max_val, default):
        frame = tk.Frame(self.content_frame, bg=self.bg_color)
        frame.pack(fill=tk.X, pady=5)
        
        lbl = tk.Label(frame, text=label_text, bg=self.bg_color, fg=self.text_color, font=("Consolas", 9))
        lbl.pack(anchor="w")
        
        val_var = tk.IntVar(value=default)
        
        scale = ttk.Scale(frame, from_=min_val, to=max_val, variable=val_var, orient=tk.HORIZONTAL,
                          command=lambda v: self.on_setting_change(var_name, int(v)))
        scale.pack(fill=tk.X)
        
        # Style the scale (basic)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TScale", background=self.bg_color, troughcolor=self.frame_color, sliderrelief=tk.FLAT)

    def on_setting_change(self, name, value):
        if name == "delay":
            self.config.click_delay = value
        elif name == "tolerance":
            self.config.color_tolerance = value
        self.config.save()

    def start_drag(self, event):
        self.drag_active = True
        self.drag_offset_x = event.x
        self.drag_offset_y = event.y
        # Force interactive while dragging
        self.set_click_through(False)

    def do_drag(self, event):
        if self.drag_active:
            x = self.root.winfo_x() + (event.x - self.drag_offset_x)
            y = self.root.winfo_y() + (event.y - self.drag_offset_y)
            self.root.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        self.drag_active = False
        # Return to click-through if not hovering controls
        self.set_click_through(True)

    def pick_region(self):
        self.root.withdraw()
        time.sleep(0.2)
        
        # Create full screen overlay
        overlay = tk.Toplevel()
        overlay.attributes('-fullscreen', True, '-topmost', True, '-alpha', 0.3)
        overlay.configure(bg='red')
        overlay.attributes('-transparentcolor', 'red') # Make red transparent? No, we want crosshair
        
        # Actually, let's just use a simple crosshair cursor and wait for click
        overlay.config(cursor="cross")
        
        coords = []
        
        def on_click(event):
            coords.append((event.x_root, event.y_root))
            if len(coords) == 2:
                overlay.destroy()
                x1, y1 = coords[0]
                x2, y2 = coords[1]
                # Normalize
                region = (min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2))
                self.config.click_region = region
                self.info_region.config(text=f"Region: {region[2]-region[0]}x{region[3]-region[1]} @ ({region[0]}, {region[1]})")
                self.config.save()
                self.root.deiconify()
                self.set_click_through(True)
        
        overlay.bind("<Button-1>", on_click)
        lbl = tk.Label(overlay, text="Click Top-Left then Bottom-Right", bg="black", fg="white", font=("Arial", 16))
        lbl.place(relx=0.5, rely=0.5, anchor="center")

    def pick_color(self):
        if not self.config.click_region:
            messagebox.showwarning("Warning", "Select a region first!")
            self.root.deiconify()
            return
            
        self.root.withdraw()
        time.sleep(0.3)
        
        # Capture region
        x1, y1, x2, y2 = self.config.click_region
        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        img_np = np.array(screenshot)
        
        # Get center color
        h, w, _ = img_np.shape
        center_color = img_np[h//2, w//2]
        
        self.config.target_color = (int(center_color[2]), int(center_color[1]), int(center_color[0])) # RGB
        r,g,b = self.config.target_color
        self.info_color.config(text=f"Color: RGB({r}, {g}, {b})", fg="#00ff9d")
        self.config.save()
        
        self.root.deiconify()
        self.set_click_through(True)

    def toggle_bot(self):
        self.running = not self.running
        if self.running:
            if not self.config.click_region or not self.config.target_color:
                messagebox.showerror("Error", "Please set Region and Color first!")
                self.running = False
                return
                
            self.btn_toggle.config(text="STOP BOT", bg="#ff5555", fg="white")
            self.status_lbl.config(text="● RUNNING", fg="#00ff9d")
            self.stop_event.clear()
            
            self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
            self.click_thread.start()
            
            self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitor_thread.start()
        else:
            self.btn_toggle.config(text="START BOT", bg="#2d2d30", fg="#00ff9d")
            self.status_lbl.config(text="● STOPPED", fg="#ff5555")
            self.stop_event.set()
            self.cps = 0

    def click_loop(self):
        mouse = pynput.mouse.Controller()
        while not self.stop_event.is_set() and self.running:
            if self.check_color():
                mouse.click(pynput.mouse.Button.left, 1)
                self.click_count += 1
                time.sleep(self.config.click_delay / 1000.0)
            else:
                time.sleep(0.01) # Small sleep to prevent CPU spike

    def check_color(self):
        if not self.config.click_region or not self.config.target_color:
            return False
            
        x1, y1, x2, y2 = self.config.click_region
        # Grab small center area for performance
        cx, cy = (x1+x2)//2, (y1+y2)//2
        grab_size = 5
        
        try:
            screenshot = ImageGrab.grab(bbox=(cx-grab_size, cy-grab_size, cx+grab_size, cy+grab_size))
            img_np = np.array(screenshot)
            # Check average color
            avg_color = np.mean(img_np, axis=(0,1)).astype(int)
            
            # Compare BGR (PIL is RGB, but target stored as RGB)
            dist = np.sqrt(np.sum((avg_color - self.config.target_color)**2))
            return dist < self.config.color_tolerance
        except:
            return False

    def monitor_loop(self):
        last_count = 0
        while not self.stop_event.is_set() and self.running:
            time.sleep(1.0)
            self.cps = self.click_count - last_count
            last_count = self.click_count
            self.click_count = 0 # Reset for next second

    def update_monitor(self):
        if self.running:
            self.cps_lbl.config(text=f"CPS: {self.cps}")
        else:
            self.cps_lbl.config(text="CPS: 0")
            
        # Re-check GD attachment occasionally
        if not self.gd_hwnd or not win32gui.IsWindow(self.gd_hwnd):
             self.find_gd_window()
             
        self.root.after(1000, self.update_monitor)

    def log(self, msg):
        print(f"[GD Cheat] {msg}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = GDClickbotCheat()
    app.run()
