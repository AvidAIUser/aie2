import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import pyautogui
import numpy as np
import time
import threading
import json
import os
import random
from datetime import datetime

# Configuration
CONFIG_FILE = "gd_clickbot_config.json"
RECORDS_FILE = "gd_clickbot_records.json"

class HumanizedClickbot:
    def __init__(self):
        self.running = False
        self.paused = False
        self.mode = "smart"  # smart, record, playback, rhythm
        self.click_interval = 0.017  # ~60 FPS
        self.target_color = (50, 50, 50)  # Default ground color placeholder
        self.color_tolerance = 30
        self.window_title = "Geometry Dash"
        
        # Learning & Recording
        self.attempts = []
        self.current_attempt = []
        self.best_distance = 0
        self.recorded_clicks = []  # List of {time, x, y}
        self.playback_start_time = 0
        
        # Humanization
        self.reaction_time_min = 0.05
        self.reaction_time_max = 0.15
        self.jitter_chance = 0.02
        self.misclick_chance = 0.01
        
        # Stats
        self.total_clicks = 0
        self.successful_clicks = 0
        self.start_time = 0
        
        self.load_config()
        self.load_records()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.target_color = tuple(data.get("target_color", self.target_color))
                    self.color_tolerance = data.get("color_tolerance", self.color_tolerance)
                    self.click_interval = data.get("click_interval", self.click_interval)
            except: pass

    def save_config(self):
        data = {
            "target_color": self.target_color,
            "color_tolerance": self.color_tolerance,
            "click_interval": self.click_interval
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f)

    def load_records(self):
        if os.path.exists(RECORDS_FILE):
            try:
                with open(RECORDS_FILE, 'r') as f:
                    data = json.load(f)
                    self.recorded_clicks = data.get("recorded_clicks", [])
            except: pass

    def save_records(self):
        data = {"recorded_clicks": self.recorded_clicks}
        with open(RECORDS_FILE, 'w') as f:
            json.dump(data, f)

    def get_game_window(self):
        try:
            window = pyautogui.getWindowsWithTitle(self.window_title)[0]
            return window
        except IndexError:
            # Try finding any window with "Geometry" in title
            windows = pyautogui.getWindowsWithTitle("Geometry")
            if windows:
                self.window_title = windows[0].title
                return windows[0]
            return None

    def is_color_match(self, pixel_color, target_color, tolerance):
        if len(pixel_color) == 4: pixel_color = pixel_color[:3]
        if len(target_color) == 4: target_color = target_color[:3]
        
        r_diff = abs(pixel_color[0] - target_color[0])
        g_diff = abs(pixel_color[1] - target_color[1])
        b_diff = abs(pixel_color[2] - target_color[2])
        
        return r_diff <= tolerance and g_diff <= tolerance and b_diff <= tolerance

    def detect_obstacle(self, window):
        """Detects obstacles by looking for changes in the ground color or specific obstacle colors"""
        if not window:
            return False
            
        # Define scan area (bottom center of the window where ground usually is)
        w, h = window.width, window.height
        x_start = int(w * 0.3)
        x_end = int(w * 0.7)
        y_start = int(h * 0.6)
        y_end = int(h * 0.9)
        
        # Sample a few points in the scan area
        sample_x = random.randint(x_start, x_end)
        sample_y = random.randint(y_start, y_end)
        
        try:
            pixel = pyautogui.pixel(sample_x, sample_y)
            # If the pixel is NOT the ground color, it might be an obstacle
            if not self.is_color_match(pixel, self.target_color, self.color_tolerance):
                return True
        except:
            pass
            
        return False

    def humanize_click(self):
        """Applies humanization to the click"""
        if random.random() < self.misclick_chance:
            return False  # Simulate a missed click
            
        time.sleep(random.uniform(self.reaction_time_min, self.reaction_time_max))
        
        if random.random() < self.jitter_chance:
            # Tiny mouse movement jitter
            current_x, current_y = pyautogui.position()
            pyautogui.move(random.randint(-2, 2), random.randint(-2, 2), duration=0.01)
            
        pyautogui.click()
        self.total_clicks += 1
        return True

    def record_click(self):
        """Records the current state as a successful click"""
        current_time = time.time() - self.start_time
        x, y = pyautogui.position()
        self.current_attempt.append({
            "time": current_time,
            "x": x,
            "y": y
        })

    def run_smart_mode(self, window):
        """Main logic for smart auto-clicking"""
        if self.detect_obstacle(window):
            if self.humanize_click():
                self.successful_clicks += 1
                # If we are progressing, save this click pattern
                if len(self.current_attempt) > 0:
                    last_click = self.current_attempt[-1]
                    if time.time() - self.start_time - last_click['time'] > 0.5:
                        self.record_click()

    def run_record_mode(self):
        """Records user clicks manually"""
        # In record mode, we listen for actual user clicks via a hook or just track time
        # For simplicity, we assume if the bot is running in record mode, 
        # we are tracking the session time. Real click recording requires a global hook.
        # Instead, let's make Record Mode simply save the timeline of attempts.
        pass

    def run_playback_mode(self):
        """Replays recorded clicks"""
        if not self.recorded_clicks:
            return
            
        current_time = time.time() - self.playback_start_time
        
        # Find clicks that should happen now
        for click in self.recorded_clicks:
            if abs(click['time'] - current_time) < 0.01:
                pyautogui.click(click['x'], click['y'])
                self.total_clicks += 1
                break

    def loop(self):
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
                
            window = self.get_game_window()
            if not window:
                time.sleep(1)
                continue
                
            # Bring window to focus optionally (can be annoying, so optional)
            # window.activate() 
            
            current_time = time.time()
            
            if self.mode == "smart":
                self.run_smart_mode(window)
                # Constantly check for ground to reset attempt logic if died
                # Simple death detection: if no progress for 2 seconds after jump?
                # For now, just basic clicking
                time.sleep(self.click_interval)
                
            elif self.mode == "rhythm":
                pyautogui.click()
                self.total_clicks += 1
                time.sleep(self.click_interval)
                
            elif self.mode == "playback":
                if self.playback_start_time == 0:
                    self.playback_start_time = time.time()
                self.run_playback_mode()
                time.sleep(0.005) # High precision for playback
                
            elif self.mode == "record":
                # In this simplified version, Record mode just tracks the session
                # Real click recording needs a keyboard/mouse hook library like 'pynput'
                # We will simulate "learning" by assuming if the user survives longer, 
                # the clicks they made were good. 
                # Since we can't easily hook global clicks without extra deps, 
                # we rely on the user using Smart mode to generate data, 
                # or we add a "Manual Record" button that listens.
                time.sleep(0.1)

        self.save_config()
        self.save_records()

    def start(self):
        if not self.running:
            self.running = True
            self.paused = False
            self.start_time = time.time()
            if self.mode == "playback":
                self.playback_start_time = time.time()
            threading.Thread(target=self.loop, daemon=True).start()

    def stop(self):
        self.running = False
        self.paused = False
        
    def toggle_pause(self):
        self.paused = not self.paused

