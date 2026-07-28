import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import numpy as np
import time
import threading
import json
import os
import random
import cv2
from datetime import datetime
from pynput import mouse as pynput_mouse

# Ensure directory exists for saving data
DATA_DIR = os.path.join(os.path.expanduser("~"), ".gd_clickbot")
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, "learned_clicks.json")

class HumanizationConfig:
    def __init__(self, reaction_time=50.0, variance=20.0, misclick_chance=0.02, 
                 jitter=2.0, fatigue_rate=0.0001):
        self.reaction_time = reaction_time  # ms
        self.variance = variance            # ms
        self.misclick_chance = misclick_chance
        self.jitter = jitter                # pixels
        self.fatigue_rate = fatigue_rate    # degradation per click

class ClickBotEngine:
    def __init__(self, config: HumanizationConfig):
        self.config = config
        self.running = False
        self.paused = False
        self.mode = "smart"  # smart, rhythm, playback
        self.click_interval = 0.017  # ~60 FPS
        self.learned_clicks = []  # List of {frame_offset, duration, mode}
        self.current_attempt_start = 0
        self.last_progress = 0
        self.session_clicks = []
        self.fatigue_level = 0
        self.window_title = "Geometry Dash"
        self.ground_color = None
        self.scan_region = None
        self.lock = threading.Lock()
        self.last_click_time = 0
        self.min_click_gap = 0.05  # Minimum 50ms between clicks to prevent spam

    def load_learned_clicks(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.learned_clicks = data.get('clicks', [])
                    print(f"Loaded {len(self.learned_clicks)} learned clicks.")
            except Exception as e:
                print(f"Error loading data: {e}")
                self.learned_clicks = []

    def save_learned_clicks(self):
        with self.lock:
            data = {
                'timestamp': datetime.now().isoformat(),
                'clicks': self.learned_clicks,
                'count': len(self.learned_clicks)
            }
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved {len(self.learned_clicks)} learned clicks.")

    def add_learned_click(self, offset, duration=0.1, mode="cube"):
        """Add a successful click pattern to the library"""
        with self.lock:
            # Check for duplicates nearby
            is_new = True
            for existing in self.learned_clicks:
                if abs(existing['frame_offset'] - offset) < 5: # 5 frame tolerance
                    is_new = False
                    break
            
            if is_new:
                self.learned_clicks.append({
                    'frame_offset': offset,
                    'duration': duration,
                    'mode': mode
                })
                # Sort by offset
                self.learned_clicks.sort(key=lambda x: x['frame_offset'])

    def get_humanized_delay(self):
        base = self.config.reaction_time / 1000.0
        variance = random.uniform(-self.config.variance, self.config.variance) / 1000.0
        fatigue = self.fatigue_level * self.config.fatigue_rate
        return max(0.005, base + variance + fatigue)

    def apply_jitter(self):
        if self.config.jitter > 0:
            dx = random.uniform(-self.config.jitter, self.config.jitter)
            dy = random.uniform(-self.config.jitter, self.config.jitter)
            current_x, current_y = pyautogui.position()
            pyautogui.moveTo(current_x + dx, current_y + dy, duration=0.01)

    def perform_click(self, duration=0.1):
        # Prevent clicking too fast
        now = time.time()
        if now - self.last_click_time < self.min_click_gap:
            return
            
        if random.random() < self.config.misclick_chance:
            self.last_click_time = now
            return # Simulate missed click
        
        self.apply_jitter()
        pyautogui.mouseDown()
        time.sleep(duration)
        pyautogui.mouseUp()
        self.last_click_time = now
        
        # Increase fatigue slightly
        self.fatigue_level += 1

    def capture_ground_color(self):
        """User helper to capture ground color for detection"""
        print("Capturing ground color in 3 seconds...")
        time.sleep(3)
        x, y = pyautogui.position()
        # Sample a small area
        screenshot = pyautogui.screenshot(region=(x-5, y-5, 10, 10))
        self.ground_color = np.array(screenshot).mean(axis=(0, 1))
        print(f"Ground color captured: {self.ground_color}")
        return self.ground_color

    def set_scan_region(self, x, y, w, h):
        self.scan_region = (x, y, w, h)

    def detect_obstacle(self):
        """Detect obstacle by comparing screen region to ground color"""
        if self.ground_color is None or self.scan_region is None:
            return False
        
        try:
            screenshot = pyautogui.screenshot(region=self.scan_region)
            img = np.array(screenshot)
            current_color = img.mean(axis=(0, 1))
            
            # Calculate Euclidean distance
            diff = np.linalg.norm(current_color - self.ground_color)
            
            # Threshold for detection (tune this value)
            return diff > 30.0 
        except Exception:
            return False

    def run_loop(self, callback_status):
        self.running = True
        self.fatigue_level = 0
        self.current_attempt_start = time.time()
        self.last_progress = 0
        self.session_clicks = []
        self.last_click_time = 0
        
        # Load learned clicks at start of run
        if self.mode == 'playback':
            self.load_learned_clicks()

        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue

            try:
                now = time.time()
                elapsed = now - self.current_attempt_start
                
                if self.mode == 'rhythm':
                    self.perform_click()
                    time.sleep(self.click_interval)
                
                elif self.mode == 'playback':
                    clicked_this_frame = False
                    for click_data in self.learned_clicks:
                        offset = click_data['frame_offset'] * 0.017 # Assuming 60fps frames
                        if abs(elapsed - offset) < 0.015: # 15ms window
                            self.perform_click(duration=click_data.get('duration', 0.1))
                            clicked_this_frame = True
                            break
                    
                    if not clicked_this_frame:
                        time.sleep(0.005) # Small sleep to prevent CPU spike
                
                elif self.mode == 'smart':
                    if self.detect_obstacle():
                        delay = self.get_humanized_delay()
                        time.sleep(delay) # Reaction time
                        self.perform_click()
                        
                        # Record this click as potentially successful
                        frame_offset = int((now - self.current_attempt_start) / 0.017)
                        self.session_clicks.append({'frame': frame_offset, 'time': now})
                    
                    time.sleep(0.005)

                # Update UI status
                if callback_status:
                    callback_status(elapsed, len(self.session_clicks))

            except Exception as e:
                print(f"Loop error: {e}")
                time.sleep(0.5)

        # Run finished
        if self.mode == 'smart' and len(self.session_clicks) > 0:
            # Simple heuristic: if we ran for more than 2 seconds, assume clicks were good
            if (time.time() - self.current_attempt_start) > 2.0:
                for click in self.session_clicks:
                    offset = int((click['time'] - self.current_attempt_start) / 0.017)
                    self.add_learned_click(offset)
                self.save_learned_clicks()
                print("Session clicks saved to library.")

    def stop(self):
        self.running = False

    def toggle_pause(self):
        self.paused = not self.paused
        return self.paused

class ClickBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GD Unified Clickbot (Learn & Play)")
        self.root.geometry("500x650")
        self.root.resizable(False, False)

        self.bot = ClickBotEngine(HumanizationConfig())
        self.thread = None

        self.create_widgets()

    def create_widgets(self):
        # Title
        lbl_title = tk.Label(self.root, text="GD Unified Clickbot", font=("Arial", 16, "bold"))
        lbl_title.pack(pady=10)

        # Status Frame
        frm_status = tk.LabelFrame(self.root, text="Status", padx=10, pady=10)
        frm_status.pack(fill="x", padx=10, pady=5)
        
        self.lbl_status = tk.Label(frm_status, text="Status: Stopped", fg="red", font=("Consolas", 12))
        self.lbl_status.pack(anchor="w")
        
        self.lbl_timer = tk.Label(frm_status, text="Time: 0.00s | Clicks: 0", font=("Consolas", 10))
        self.lbl_timer.pack(anchor="w")

        # Controls Frame
        frm_controls = tk.Frame(self.root)
        frm_controls.pack(fill="x", padx=10, pady=5)

        self.btn_start = tk.Button(frm_controls, text="START", command=self.start_bot, bg="#4CAF50", fg="white", width=10)
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_stop = tk.Button(frm_controls, text="STOP", command=self.stop_bot, bg="#f44336", fg="white", width=10)
        self.btn_stop.grid(row=0, column=1, padx=5)

        self.btn_pause = tk.Button(frm_controls, text="PAUSE", command=self.toggle_pause, width=10)
        self.btn_pause.grid(row=0, column=2, padx=5)

        # Mode Selection
        frm_mode = tk.LabelFrame(self.root, text="Operation Mode", padx=10, pady=10)
        frm_mode.pack(fill="x", padx=10, pady=5)

        self.mode_var = tk.StringVar(value="smart")
        rb_smart = tk.Radiobutton(frm_mode, text="Smart (Detect & Learn)", variable=self.mode_var, value="smart", command=self.update_mode)
        rb_smart.pack(anchor="w")
        rb_rhythm = tk.Radiobutton(frm_mode, text="Rhythm (Interval)", variable=self.mode_var, value="rhythm", command=self.update_mode)
        rb_rhythm.pack(anchor="w")
        rb_playback = tk.Radiobutton(frm_mode, text="Playback (Learned Runs)", variable=self.mode_var, value="playback", command=self.update_mode)
        rb_playback.pack(anchor="w")

        # Settings Frame
        frm_settings = tk.LabelFrame(self.root, text="Settings", padx=10, pady=10)
        frm_settings.pack(fill="x", padx=10, pady=5)

        # Interval Slider
        tk.Label(frm_settings, text="Click Interval (Rhythm Mode):").grid(row=0, column=0, sticky="w")
        self.slider_interval = tk.Scale(frm_settings, from_=0.005, to=0.1, resolution=0.001, orient="horizontal", length=200)
        self.slider_interval.set(0.017)
        self.slider_interval.grid(row=0, column=1, padx=10)

        # Reaction Time
        tk.Label(frm_settings, text="Reaction Time (ms):").grid(row=1, column=0, sticky="w")
        self.entry_reaction = tk.Entry(frm_settings, width=10)
        self.entry_reaction.insert(0, "50")
        self.entry_reaction.grid(row=1, column=1, sticky="w", padx=10)

        # Jitter
        tk.Label(frm_settings, text="Jitter (px):").grid(row=2, column=0, sticky="w")
        self.entry_jitter = tk.Entry(frm_settings, width=10)
        self.entry_jitter.insert(0, "2.0")
        self.entry_jitter.grid(row=2, column=1, sticky="w", padx=10)

        # Setup Helpers
        frm_helpers = tk.Frame(self.root)
        frm_helpers.pack(fill="x", padx=10, pady=10)

        tk.Button(frm_helpers, text="Set Scan Region (Drag Mouse)", command=self.set_region).pack(side="left", padx=5)
        tk.Button(frm_helpers, text="Capture Ground Color", command=self.capture_color).pack(side="left", padx=5)
        tk.Button(frm_helpers, text="Clear Learned Data", command=self.clear_data).pack(side="left", padx=5)

        # Info Log
        frm_log = tk.LabelFrame(self.root, text="Info / Log", padx=5, pady=5)
        frm_log.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.txt_log = tk.Text(frm_log, height=8, state="disabled")
        self.txt_log.pack(fill="both", expand=True)

        self.log("Ready. Configure settings and press START.")
        self.log(f"Data stored in: {DATA_FILE}")

    def log(self, message):
        self.txt_log.config(state="normal")
        self.txt_log.insert("end", f"> {message}\n")
        self.txt_log.see("end")
        self.txt_log.config(state="disabled")

    def update_mode(self):
        self.bot.mode = self.mode_var.get()
        self.log(f"Mode switched to: {self.bot.mode}")
        if self.bot.mode == 'playback':
            self.bot.load_learned_clicks()
            self.log(f"Loaded {len(self.bot.learned_clicks)} patterns.")

    def update_status(self, elapsed, clicks):
        status_text = "Running" if not self.bot.paused else "Paused"
        color = "orange" if self.bot.paused else "green"
        self.lbl_status.config(text=f"Status: {status_text}", fg=color)
        self.lbl_timer.config(text=f"Time: {elapsed:.2f}s | Clicks: {clicks}")

    def start_bot(self):
        if self.thread and self.thread.is_alive():
            self.log("Bot already running.")
            return

        # Update config from UI
        self.bot.config.reaction_time = float(self.entry_reaction.get())
        self.bot.config.jitter = float(self.entry_jitter.get())
        self.bot.click_interval = self.slider_interval.get()
        self.bot.mode = self.mode_var.get()

        if self.bot.mode == 'smart' and (self.bot.ground_color is None or self.bot.scan_region is None):
            messagebox.showwarning("Warning", "Scan region or ground color not set! Smart mode may not work correctly.\nUse the helper buttons to set them.")

        self.thread = threading.Thread(target=self.bot.run_loop, args=(self.update_status,), daemon=True)
        self.thread.start()
        self.log("Bot started.")

    def stop_bot(self):
        if self.thread:
            self.bot.stop()
            self.thread.join(timeout=2.0)
            self.log("Bot stopped.")
            self.lbl_status.config(text="Status: Stopped", fg="red")

    def toggle_pause(self):
        if self.thread and self.thread.is_alive():
            is_paused = self.bot.toggle_pause()
            state = "Paused" if is_paused else "Resumed"
            self.log(f"Bot {state}.")

    def set_region(self):
        self.log("Move mouse to top-left of scan area, click, then move to bottom-right and click.")
        def get_coords():
            p1 = pyautogui.position()
            self.log(f"Top-Left selected: {p1}")
            # Wait for second click implicitly by blocking or just instructing user
            # For simplicity in this script, we'll just take two rapid clicks logic or manual entry
            # Implementing a simple wait loop for two clicks
            coords = []
            def on_click(x, y, button, pressed):
                if pressed:
                    coords.append((x, y))
                    if len(coords) == 2:
                        return False
            
            import pynput.mouse
            with pynput.mouse.Listener(on_click=on_click) as listener:
                listener.join()
            
            if len(coords) == 2:
                x1, y1 = coords[0]
                x2, y2 = coords[1]
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                x = min(x1, x2)
                y = min(y1, y2)
                self.bot.set_scan_region(x, y, w, h)
                self.log(f"Region set: x={x}, y={y}, w={w}, h={h}")
            else:
                self.log("Region selection cancelled.")
        
        threading.Thread(target=get_coords, daemon=True).start()

    def capture_color(self):
        self.log("Position mouse over the ground/wall and click to capture color...")
        def get_color():
            import pynput.mouse
            clicked = False
            def on_click(x, y, button, pressed):
                nonlocal clicked
                if pressed and not clicked:
                    clicked = True
                    pyautogui.moveTo(x, y) # Move to ensure accuracy
                    self.bot.capture_ground_color()
                    self.log("Color captured!")
                    return False
            
            with pynput.mouse.Listener(on_click=on_click) as listener:
                listener.join()
        
        threading.Thread(target=get_color, daemon=True).start()

    def clear_data(self):
        if messagebox.askyesno("Confirm", "Delete all learned click patterns?"):
            self.bot.learned_clicks = []
            self.bot.save_learned_clicks()
            self.log("Learned data cleared.")

if __name__ == "__main__":
    # Need pynput for the mouse listeners in setup
    try:
        import pynput
    except ImportError:
        print("Please install pynput: pip install pynput")
        # Fallback or exit
        # For this script we assume it's installed or handle gracefully
        pass

    root = tk.Tk()
    app = ClickBotGUI(root)
    root.mainloop()
