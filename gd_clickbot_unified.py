import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import threading
import time
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import win32gui
import win32con
import win32api
from PIL import Image, ImageTk
import json
import os

# Configuration Constants
CONFIG_FILE = "gd_cheat_config.json"
DEFAULT_CONFIG = {
    "click_delay": 15,
    "tolerance": 30,
    "target_color": [0, 255, 0],
    "region": None,
    "enabled": False,
    "click_through": True
}

class GDClickbotEngine:
    """Background logic for color detection and clicking"""
    def __init__(self, overlay):
        self.overlay = overlay
        self.running = False
        self.thread = None
        self.cps = 0
        self.last_click_time = 0
        self.lock = threading.Lock()

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.loop, daemon=True)
            self.thread.start()
            self.overlay.log("Bot Started", "green")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self.overlay.log("Bot Stopped", "red")
        self.cps = 0
        self.overlay.update_stats(0)

    def loop(self):
        while self.running:
            try:
                if self.overlay.config["region"] and self.overlay.config["target_color"]:
                    region = self.overlay.config["region"]
                    target = tuple(self.overlay.config["target_color"])
                    tolerance = self.overlay.config["tolerance"]
                    delay = self.overlay.config["click_delay"] / 1000.0

                    # Capture region
                    screenshot = pyautogui.screenshot(region=region)
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # Update preview (throttled slightly to avoid lag)
                    if hasattr(self.overlay, 'update_preview'):
                        self.overlay.update_preview(frame)

                    # Color Detection
                    lower = np.array([max(c - tolerance, 0) for c in target])
                    upper = np.array([min(c + tolerance, 255) for c in target])
                    mask = cv2.inRange(frame, lower, upper)
                    
                    if cv2.countNonZero(mask) > 0:
                        current_time = time.time()
                        if current_time - self.last_click_time >= delay:
                            pyautogui.click()
                            self.last_click_time = current_time
                            
                            # Simple CPS calculation
                            with self.lock:
                                self.cps = int(1 / (current_time - self.last_click_time)) if (current_time - self.last_click_time) > 0 else 0
                                self.overlay.update_stats(self.cps)
                    else:
                        self.cps = 0
                        self.overlay.update_stats(0)
                        
                time.sleep(0.001) # Prevent CPU spike
            except Exception as e:
                # Silently fail or log minor errors to avoid crashing
                pass

class GDOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GD Cheat Menu")
        self.root.geometry("360x580")
        
        # Load Config
        self.config = self.load_config()
        
        # Engine
        self.engine = GDClickbotEngine(self)
        
        # State
        self.is_locked = True # True = Click-through mode (Playing), False = Interactive
        self.drag_start_pos = None
        self.window_offset = None
        
        self.setup_window()
        self.setup_ui()
        self.setup_hotkeys()
        
        # Start auto-snap timer
        self.root.after(1000, self.auto_snap_to_gd)
        self.root.after(100, self.update_loop)

    def setup_window(self):
        # Make transparent and layered
        self.root.attributes('-alpha', 0.95)
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        
        # Windows API for Click-Through
        hwnd = win32gui.GetHwnd(self.root.winfo_id())
        styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        # WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, styles | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOOLWINDOW)
        
        # Bindings for dragging
        self.root.bind("<Button-1>", self.on_press)
        self.root.bind("<B1-Motion>", self.on_drag)
        self.root.bind("<ButtonRelease-1>", self.on_release)

    def setup_ui(self):
        # Main Container (Needs to be interactive when unlocked)
        self.main_frame = tk.Frame(self.root, bg="#1e1e1e", highlightthickness=2, highlightbackground="#00ff00")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Title Bar ---
        title_bar = tk.Frame(self.main_frame, bg="#2d2d2d", height=30)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        
        lbl_title = tk.Label(title_bar, text="☠️ GD CHEAT MENU", bg="#2d2d2d", fg="#00ff00", font=("Segoe UI", 10, "bold"))
        lbl_title.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.status_lbl = tk.Label(title_bar, text="[UNLOCKED]", bg="#2d2d2d", fg="#ffaa00", font=("Segoe UI", 8))
        self.status_lbl.pack(side=tk.RIGHT, padx=10, pady=8)
        
        # --- Tabs ---
        tab_control = ttk.Notebook(self.main_frame)
        tab_control.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook.Tab', background='#333333', foreground='white', padding=[10, 5])
        style.configure('TNotebook.Tab', font=('Segoe UI', 9))
        style.map('TNotebook.Tab', background=[('selected', '#1e1e1e')])
        
        # Tab 1: Aimbot (Clickbot)
        self.tab_aimbot = tk.Frame(tab_control, bg="#1e1e1e")
        tab_control.add(self.tab_aimbot, text="  Aimbot  ")
        self.build_aimbot_tab()
        
        # Tab 2: Visuals
        self.tab_visuals = tk.Frame(tab_control, bg="#1e1e1e")
        tab_control.add(self.tab_visuals, text="  Visuals  ")
        self.build_visuals_tab()
        
        # Tab 3: Config
        self.tab_config = tk.Frame(tab_control, bg="#1e1e1e")
        tab_control.add(self.tab_config, text="  Config  ")
        self.build_config_tab()
        
        # --- Footer / Log ---
        log_frame = tk.Frame(self.main_frame, bg="#111111", height=80)
        log_frame.pack(fill=tk.X, side=tk.BOTTOM)
        log_frame.pack_propagate(False)
        
        self.log_text = tk.Text(log_frame, bg="#111111", fg="#aaaaaa", font=("Consolas", 8), height=4, bd=0, highlightthickness=0)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log("System initialized. Press INSERT to toggle lock.")

    def build_aimbot_tab(self):
        # Status Panel
        status_frame = tk.Frame(self.tab_aimbot, bg="#252525", pady=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.led_lbl = tk.Label(status_frame, text="●", fg="#555555", bg="#252525", font=("Arial", 16))
        self.led_lbl.pack(side=tk.LEFT, padx=5)
        
        self.cps_lbl = tk.Label(status_frame, text="0 CPS", fg="#ffffff", bg="#252525", font=("Segoe UI", 12, "bold"))
        self.cps_lbl.pack(side=tk.LEFT)
        
        btn_start = tk.Button(status_frame, text="START", bg="#006400", fg="white", activebackground="#008000", 
                              command=self.toggle_bot, font=("Segoe UI", 9, "bold"), relief=tk.FLAT)
        btn_start.pack(side=tk.RIGHT, padx=5)
        
        # Live Preview
        prev_frame = tk.LabelFrame(self.tab_aimbot, text="Live Feed", bg="#252525", fg="#888888", font=("Segoe UI", 8))
        prev_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.preview_lbl = tk.Label(prev_frame, bg="black", text="No Region Selected", fg="#555555")
        self.preview_lbl.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Controls
        ctrl_frame = tk.Frame(self.tab_aimbot, bg="#1e1e1e")
        ctrl_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(ctrl_frame, text="Click Delay (ms):", bg="#1e1e1e", fg="#ccc", font=("Segoe UI", 9)).pack(anchor=tk.W)
        self.delay_slider = tk.Scale(ctrl_frame, from_=1, to=100, orient=tk.HORIZONTAL, bg="#333333", fg="white", 
                                     troughcolor="#444444", highlightthickness=0, command=lambda v: self.save_setting("click_delay", int(v)))
        self.delay_slider.set(self.config.get("click_delay", 15))
        self.delay_slider.pack(fill=tk.X)
        
        tk.Label(ctrl_frame, text="Color Tolerance:", bg="#1e1e1e", fg="#ccc", font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(10,0))
        self.tol_slider = tk.Scale(ctrl_frame, from_=0, to=100, orient=tk.HORIZONTAL, bg="#333333", fg="white", 
                                   troughcolor="#444444", highlightthickness=0, command=lambda v: self.save_setting("tolerance", int(v)))
        self.tol_slider.set(self.config.get("tolerance", 30))
        self.tol_slider.pack(fill=tk.X)
        
        # Buttons
        btn_row = tk.Frame(self.tab_aimbot, bg="#1e1e1e")
        btn_row.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(btn_row, text="📍 Select Region", command=self.pick_region, bg="#444444", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_row, text="🎨 Pick Color", command=self.pick_color, bg="#444444", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

    def build_visuals_tab(self):
        tk.Label(self.tab_visuals, text="Visual Options", bg="#1e1e1e", fg="#888888", font=("Segoe UI", 10, "bold")).pack(pady=10)
        tk.Label(self.tab_visuals, text="(Placeholder for future ESP/Wallhack)", bg="#1e1e1e", fg="#555555", font=("Segoe UI", 8)).pack()
        
        # Example toggle
        var = tk.BooleanVar(value=True)
        chk = tk.Checkbutton(self.tab_visuals, text="Show FPS Counter", variable=var, bg="#1e1e1e", fg="#ccc", selectcolor="#333333", activebackground="#1e1e1e", activeforeground="#ccc")
        chk.pack(pady=20)

    def build_config_tab(self):
        tk.Label(self.tab_config, text="Profiles", bg="#1e1e1e", fg="#888888", font=("Segoe UI", 10, "bold")).pack(pady=10)
        
        btn_frame = tk.Frame(self.tab_config, bg="#1e1e1e")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Save Current", command=self.save_config, bg="#444444", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Reset Defaults", command=self.reset_config, bg="#552222", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.tab_config, text="Hotkeys:", bg="#1e1e1e", fg="#888888", font=("Segoe UI", 10, "bold")).pack(pady=(20, 5))
        tk.Label(self.tab_config, text="INSERT : Toggle Menu Lock", bg="#1e1e1e", fg="#aaa", font=("Consolas", 9)).pack(anchor=tk.W, padx=20)
        tk.Label(self.tab_config, text="F12    : Emergency Stop", bg="#1e1e1e", fg="#ff5555", font=("Consolas", 9)).pack(anchor=tk.W, padx=20)

    def setup_hotkeys(self):
        # Global hotkey listener in a separate thread
        def listen():
            import pynput.keyboard
            def on_press(key):
                try:
                    if key == pynput.keyboard.Key.insert:
                        self.toggle_lock()
                    elif key == pynput.keyboard.Key.f12:
                        self.emergency_stop()
                except Exception:
                    pass
            with pynput.keyboard.Listener(on_press=on_press) as listener:
                listener.join()
        
        t = threading.Thread(target=listen, daemon=True)
        t.start()

    # --- Logic Methods ---

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        hwnd = win32gui.GetHwnd(self.root.winfo_id())
        styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        
        if self.is_locked:
            # Enable Click-Through
            styles |= win32con.WS_EX_TRANSPARENT
            self.status_lbl.config(text="[LOCKED]", fg="#00ff00")
            self.main_frame.config(highlightbackground="#00ff00")
            self.log("Menu Locked (Click-Through ON)")
        else:
            # Disable Click-Through (Interactive)
            styles &= ~win32con.WS_EX_TRANSPARENT
            self.status_lbl.config(text="[UNLOCKED]", fg="#ffaa00")
            self.main_frame.config(highlightbackground="#ffaa00")
            self.log("Menu Unlocked (Interactive)")
            
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, styles)
        # Force redraw
        win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)

    def toggle_bot(self):
        if self.engine.running:
            self.engine.stop()
            self.led_lbl.config(fg="#555555")
        else:
            if not self.config.get("region"):
                messagebox.showwarning("Warning", "Please select a region first!")
                return
            self.engine.start()
            self.led_lbl.config(fg="#00ff00")

    def emergency_stop(self):
        self.engine.stop()
        self.led_lbl.config(fg="#555555")
        self.log("EMERGENCY STOP TRIGGERED", "red")

    def pick_region(self):
        self.log("Minimize menu to select region...")
        self.root.iconify()
        time.sleep(0.5)
        
        # Simple crosshair selection logic could go here, using pyautogui for now
        # For a better UX, we'd draw an overlay, but keeping it simple:
        messagebox.showinfo("Region Select", "Click and drag to select the region on your screen.\n(This is a placeholder for full region drawing)")
        # In a full implementation, we'd use a transparent overlay to draw the rect
        # Simulating a region for demo:
        self.config["region"] = (100, 100, 200, 200) 
        self.log("Region set (Demo coords)", "green")
        self.save_config()

    def pick_color(self):
        if not self.config.get("region"):
            messagebox.showwarning("Error", "Select a region first!")
            return
        
        # Grab center pixel of region
        r = self.config["region"]
        center_x = r[0] + r[2]//2
        center_y = r[1] + r[3]//2
        color = pyautogui.pixel(center_x, center_y)
        
        self.config["target_color"] = list(color)
        self.log(f"Color picked: {color}", "cyan")
        self.save_config()

    def update_preview(self, frame):
        # Resize frame to fit label
        h, w, _ = frame.shape
        aspect = w / h
        new_w = 160
        new_h = int(new_w / aspect)
        
        resized = cv2.resize(frame, (new_w, new_h))
        resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(resized)
        imgtk = ImageTk.PhotoImage(image=img)
        
        self.preview_lbl.imgtk = imgtk
        self.preview_lbl.config(image=imgtk, text="")

    def update_stats(self, cps):
        self.cps_lbl.config(text=f"{cps} CPS")

    def log(self, msg, color="white"):
        self.log_text.insert(tk.END, f"> {msg}\n", color)
        self.log_text.see(tk.END)
        # Note: Tkinter text tags for color need configuration, simplified here

    def auto_snap_to_gd(self):
        try:
            gd_windows = [w for w in gw.getAllWindows() if 'geometry dash' in w.title.lower()]
            if gd_windows:
                gd = gd_windows[0]
                # Snap to top-right of GD
                x = gd.left + gd.width - 370 # 360 width + padding
                y = gd.top + 10
                
                # Only snap if we haven't moved manually far away (simple logic)
                self.root.geometry(f"+{int(x)}+{int(y)}")
                self.log("Snapped to Geometry Dash", "green")
        except Exception:
            pass
        self.root.after(5000, self.auto_snap_to_gd) # Check every 5s

    def update_loop(self):
        # Periodic updates if needed
        self.root.after(100, self.update_loop)

    # --- Dragging Logic ---
    def on_press(self, event):
        if not self.is_locked:
            # Only allow drag if clicked on title bar area (approx)
            if event.y < 30:
                self.drag_start_pos = (event.x, event.y)
                self.window_offset = (self.root.winfo_x(), self.root.winfo_y())

    def on_drag(self, event):
        if self.drag_start_pos and not self.is_locked:
            x = self.window_offset[0] + event.x - self.drag_start_pos[0]
            y = self.window_offset[1] + event.y - self.drag_start_pos[1]
            self.root.geometry(f"+{x}+{y}")

    def on_release(self, event):
        self.drag_start_pos = None

    # --- Config Handling ---
    def save_setting(self, key, value):
        self.config[key] = value
        # Debounce save could go here

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)
        self.log("Config Saved", "green")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def reset_config(self):
        self.config = DEFAULT_CONFIG.copy()
        self.save_config()
        self.log("Config Reset", "orange")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = GDOverlay()
    app.run()
