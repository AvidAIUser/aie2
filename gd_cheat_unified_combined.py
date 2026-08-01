import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import threading
import time
import json
import os
import win32gui
import win32con
import win32api
import ctypes
from PIL import Image, ImageGrab, ImageTk
import cv2
import numpy as np
import pynput.keyboard
import pynput.mouse
import pyautogui
import pygetwindow as gw

# --- Configuration ---
CONFIG_FILE = "gd_cheat_config.json"
HOTKEY_TOGGLE = "insert"  # Key to show/hide menu
HOTKEY_EMERGENCY = "f12"  # Emergency stop

# Win32 constants for custom window procedure
GWL_WNDPROC = -4
WM_NCHITTEST = 0x0084
HTTRANSPARENT = -1
HTCLIENT = 1

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


class GDClickbotUnified:
    def __init__(self):
        self.config = CheatConfig()
        self.root = None
        self.is_visible = True
        self.is_click_through = False
        self.drag_active = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.hwnd = None
        self.old_wndproc = None
        self.wndproc_callback = None

        # Runtime state
        self.cps = 0
        self.last_click_time = 0
        self.click_count = 0
        self.running = False
        self.gd_hwnd = None

        # Threading control
        self.click_thread = None
        self.monitor_thread = None
        self.stop_event = threading.Event()
        self.snap_thread = None
        self.stop_snap_loop = False

        # Setup hotkeys FIRST before GUI
        self.setup_hotkey()

        # Create GUI
        self.create_gui()
        
        # Start background monitoring AFTER GUI exists
        self.stop_monitoring = False
        self.monitor_thread = threading.Thread(target=self.monitor_gd_window, daemon=True)
        self.monitor_thread.start()
        
        # Try to find GD immediately (non-blocking)
        self.root.after(100, self.find_gd_window)

    def setup_hotkey(self):
        def on_press(key):
            try:
                if key.char == HOTKEY_TOGGLE or str(key) == f"<Key.{HOTKEY_TOGGLE}>":
                    self.toggle_menu()
                elif str(key) == f"<Key.{HOTKEY_EMERGENCY}>":
                    self.emergency_stop()
            except AttributeError:
                if str(key) == f"<Key.{HOTKEY_TOGGLE}>":
                    self.toggle_menu()
                elif str(key) == f"<Key.{HOTKEY_EMERGENCY}>":
                    self.emergency_stop()
        
        listener = pynput.keyboard.Listener(on_press=on_press)
        listener.start()

    def emergency_stop(self):
        """Emergency stop - halts all bot activity"""
        if self.running:
            self.running = False
            self.stop_event.set()
            self.btn_toggle.config(text="START BOT", bg="#2d2d30", fg="#00ff9d")
            self.status_lbl.config(text="● STOPPED", fg="#ff5555")
            self.log("EMERGENCY STOP TRIGGERED")

    def find_gd_window(self):
        """Finds Geometry Dash window and stores handle - SAFE non-blocking version"""
        if not hasattr(self, 'root') or self.root is None:
            return
            
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
                # Use after() to schedule snap on main thread safely
                self.root.after(0, self.snap_to_gd)
            else:
                if self.debug_logging_var.get() if hasattr(self, 'debug_logging_var') else False:
                    self.log("GD not found. Launch the game to attach.")
        except Exception as e:
            if self.debug_logging_var.get() if hasattr(self, 'debug_logging_var') else False:
                self.log(f"Error finding GD: {e}")

    def monitor_gd_window(self):
        """Background thread to detect GD window changes without freezing"""
        last_hwnd = None
        while not getattr(self, 'stop_monitoring', False):
            try:
                windows = gw.getWindowsWithTitle("Geometry Dash")
                if windows:
                    win = windows[0]
                    current_hwnd = win._hWnd
                    
                    # Only act if window state changed
                    if current_hwnd != last_hwnd:
                        last_hwnd = current_hwnd
                        self.gd_hwnd = current_hwnd
                        
                        # Schedule UI updates on main thread
                        if hasattr(self, 'root') and self.root:
                            self.root.after(0, lambda h=current_hwnd: self.on_gd_found(h))
                    elif not win.isActive:
                        # Window exists but not active
                        pass
                else:
                    if last_hwnd is not None:
                        last_hwnd = None
                        self.gd_hwnd = None
                        if hasattr(self, 'root') and self.root:
                            self.root.after(0, lambda: self.log("GD window lost."))
                
                time.sleep(1.5)  # Check every 1.5 seconds
            except Exception as e:
                if getattr(self, 'debug_logging_var', None) and self.debug_logging_var.get():
                    if hasattr(self, 'root') and self.root:
                        self.root.after(0, lambda err=e: self.log(f"Monitor error: {err}"))
                time.sleep(2.0)

    def on_gd_found(self, hwnd):
        """Called when GD is found - runs on main thread"""
        self.gd_hwnd = hwnd
        self.log(f"Attached to Geometry Dash (HWND: {hwnd})")
        
        # Only auto-snap if enabled
        if hasattr(self, 'auto_snap_var') and self.auto_snap_var.get():
            self.snap_to_gd()

    def snap_to_gd(self):
        """Moves the cheat menu to the top-right of the GD window - SAFE version"""
        if not hasattr(self, 'root') or self.root is None:
            return
        
        # Safety: don't snap if root is being destroyed
        try:
            self.root.update_idletasks()
        except:
            return
        
        # Try pygetwindow first (more reliable for modern Windows)
        try:
            gd_windows = [w for w in gw.getAllWindows() if 'geometry dash' in w.title.lower()]
            if gd_windows:
                gd = gd_windows[0]
                # Position menu at top-right inside the game window
                menu_w = 360
                menu_h = 580
                
                x = gd.left + gd.width - menu_w - 10
                y = gd.top + 10
                
                # Bounds check
                screen_w = self.root.winfo_screenwidth()
                screen_h = self.root.winfo_screenheight()
                x = max(0, min(x, screen_w - menu_w))
                y = max(0, min(y, screen_h - menu_h))
                
                self.root.geometry(f"{menu_w}x{menu_h}+{int(x)}+{int(y)}")
                self.log("Menu snapped to GD window (pygetwindow).")
                self.gd_hwnd = None  # Clear old handle
                return
        except Exception as e:
            if hasattr(self, 'debug_logging_var') and self.debug_logging_var.get():
                self.log(f"pygetwindow snap failed: {e}")
        
        # Fallback to win32gui method
        if not self.gd_hwnd:
            # Don't recursively call find_gd_window, just return
            return
        
        if not self.root:
            return

        try:
            rect = win32gui.GetWindowRect(self.gd_hwnd)
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top
            
            menu_w = 360
            menu_h = 580
            
            x = left + width - menu_w - 10
            y = top + 10
            
            # Bounds check
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            x = max(0, min(x, screen_w - menu_w))
            y = max(0, min(y, screen_h - menu_h))
            
            self.root.geometry(f"{menu_w}x{menu_h}+{int(x)}+{int(y)}")
            self.log("Menu snapped to GD window (win32gui).")
        except Exception as e:
            if hasattr(self, 'debug_logging_var') and self.debug_logging_var.get():
                self.log(f"Snap failed: {e}")

    def toggle_menu(self):
        self.is_visible = not self.is_visible
        if self.is_visible:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.set_click_through(False) # Become interactive when opened
            self.find_gd_window() # Re-scan for GD
        else:
            self.root.withdraw()

    def set_click_through(self, enable):
        """Makes the window click-through using proper WS_EX_LAYERED approach"""
        self.is_click_through = enable
        
        if not hasattr(self, 'hwnd') or self.hwnd is None:
            try:
                self.hwnd = self.root.winfo_id()
            except:
                return

        ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)

        if enable:
            # Add Transparent and Layered - this makes clicks pass through to GD
            ex_style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
            # Set opacity (200/255 for visibility but still see-through)
            ctypes.windll.user32.SetLayeredWindowAttributes(
                self.hwnd,
                0,
                200,
                win32con.LWA_ALPHA
            )
        else:
            # Remove Transparent - this makes window clickable again
            ex_style &= ~win32con.WS_EX_TRANSPARENT
            
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, ex_style)
        
        # Force window refresh to apply changes immediately
        self.root.update_idletasks()

    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("GD Clickbot Unified")
        self.root.overrideredirect(True) # Borderless
        self.root.attributes('-topmost', True)
        
        # Force window to be visible and on top
        self.root.lift()
        self.root.focus_force()
        self.root.update_idletasks()
        
        # Initial size
        self.root.geometry("360x580+100+100")  # Start at a visible position
        
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
        lbl_title = tk.Label(self.title_bar, text="☠ GD CHEAT MENU UNIFIED", 
                             bg=self.header_color, fg=self.accent_color, 
                             font=("Consolas", 10, "bold"), anchor="w", padx=10)
        lbl_title.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Status Label
        self.status_lbl = tk.Label(self.title_bar, text="● STOPPED", 
                                   bg=self.header_color, fg="#ff5555",
                                   font=("Consolas", 8, "bold"))
        self.status_lbl.pack(side=tk.RIGHT, padx=10)
        
        # Close Button
        btn_close = tk.Label(self.title_bar, text="✕", bg=self.header_color, fg="#ff5555",
                             font=("Arial", 12, "bold"), cursor="hand2", padx=8)
        btn_close.pack(side=tk.RIGHT)
        btn_close.bind("<Button-1>", lambda e: self.root.quit())
        
        # Drag Logic (Only on Title Bar)
        self.title_bar.bind("<ButtonPress-1>", self.start_drag)
        self.title_bar.bind("<B1-Motion>", self.do_drag)
        self.title_bar.bind("<ButtonRelease-1>", self.stop_drag)
        lbl_title.bind("<ButtonPress-1>", self.start_drag)
        lbl_title.bind("<B1-Motion>", self.do_drag)
        lbl_title.bind("<ButtonRelease-1>", self.stop_drag)

        # --- Tabs ---
        tab_control = ttk.Notebook(self.main_frame)
        tab_control.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook.Tab', background='#333333', foreground='white', padding=[10, 5])
        style.configure('TNotebook.Tab', font=('Consolas', 9))
        style.map('TNotebook.Tab', background=[('selected', '#1e1e1e')])
        
        # Tab 1: Aimbot (Clickbot)
        self.tab_aimbot = tk.Frame(tab_control, bg=self.bg_color)
        tab_control.add(self.tab_aimbot, text="  Aimbot  ")
        self.build_aimbot_tab()
        
        # Tab 2: Visuals
        self.tab_visuals = tk.Frame(tab_control, bg=self.bg_color)
        tab_control.add(self.tab_visuals, text="  Visuals  ")
        self.build_visuals_tab()
        
        # Tab 3: Config
        self.tab_config = tk.Frame(tab_control, bg=self.bg_color)
        tab_control.add(self.tab_config, text="  Config  ")
        self.build_config_tab()

        # Make controls interactive (remove click-through when hovering them)
        self.setup_control_bindings()
        
        # Bind tab control for interactivity
        tab_control.bind("<Enter>", lambda e: self.set_click_through(False))
        tab_control.bind("<Leave>", lambda e: self.set_click_through(self.is_click_through))
        tab_control.bind("<Button-1>", lambda e: self.set_click_through(False))
        tab_control.bind("<ButtonRelease-1>", lambda e: self.set_click_through(True))
        
        # Add FocusLost binding to restore click-through when clicking outside (e.g., on GD)
        self.root.bind("<FocusOut>", lambda e: self.set_click_through(True))
        
        # Initial state - start visible and interactive so user can see it
        self.set_click_through(False)
        
        # Start monitor loop
        self.root.after(100, self.update_monitor)

    def build_aimbot_tab(self):
        # Status Panel
        status_frame = tk.Frame(self.tab_aimbot, bg=self.frame_color, pady=5)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.led_lbl = tk.Label(status_frame, text="●", fg="#555555", bg=self.frame_color, font=("Consolas", 14, "bold"))
        self.led_lbl.pack(side=tk.LEFT, padx=10)
        
        self.cps_lbl = tk.Label(status_frame, text="CPS: 0", bg=self.frame_color, fg=self.text_color, font=("Consolas", 9))
        self.cps_lbl.pack(side=tk.LEFT, padx=10)
        
        # Live Preview
        prev_frame = tk.LabelFrame(self.tab_aimbot, text="Live Feed", bg=self.frame_color, fg="#888888", font=("Consolas", 8))
        prev_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.preview_lbl = tk.Label(prev_frame, bg="black", text="No Region Selected", fg="#555555", font=("Consolas", 8))
        self.preview_lbl.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Controls
        ctrl_frame = tk.Frame(self.tab_aimbot, bg=self.bg_color)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=5)
        
        lbl_delay = tk.Label(ctrl_frame, text="Click Delay (ms)", bg=self.bg_color, fg=self.text_color, font=("Consolas", 9))
        lbl_delay.pack(anchor="w")
        
        self.delay_var = tk.IntVar(value=self.config.click_delay)
        self.delay_scale = ttk.Scale(ctrl_frame, from_=1, to=100, variable=self.delay_var, orient=tk.HORIZONTAL,
                                command=lambda v: self.on_setting_change("delay", int(v)))
        self.delay_scale.pack(fill=tk.X)
        
        lbl_tol = tk.Label(ctrl_frame, text="Color Tolerance", bg=self.bg_color, fg=self.text_color, font=("Consolas", 9))
        lbl_tol.pack(anchor="w", pady=(10,0))
        
        self.tol_var = tk.IntVar(value=self.config.color_tolerance)
        self.tol_scale = ttk.Scale(ctrl_frame, from_=0, to=100, variable=self.tol_var, orient=tk.HORIZONTAL,
                              command=lambda v: self.on_setting_change("tolerance", int(v)))
        self.tol_scale.pack(fill=tk.X)
        
        # Buttons Row
        btn_row = tk.Frame(self.tab_aimbot, bg=self.bg_color)
        btn_row.pack(fill=tk.X, padx=10, pady=10)
        
        self.btn_pick_region = tk.Button(btn_row, text="🎯 Pick Region", command=self.pick_region,
                                         bg=self.frame_color, fg=self.text_color, activebackground=self.accent_color,
                                         font=("Consolas", 9), relief=tk.FLAT, cursor="hand2")
        self.btn_pick_region.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.btn_pick_color = tk.Button(btn_row, text="🎨 Pick Color", command=self.pick_color,
                                        bg=self.frame_color, fg=self.text_color, activebackground=self.accent_color,
                                        font=("Consolas", 9), relief=tk.FLAT, cursor="hand2")
        self.btn_pick_color.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # Info Labels
        self.info_region = tk.Label(self.tab_aimbot, text="Region: Not Set", bg=self.bg_color, fg="#888", font=("Consolas", 8), anchor="w")
        self.info_region.pack(fill=tk.X, pady=(2,0), padx=10)
        
        self.info_color = tk.Label(self.tab_aimbot, text="Color: Not Set", bg=self.bg_color, fg="#888", font=("Consolas", 8), anchor="w")
        self.info_color.pack(fill=tk.X, pady=(2,10), padx=10)
        
        # Start/Stop Button
        self.btn_toggle = tk.Button(self.tab_aimbot, text="START BOT", command=self.toggle_bot,
                                    bg="#2d2d30", fg="#00ff9d", activebackground="#00ff9d", activeforeground="#000",
                                    font=("Consolas", 12, "bold"), relief=tk.FLAT, cursor="hand2", pady=10)
        self.btn_toggle.pack(fill=tk.X, pady=10, padx=10)

    def build_visuals_tab(self):
        tk.Label(self.tab_visuals, text="Visual Options", bg=self.bg_color, fg="#888888", font=("Consolas", 10, "bold")).pack(pady=10)
        
        # ESP Options Frame
        esp_frame = tk.LabelFrame(self.tab_visuals, text="ESP / Overlay", bg=self.frame_color, fg="#aaa", font=("Consolas", 9))
        esp_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.esp_var = tk.BooleanVar(value=False)
        self.chk_esp = tk.Checkbutton(esp_frame, text="Enable ESP Overlay", variable=self.esp_var, 
                                bg=self.frame_color, fg="#ccc", selectcolor="#333333",
                                activebackground=self.frame_color, activeforeground="#ccc",
                                font=("Consolas", 9), command=self.toggle_esp)
        self.chk_esp.pack(pady=5, padx=10, anchor=tk.W)
        
        self.show_coords_var = tk.BooleanVar(value=True)
        self.chk_coords = tk.Checkbutton(esp_frame, text="Show Coordinates", variable=self.show_coords_var,
                                   bg=self.frame_color, fg="#ccc", selectcolor="#333333",
                                   activebackground=self.frame_color, activeforeground="#ccc",
                                   font=("Consolas", 9))
        self.chk_coords.pack(pady=5, padx=10, anchor=tk.W)
        
        # Color Picker for ESP
        color_frame = tk.Frame(esp_frame, bg=self.frame_color)
        color_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(color_frame, text="ESP Color:", bg=self.frame_color, fg="#aaa", font=("Consolas", 8)).pack(side=tk.LEFT)
        self.esp_color_btn = tk.Button(color_frame, text="█████", bg="#00ff9d", command=self.pick_esp_color,
                                      relief=tk.FLAT, cursor="hand2")
        self.esp_color_btn.pack(side=tk.RIGHT)
        self.esp_color = "#00ff9d"
        
        # Performance Options
        perf_frame = tk.LabelFrame(self.tab_visuals, text="Performance", bg=self.frame_color, fg="#aaa", font=("Consolas", 9))
        perf_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.fps_var = tk.BooleanVar(value=True)
        self.chk_fps = tk.Checkbutton(perf_frame, text="Show FPS Counter", variable=self.fps_var,
                                bg=self.frame_color, fg="#ccc", selectcolor="#333333",
                                activebackground=self.frame_color, activeforeground="#ccc",
                                font=("Consolas", 9))
        self.chk_fps.pack(pady=5, padx=10, anchor=tk.W)
        
        self.vsync_var = tk.BooleanVar(value=False)
        self.chk_vsync = tk.Checkbutton(perf_frame, text="Force VSync", variable=self.vsync_var,
                                  bg=self.frame_color, fg="#ccc", selectcolor="#333333",
                                  activebackground=self.frame_color, activeforeground="#ccc",
                                  font=("Consolas", 9))
        self.chk_vsync.pack(pady=5, padx=10, anchor=tk.W)
        
        # Info label
        tk.Label(self.tab_visuals, text="(More visuals coming soon...)", bg=self.bg_color, 
                fg="#555555", font=("Consolas", 8)).pack(side=tk.BOTTOM, pady=10)

    def toggle_esp(self):
        """Toggle ESP overlay visibility"""
        if self.esp_var.get():
            self.log("ESP Overlay Enabled")
        else:
            self.log("ESP Overlay Disabled")
    
    def pick_esp_color(self):
        """Pick color for ESP overlay"""
        color = colorchooser.askcolor(initialcolor=self.esp_color, title="Choose ESP Color")
        if color[1]:
            self.esp_color = color[1]
            self.esp_color_btn.config(bg=color[1])
            self.log(f"ESP Color set to {color[1]}")

    def build_config_tab(self):
        # Profiles Section
        tk.Label(self.tab_config, text="Profiles", bg=self.bg_color, fg="#888888", font=("Consolas", 10, "bold")).pack(pady=10)
        
        btn_frame = tk.Frame(self.tab_config, bg=self.bg_color)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="💾 Save Current", command=self.save_config, bg=self.frame_color, fg="white", relief=tk.FLAT, font=("Consolas", 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🔄 Reset Defaults", command=self.reset_config, bg="#552222", fg="white", relief=tk.FLAT, font=("Consolas", 9)).pack(side=tk.LEFT, padx=5)
        
        # Profile Selector (Placeholder for future multiple profiles)
        profile_frame = tk.Frame(self.tab_config, bg=self.bg_color)
        profile_frame.pack(pady=5)
        tk.Label(profile_frame, text="Active Profile:", bg=self.bg_color, fg="#aaa", font=("Consolas", 8)).pack(side=tk.LEFT, padx=5)
        self.profile_var = tk.StringVar(value="Default")
        self.profile_combo = ttk.Combobox(profile_frame, textvariable=self.profile_var, values=["Default", "Practice Mode", "Demon Rush"], state="readonly", width=15)
        self.profile_combo.pack(side=tk.LEFT)
        self.profile_combo.bind("<<ComboboxSelected>>", lambda e: self.load_profile())
        
        # Hotkeys Section
        tk.Label(self.tab_config, text="Hotkeys", bg=self.bg_color, fg="#888888", font=("Consolas", 10, "bold")).pack(pady=(20, 5))
        hotkey_frame = tk.Frame(self.tab_config, bg=self.frame_color)
        hotkey_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(hotkey_frame, text="INSERT", bg=self.frame_color, fg=self.accent_color, font=("Consolas", 9, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        tk.Label(hotkey_frame, text=": Toggle Menu Visibility", bg=self.frame_color, fg="#aaa", font=("Consolas", 8)).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        tk.Label(hotkey_frame, text="F12", bg=self.frame_color, fg="#ff5555", font=("Consolas", 9, "bold")).grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        tk.Label(hotkey_frame, text=": Emergency Stop (Halts Bot)", bg=self.frame_color, fg="#aaa", font=("Consolas", 8)).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Window Management
        tk.Label(self.tab_config, text="Window Management", bg=self.bg_color, fg="#888888", font=("Consolas", 10, "bold")).pack(pady=(15, 5))
        
        btn_attach = tk.Button(self.tab_config, text="📎 Snap to GD Window", command=self.snap_to_gd,
                               bg=self.frame_color, fg=self.accent_color, activebackground=self.accent_color, activeforeground="#000",
                               font=("Consolas", 9, "bold"), relief=tk.FLAT, cursor="hand2", pady=5)
        btn_attach.pack(fill=tk.X, pady=5, padx=10)
        
        self.auto_snap_var = tk.BooleanVar(value=True)
        self.chk_auto_snap = tk.Checkbutton(self.tab_config, text="Auto-snap to GD every 5s", variable=self.auto_snap_var,
                                      bg=self.bg_color, fg="#aaa", selectcolor="#333333",
                                      activebackground=self.bg_color, activeforeground="#aaa",
                                      font=("Consolas", 8))
        self.chk_auto_snap.pack(anchor=tk.W, padx=25, pady=2)
        
        # Advanced Settings
        tk.Label(self.tab_config, text="Advanced", bg=self.bg_color, fg="#888888", font=("Consolas", 10, "bold")).pack(pady=(15, 5))
        
        adv_frame = tk.Frame(self.tab_config, bg=self.bg_color)
        adv_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.debug_var = tk.BooleanVar(value=False)
        self.chk_debug = tk.Checkbutton(adv_frame, text="Debug Logging", variable=self.debug_var,
                                  bg=self.bg_color, fg="#aaa", selectcolor="#333333",
                                  activebackground=self.bg_color, activeforeground="#aaa",
                                  font=("Consolas", 8))
        self.chk_debug.pack(anchor=tk.W)
        
        self.topmost_var = tk.BooleanVar(value=True)
        self.chk_topmost = tk.Checkbutton(adv_frame, text="Always On Top", variable=self.topmost_var, command=self.toggle_topmost,
                                    bg=self.bg_color, fg="#aaa", selectcolor="#333333",
                                    activebackground=self.bg_color, activeforeground="#aaa",
                                    font=("Consolas", 8))
        self.chk_topmost.pack(anchor=tk.W, pady=2)
        
        # Helper Text
        lbl_help = tk.Label(self.tab_config, text=f"☠ Drag title bar to move menu\n☠ Press [{HOTKEY_TOGGLE.upper()}] anywhere to toggle menu", 
                            bg=self.bg_color, fg="#888888", font=("Consolas", 7), justify=tk.CENTER)
        lbl_help.pack(side=tk.BOTTOM, pady=10)

    def load_profile(self):
        """Load a saved profile (placeholder for future implementation)"""
        profile = self.profile_var.get()
        self.log(f"Loading profile: {profile}")
        # Future: Load profile-specific settings from JSON
        
    def toggle_topmost(self):
        """Toggle always-on-top setting"""
        if self.topmost_var.get():
            self.root.attributes('-topmost', True)
            self.log("Always on top: ENABLED")
        else:
            self.root.attributes('-topmost', False)
            self.log("Always on top: DISABLED")

    def setup_control_bindings(self):
        """Make controls interactive (remove click-through when hovering them)"""
        widgets = [self.btn_pick_region, self.btn_pick_color, self.btn_toggle, 
                   self.led_lbl, self.cps_lbl, self.info_region, self.info_color,
                   self.preview_lbl]
        for w in widgets:
            w.bind("<Enter>", lambda e: self.set_click_through(False))
            w.bind("<Leave>", lambda e: self.set_click_through(self.is_click_through))
            # Also bind click events to ensure interactivity
            w.bind("<Button-1>", lambda e: self.set_click_through(False))
            w.bind("<ButtonRelease-1>", lambda e: self.set_click_through(True))
        
        # Bind scales for interactivity
        if hasattr(self, 'delay_scale'):
            self.delay_scale.bind("<Enter>", lambda e: self.set_click_through(False))
            self.delay_scale.bind("<Leave>", lambda e: self.set_click_through(self.is_click_through))
            self.delay_scale.bind("<Button-1>", lambda e: self.set_click_through(False))
            self.delay_scale.bind("<ButtonRelease-1>", lambda e: self.set_click_through(True))
        
        if hasattr(self, 'tol_scale'):
            self.tol_scale.bind("<Enter>", lambda e: self.set_click_through(False))
            self.tol_scale.bind("<Leave>", lambda e: self.set_click_through(self.is_click_through))
            self.tol_scale.bind("<Button-1>", lambda e: self.set_click_through(False))
            self.tol_scale.bind("<ButtonRelease-1>", lambda e: self.set_click_through(True))
        
        # Bind combobox for interactivity
        if hasattr(self, 'profile_combo'):
            self.profile_combo.bind("<Enter>", lambda e: self.set_click_through(False))
            self.profile_combo.bind("<Leave>", lambda e: self.set_click_through(self.is_click_through))
            self.profile_combo.bind("<Button-1>", lambda e: self.set_click_through(False))
            self.profile_combo.bind("<ButtonRelease-1>", lambda e: self.set_click_through(True))
        
        # Bind checkbuttons separately (they need special handling)
        checkbuttons = [getattr(self, 'chk_esp', None), getattr(self, 'chk_coords', None), 
                        getattr(self, 'chk_fps', None), getattr(self, 'chk_vsync', None),
                        getattr(self, 'chk_auto_snap', None), getattr(self, 'chk_debug', None),
                        getattr(self, 'chk_topmost', None)]
        for cb in checkbuttons:
            if cb is not None:
                cb.bind("<Enter>", lambda e: self.set_click_through(False))
                cb.bind("<Leave>", lambda e: self.set_click_through(self.is_click_through))
                cb.bind("<Button-1>", lambda e: self.set_click_through(False))
                cb.bind("<ButtonRelease-1>", lambda e: self.set_click_through(True))

    def on_setting_change(self, name, value):
        if name == "delay":
            self.config.click_delay = value
            self.delay_var.set(value)
        elif name == "tolerance":
            self.config.color_tolerance = value
            self.tol_var.set(value)
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

    def pick_region(self):
        self.root.withdraw()
        time.sleep(0.2)
        
        # Create full screen overlay
        overlay = tk.Toplevel()
        overlay.attributes('-fullscreen', True, '-topmost', True, '-alpha', 0.3)
        overlay.configure(bg='red')
        overlay.attributes('-transparentcolor', 'red')
        
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
            self.led_lbl.config(fg="#00ff9d")
            self.stop_event.clear()
            
            self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
            self.click_thread.start()
            
            self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            self.log("Bot Started")
        else:
            self.btn_toggle.config(text="START BOT", bg="#2d2d30", fg="#00ff9d")
            self.status_lbl.config(text="● STOPPED", fg="#ff5555")
            self.led_lbl.config(fg="#555555")
            self.stop_event.set()
            self.cps = 0
            self.log("Bot Stopped")

    def click_loop(self):
        mouse = pynput.mouse.Controller()
        while not self.stop_event.is_set() and self.running:
            if self.check_color():
                mouse.click(pynput.mouse.Button.left, 1)
                self.click_count += 1
                time.sleep(self.config.click_delay / 1000.0)
            else:
                time.sleep(0.001) # Small sleep to prevent CPU spike

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
            
            # Compare RGB
            dist = np.sqrt(np.sum((avg_color - self.config.target_color)**2))
            result = dist < self.config.color_tolerance
            
            # Update preview periodically
            if hasattr(self, 'preview_lbl') and self.preview_lbl:
                self.update_preview(img_np)
            
            return result
        except:
            return False

    def update_preview(self, frame):
        """Update the live preview with captured frame"""
        try:
            # Resize frame to fit label
            h, w, _ = frame.shape
            if h == 0 or w == 0:
                return
            
            # Convert to RGB for display
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) if len(frame.shape) == 3 else frame
            
            new_w, new_h = 100, 80
            resized = cv2.resize(rgb_frame, (new_w, new_h))
            
            # Convert to PIL Image
            img = Image.fromarray(resized)
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.preview_lbl.imgtk = imgtk
            self.preview_lbl.config(image=imgtk, text="")
        except:
            pass

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
            
        # Auto-snap to GD periodically (from gd_clickbot_unified.py)
        # This runs every 5 seconds in the background
        self.root.after(5000, self.auto_snap_to_gd_loop)
             
        self.root.after(1000, self.update_monitor)

    def auto_snap_to_gd_loop(self):
        """Periodic auto-snap to GD window (from gd_clickbot_unified.py)"""
        if not self.auto_snap_var.get():
            return  # User disabled auto-snap
            
        try:
            gd_windows = [w for w in gw.getAllWindows() if 'geometry dash' in w.title.lower()]
            if gd_windows:
                gd = gd_windows[0]
                # Only snap if menu is visible and not being dragged
                if self.is_visible and not self.drag_active:
                    x = gd.left + gd.width - 370
                    y = gd.top + 10
                    # Check if we're far from expected position (avoid snapping if user moved it)
                    current_x = self.root.winfo_x()
                    current_y = self.root.winfo_y()
                    if abs(current_x - x) > 50 or abs(current_y - y) > 50:
                        pass  # User moved it, don't auto-snap
                    else:
                        self.root.geometry(f"+{int(x)}+{int(y)}")
                        self.gd_hwnd = None  # Clear old handle
                        if self.debug_var.get():
                            self.log("Auto-snapped to GD window")
        except Exception as e:
            if self.debug_var.get():
                self.log(f"Auto-snap error: {e}")

    def save_config(self):
        self.config.save()
        self.log("Config Saved")

    def reset_config(self):
        self.config.click_delay = 10
        self.config.color_tolerance = 30
        self.config.target_color = None
        self.config.click_region = None
        self.config.save()
        
        # Update UI
        self.delay_var.set(10)
        self.tol_var.set(30)
        self.info_region.config(text="Region: Not Set")
        self.info_color.config(text="Color: Not Set", fg="#888")
        self.log("Config Reset")

    def log(self, msg):
        print(f"[GD Cheat] {msg}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = GDClickbotUnified()
    app.run()