class ClickbotGUI:
    def __init__(self, root):
        self.bot = HumanizedClickbot()
        self.root = root
        self.root.title("GD Humanized Clickbot")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        self.create_widgets()
        self.update_stats()

    def create_widgets(self):
        # Title
        lbl_title = tk.Label(self.root, text="GD Humanized Clickbot", font=("Arial", 16, "bold"))
        lbl_title.pack(pady=10)

        # Status Frame
        frm_status = tk.Frame(self.root)
        frm_status.pack(pady=5)
        
        self.lbl_status = tk.Label(frm_status, text="Status: Stopped", fg="red", font=("Arial", 12, "bold"))
        self.lbl_status.pack(side=tk.LEFT, padx=10)
        
        self.lbl_mode = tk.Label(frm_status, text="Mode: Smart", fg="blue")
        self.lbl_mode.pack(side=tk.LEFT, padx=10)

        # Control Buttons
        frm_controls = tk.Frame(self.root)
        frm_controls.pack(pady=10)
        
        self.btn_start = tk.Button(frm_controls, text="START", bg="#4CAF50", fg="white", 
                                   width=10, height=2, command=self.toggle_start)
        self.btn_start.pack(side=tk.LEFT, padx=10)
        
        self.btn_stop = tk.Button(frm_controls, text="STOP", bg="#f44336", fg="white", 
                                  width=10, height=2, command=self.stop_bot)
        self.btn_stop.pack(side=tk.LEFT, padx=10)

        # Mode Selection
        frm_mode = tk.LabelFrame(self.root, text="Operation Mode", padx=10, pady=10)
        frm_mode.pack(fill="x", padx=20, pady=5)
        
        self.mode_var = tk.StringVar(value="smart")
        modes = [("Smart (Auto-Detect)", "smart"), ("Rhythm (Constant)", "rhythm"), 
                 ("Playback (Learned)", "playback"), ("Record Session", "record")]
        
        for text, mode in modes:
            rb = tk.Radiobutton(frm_mode, text=text, variable=self.mode_var, value=mode,
                                command=self.change_mode)
            rb.pack(anchor="w")

        # Settings
        frm_settings = tk.LabelFrame(self.root, text="Settings", padx=10, pady=10)
        frm_settings.pack(fill="x", padx=20, pady=5)
        
        # Color Picker
        frm_color = tk.Frame(frm_settings)
        frm_color.pack(fill="x", pady=5)
        tk.Label(frm_color, text="Target Ground Color:").pack(side=tk.LEFT)
        self.btn_color = tk.Button(frm_color, text="Pick Color", command=self.pick_color)
        self.btn_color.pack(side=tk.LEFT, padx=10)
        self.lbl_color_preview = tk.Label(frm_color, text=f"RGB: {self.bot.target_color}", relief="sunken")
        self.lbl_color_preview.pack(side=tk.LEFT)

        # Sliders
        tk.Label(frm_settings, text="Click Interval (sec):").pack(anchor="w")
        self.slider_interval = tk.Scale(frm_settings, from_=0.005, to=0.1, resolution=0.001, 
                                        orient=tk.HORIZONTAL, length=300)
        self.slider_interval.set(self.bot.click_interval)
        self.slider_interval.pack(anchor="w")
        
        tk.Label(frm_settings, text="Color Tolerance:").pack(anchor="w")
        self.slider_tolerance = tk.Scale(frm_settings, from_=10, to=100, orient=tk.HORIZONTAL, length=300)
        self.slider_tolerance.set(self.bot.color_tolerance)
        self.slider_tolerance.pack(anchor="w")

        # Stats Panel
        frm_stats = tk.LabelFrame(self.root, text="Statistics", padx=10, pady=10)
        frm_stats.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.lbl_total_clicks = tk.Label(frm_stats, text="Total Clicks: 0", anchor="w")
        self.lbl_total_clicks.pack(fill="x")
        
        self.lbl_learned = tk.Label(frm_stats, text="Learned Clicks: 0", anchor="w")
        self.lbl_learned.pack(fill="x")
        
        self.lbl_runtime = tk.Label(frm_stats, text="Runtime: 0s", anchor="w")
        self.lbl_runtime.pack(fill="x")

        # Instructions
        lbl_inst = tk.Label(self.root, text="Tip: Use 'Smart' mode. Pick the ground color first.\nEnsure GD window is titled 'Geometry Dash'", 
                            fg="gray", font=("Arial", 9))
        lbl_inst.pack(side=tk.BOTTOM, pady=10)

        # Start update loop
        self.root.after(100, self.update_stats)

    def toggle_start(self):
        if not self.bot.running:
            self.bot.mode = self.mode_var.get()
            self.bot.color_tolerance = self.slider_tolerance.get()
            self.bot.click_interval = self.slider_interval.get()
            self.bot.start()
            self.lbl_status.config(text="Status: Running", fg="green")
            self.btn_start.config(state=tk.DISABLED)
        else:
            self.bot.toggle_pause()
            if self.bot.paused:
                self.lbl_status.config(text="Status: Paused", fg="orange")
                self.btn_start.config(text="RESUME")
            else:
                self.lbl_status.config(text="Status: Running", fg="green")
                self.btn_start.config(text="START")

    def stop_bot(self):
        self.bot.stop()
        self.lbl_status.config(text="Status: Stopped", fg="red")
        self.btn_start.config(text="START", state=tk.NORMAL)
        self.btn_start.config(state=tk.NORMAL)

    def change_mode(self):
        self.bot.mode = self.mode_var.get()
        self.lbl_mode.config(text=f"Mode: {self.bot.mode.capitalize()}")
        if self.bot.mode == "playback":
            messagebox.showinfo("Playback Mode", "Make sure you have recorded clicks from previous sessions!")

    def pick_color(self):
        messagebox.showinfo("Pick Color", "Click OK, then select the ground color in Geometry Dash within 5 seconds.")
        self.root.after(1000, self.delayed_color_pick)

    def delayed_color_pick(self):
        # Wait a moment then grab color at cursor
        time.sleep(4)
        x, y = pyautogui.position()
        color = pyautogui.pixel(x, y)
        self.bot.target_color = color
        self.lbl_color_preview.config(text=f"RGB: {color}")
        self.bot.save_config()
        messagebox.showinfo("Color Set", f"Selected color: {color}")

    def update_stats(self):
        if self.bot.running:
            self.lbl_total_clicks.config(text=f"Total Clicks: {self.bot.total_clicks}")
            self.lbl_learned.config(text=f"Learned Clicks: {len(self.bot.recorded_clicks)}")
            
            if self.bot.start_time > 0:
                runtime = int(time.time() - self.bot.start_time)
                self.lbl_runtime.config(text=f"Runtime: {runtime}s")
        
        self.root.after(200, self.update_stats)

if __name__ == "__main__":
    root = tk.Tk()
    app = ClickbotGUI(root)
    root.mainloop()
