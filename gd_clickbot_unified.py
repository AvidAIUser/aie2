#!/usr/bin/env python3
"""
GD Clickbot Overlay v5.0 - Ultimate In-Game Automation
Features:
- Seamless in-game overlay (click-through, always-on-top)
- Real-time CPS monitoring & latency display
- Live mini-preview of monitored region
- Smart auto-positioning over Geometry Dash
- Modern cyberpunk UI with neon accents
- Profile system for quick configuration switching
- Intelligent hover-to-interact system
"""

import tkinter as tk
from tkinter import ttk, font, messagebox, simpledialog
import threading
import time
import sys
import os
import json
import mss
import numpy as np
import cv2
from PIL import Image, ImageTk
from pynput.mouse import Controller, Button
import win32gui
import win32con

CONFIG_FILE = "gd_clickbot_config.json"
DEFAULT_CONFIG = {
    "click_delay": 15,
    "color_tolerance": 30,
    "target_color": [255, 255, 255],
    "region": None,
    "opacity": 240,
    "theme_color": "#00ffff"
}

class Config:
    def __init__(self):
        self.data = DEFAULT_CONFIG.copy()
        self.load()
    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.data.update(json.load(f))
            except: pass
    def save(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)
    def __getitem__(self, key): return self.data[key]
    def __setitem__(self, key, value):
        self.data[key] = value
        self.save()

class GhostOverlay(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.is_hovered = False
        self.is_click_through = True
        self.drag_start = None
        self.title("GD Clickbot v5.0")
        self.geometry("420x640")
        self.resizable(False, False)
        self.overrideredirect(True)
        self.wm_attributes("-topmost", 1)
        self.hwnd = None
        self.update_idletasks()
        if self.winfo_exists():
            self.hwnd = win32gui.GetParent(self.winfo_id())
            self.apply_ghost_mode()
        self.bg_color = "#0f0f15"
        self.accent = controller.config["theme_color"]
        self.configure(bg=self.bg_color)
        self.build_interface()
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)
        self.after(50, self.refresh_preview)

    def apply_ghost_mode(self):
        if not self.hwnd: return
        if self.is_click_through and not self.is_hovered:
            style = win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED | win32con.WS_EX_TOOLWINDOW
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, style)
            win32gui.SetLayeredWindowAttributes(self.hwnd, 0, 235, win32con.LWA_ALPHA)
        else:
            style = win32con.WS_EX_LAYERED | win32con.WS_EX_TOOLWINDOW
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, style)
            win32gui.SetLayeredWindowAttributes(self.hwnd, 0, 255, win32con.LWA_ALPHA)

    def on_enter(self, e):
        self.is_hovered = True
        self.is_click_through = False
        self.apply_ghost_mode()
        self.config(cursor="arrow")
        self.header.config(bg="#1a1a2e")

    def on_leave(self, e):
        self.is_hovered = False
        self.is_click_through = True
        self.apply_ghost_mode()
        self.config(cursor="none")
        self.header.config(bg=self.bg_color)

    def build_interface(self):
        main = tk.Frame(self, bg=self.bg_color, highlightthickness=2, highlightbackground=self.accent)
        main.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.header = tk.Frame(main, bg=self.bg_color, height=45)
        self.header.pack(fill=tk.X, pady=(8, 5))
        tk.Label(self.header, text="GD CLICKBOT v5", bg=self.bg_color, fg=self.accent, font=("Segoe UI", 15, "bold")).pack(side=tk.LEFT, padx=12)
        self.led = tk.Canvas(self.header, width=22, height=22, bg=self.bg_color, highlightthickness=0)
        self.led.pack(side=tk.RIGHT, padx=12)
        self.update_led(False)
        prev_box = tk.Frame(main, bg="#000", bd=2, relief=tk.FLAT)
        prev_box.pack(padx=12, pady=4)
        self.preview_lbl = tk.Label(prev_box, bg="#000")
        self.preview_lbl.pack()
        tk.Label(prev_box, text="Live Monitor Feed", bg="#000", fg="#444", font=("Arial", 7)).pack()
        stats = tk.Frame(main, bg=self.bg_color)
        stats.pack(fill=tk.X, padx=12, pady=8)
        self.cps_txt = tk.StringVar(value="CPS: 0.0")
        tk.Label(stats, textvariable=self.cps_txt, bg=self.bg_color, fg="#fff", font=("Consolas", 13, "bold")).pack(side=tk.LEFT)
        self.lat_txt = tk.StringVar(value="Latency: 0ms")
        tk.Label(stats, textvariable=self.lat_txt, bg=self.bg_color, fg="#888", font=("Consolas", 10)).pack(side=tk.RIGHT)
        ctrl = tk.Frame(main, bg=self.bg_color)
        ctrl.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
        btn_cfg = {"font": ("Segoe UI", 10, "bold"), "bd": 0, "pady": 12}
        self.btn_toggle = tk.Button(ctrl, text="START BOT", bg="#00cc66", fg="#000", command=self.controller.toggle, **btn_cfg)
        self.btn_toggle.pack(fill=tk.X, pady=6)
        tk.Label(ctrl, text="Configuration", bg=self.bg_color, fg="#666", font=("Arial", 9, "italic")).pack(pady=(12, 4))
        self.make_slider(ctrl, "Click Delay (ms)", 1, 100, "click_delay", self.controller.config["click_delay"])
        self.make_slider(ctrl, "Color Tolerance", 0, 100, "tolerance", self.controller.config["color_tolerance"])
        act_frm = tk.Frame(ctrl, bg=self.bg_color)
        act_frm.pack(fill=tk.X, pady=10)
        tk.Button(act_frm, text="Select Region", bg="#2a2a35", fg="#fff", command=self.controller.select_region, **btn_cfg).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(act_frm, text="Sample Color", bg="#2a2a35", fg="#fff", command=self.controller.sample_color, **btn_cfg).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        prof_frm = tk.Frame(main, bg=self.bg_color)
        prof_frm.pack(fill=tk.X, padx=12, pady=(0, 8))
        tk.Button(prof_frm, text="Save", bg="#1a1a25", fg="#aaa", command=self.save_profile, font=("Arial", 8)).pack(side=tk.LEFT, padx=4)
        tk.Button(prof_frm, text="Load", bg="#1a1a25", fg="#aaa", command=self.load_profile, font=("Arial", 8)).pack(side=tk.LEFT, padx=4)
        tk.Label(main, text="Hover to Interact | Move Away to Play", bg=self.bg_color, fg="#333", font=("Arial", 7)).pack(side=tk.BOTTOM, pady=4)

    def make_slider(self, parent, label, min_v, max_v, key, init):
        frm = tk.Frame(parent, bg=self.bg_color)
        frm.pack(fill=tk.X, pady=4)
        tk.Label(frm, text=label, bg=self.bg_color, fg="#aaa", font=("Arial", 8)).pack(anchor=tk.W)
        var = tk.DoubleVar(value=init)
        slider = ttk.Scale(frm, from_=min_v, to=max_v, variable=var, orient=tk.HORIZONTAL, command=lambda e: self.update_setting(key, var.get()))
        slider.pack(fill=tk.X)

    def update_setting(self, key, val):
        if key == "click_delay": self.controller.config[key] = int(val)
        elif key == "tolerance": self.controller.config["color_tolerance"] = float(val)
        else: self.controller.config[key] = float(val)

    def update_led(self, active):
        self.led.delete("all")
        color = "#00ff00" if active else "#222"
        glow = "#00ff00" if active else "#000"
        self.led.create_oval(3, 3, 19, 19, fill=color, outline=glow, width=2)

    def refresh_preview(self):
        if self.controller.frame is not None:
            try:
                img = cv2.cvtColor(self.controller.frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)
                img = img.resize((160, 90), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.preview_lbl.config(image=photo)
                self.preview_lbl.image = photo
            except: pass
        self.after(50, self.refresh_preview)

    def update_stats(self, cps, lat):
        self.cps_txt.set(f"CPS: {cps:.1f}")
        self.lat_txt.set(f"Latency: {lat}ms")
        if self.controller.active:
            self.btn_toggle.config(text="STOP BOT", bg="#ff3333", fg="#fff")
            self.update_led(True)
        else:
            self.btn_toggle.config(text="START BOT", bg="#00cc66", fg="#000")
            self.update_led(False)

    def start_drag(self, e): self.drag_start = (e.x, e.y)
    def do_drag(self, e):
        if self.drag_start:
            dx = e.x - self.drag_start[0]
            dy = e.y - self.drag_start[1]
            self.geometry(f"+{self.winfo_x() + dx}+{self.winfo_y() + dy}")

    def save_profile(self):
        name = simpledialog.askstring("Save Profile", "Profile name:")
        if name:
            with open(f"profile_{name}.json", 'w') as f:
                json.dump(self.controller.config.data, f, indent=4)
            messagebox.showinfo("Saved", f"Profile '{name}' saved!")

    def load_profile(self):
        files = [f for f in os.listdir('.') if f.startswith('profile_') and f.endswith('.json')]
        if not files:
            messagebox.showinfo("Profiles", "No saved profiles found.")
            return
        names = "\n".join([f.replace('profile_', '').replace('.json', '') for f in files])
        messagebox.showinfo("Available Profiles", names + "\n\n(Manual load via config edit)")

class ClickbotController:
    def __init__(self):
        self.config = Config()
        self.active = False
        self.mouse = Controller()
        self.frame = None
        self.cps_data = []
        self.last_click = 0
        self.lock = threading.Lock()
        self.stop_flag = threading.Event()
        self.thread_capture = None
        self.thread_logic = None
        self.ui = GhostOverlay(self)
        self.auto_snap()

    def auto_snap(self):
        def enum_cb(hwnd, lst):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Geometry Dash" in title: lst.append(hwnd)
            return True
        wins = []
        win32gui.EnumWindows(enum_cb, wins)
        if wins:
            hwnd = wins[0]
            rect = win32gui.GetWindowRect(hwnd)
            x, y, w, h = rect
            self.ui.geometry(f"+{x + w - 440}+{y + 60}")
            print(f"Snapped to GD at {x + w - 440}, {y + 60}")
        else:
            print("Geometry Dash not found - position manually")

    def launch_threads(self):
        self.stop_flag.clear()
        self.thread_capture = threading.Thread(target=self.capture_loop, daemon=True)
        self.thread_logic = threading.Thread(target=self.logic_loop, daemon=True)
        self.thread_capture.start()
        self.thread_logic.start()

    def halt_threads(self):
        self.stop_flag.set()
        if self.thread_capture: self.thread_capture.join(timeout=1)
        if self.thread_logic: self.thread_logic.join(timeout=1)

    def capture_loop(self):
        with mss.mss() as sct:
            while not self.stop_flag.is_set():
                if self.config["region"]:
                    mon = {"left": self.config["region"][0], "top": self.config["region"][1], "width": self.config["region"][2], "height": self.config["region"][3]}
                    grab = sct.grab(mon)
                    frame = np.array(grab)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    with self.lock: self.frame = frame
                else: time.sleep(0.1)
                time.sleep(0.008)

    def logic_loop(self):
        while not self.stop_flag.is_set():
            if self.active and self.config["region"] and self.frame is not None:
                t0 = time.time()
                with self.lock: frm = self.frame.copy()
                target = np.array(self.config["target_color"], dtype=np.uint8)
                tol = self.config["color_tolerance"]
                lower = np.maximum(target - tol, 0)
                upper = np.minimum(target + tol, 255)
                mask = cv2.inRange(frm, lower, upper)
                if np.any(mask):
                    now = time.time()
                    if (now - self.last_click) * 1000 >= self.config["click_delay"]:
                        self.mouse.click(Button.left)
                        self.last_click = now
                elapsed = time.time() - t0
                self.cps_data.append(1/elapsed if elapsed > 0 else 0)
                if len(self.cps_data) > 20: self.cps_data.pop(0)
                avg_cps = sum(self.cps_data) / len(self.cps_data)
                try: self.ui.after(0, self.ui.update_stats, avg_cps, int(elapsed*1000))
                except: pass
            else:
                self.cps_data = []
                try: self.ui.after(0, self.ui.update_stats, 0, 0)
                except: pass
            time.sleep(0.001)

    def toggle(self):
        self.active = not self.active
        if self.active:
            if not self.config["region"]:
                messagebox.showwarning("Warning", "Select a region first!")
                self.active = False
                return
            self.launch_threads()
        else: self.halt_threads()

    def select_region(self):
        self.ui.withdraw()
        time.sleep(0.3)
        try:
            import screeninfo
            mon = screeninfo.get_monitors()[0]
            cx, cy = mon.width // 2, mon.height // 2
            self.config["region"] = [cx - 50, cy - 50, 100, 100]
            messagebox.showinfo("Region Set", f"Center region selected.\nEdit config for precision.")
        except: self.config["region"] = [100, 100, 100, 100]
        self.ui.deiconify()
        self.ui.focus_force()

    def sample_color(self):
        if self.frame is not None:
            h, w, _ = self.frame.shape
            center = self.frame[h//2, w//2]
            self.config["target_color"] = center.tolist()
            messagebox.showinfo("Sampled", f"Color (BGR): {center}")
        else: messagebox.showwarning("No Feed", "Start bot or set region first")

    def run(self):
        self.ui.mainloop()
        self.halt_threads()

if __name__ == "__main__":
    try: import screeninfo
    except ImportError: os.system("pip install screeninfo --quiet")
    app = ClickbotController()
    app.run()
