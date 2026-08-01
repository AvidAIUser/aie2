import pygame
import pyautogui
import numpy as np
import time
import json
import os
import threading
from datetime import datetime
from pynput.mouse import Controller as MouseController, Button as MouseButton
from pynput.keyboard import Controller as KeyboardController, Key

# Configuration Paths
DATA_DIR = os.path.join(os.path.expanduser("~"), ".gd_clickbot")
LEARNED_FILE = os.path.join(DATA_DIR, "learned_patterns.json")

class ClickBotEngine:
    def __init__(self):
        self.running = False
        self.paused = False
        self.mode = "SMART"  # SMART, RHYTHM, PLAYBACK
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        
        # Settings
        self.click_interval = 0.017  # ~60 CPS
        self.reaction_time = 0.040   # Base reaction delay
        self.jitter = 2.0            # Pixel jitter
        self.misclick_chance = 0.02  # 2% chance to miss
        
        # Vision
        self.scan_region = None      # (x, y, w, h)
        self.ground_color = None     # (r, g, b)
        self.threshold = 30          # Color difference threshold
        
        # Learning
        self.attempt_start_time = 0
        self.current_attempt_clicks = [] # List of (timestamp, x_offset_from_scan)
        self.learned_patterns = []   # List of successful timestamps relative to start
        self.success_threshold = 2.0 # Seconds of progress to count as "success"
        self.last_progress_dist = 0
        self.last_progress_time = 0
        
        # State
        self.last_click_time = 0
        self.min_click_gap = 0.045   # Minimum 45ms between clicks
        self.click_count = 0
        self.death_count = 0
        
        self.load_data()

    def load_data(self):
        if os.path.exists(LEARNED_FILE):
            try:
                with open(LEARNED_FILE, 'r') as f:
                    data = json.load(f)
                    self.learned_patterns = data.get("patterns", [])
                    print(f"Loaded {len(self.learned_patterns)} learned patterns.")
            except:
                self.learned_patterns = []

    def save_data(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(LEARNED_FILE, 'w') as f:
            json.dump({"patterns": self.learned_patterns}, f)
        print(f"Saved {len(self.learned_patterns)} patterns.")

    def set_scan_region(self, x, y, w, h):
        self.scan_region = (x, y, w, h)

    def capture_ground_color(self):
        if not self.scan_region:
            return None
        x, y, w, h = self.scan_region
        # Sample center bottom area
        cx, cy = x + w // 2, y + h - 5
        try:
            pixel = pyautogui.pixel(cx, cy)
            self.ground_color = (pixel[0], pixel[1], pixel[2])
            return self.ground_color
        except:
            return None

    def is_obstacle_detected(self):
        if not self.scan_region or self.ground_color is None:
            return False
        
        x, y, w, h = self.scan_region
        try:
            # Capture the scan region
            screenshot = pyautogui.screenshot(region=self.scan_region)
            img = np.array(screenshot)
            
            # Calculate difference from ground color
            diff = np.mean(np.abs(img.astype(float) - self.ground_color), axis=2)
            
            # If average difference in the bottom half is high, obstacle detected
            # We focus on the bottom 30% of the scan region where spikes/blocks appear
            bottom_section = diff[int(h*0.4):, :] 
            max_diff = np.max(bottom_section)
            
            return max_diff > self.threshold
        except Exception as e:
            return False

    def get_current_time(self):
        return time.time() - self.attempt_start_time

    def record_click(self):
        t = self.get_current_time()
        # Store relative time and a dummy offset (since we don't know exact player X easily without memory)
        # In this visual-only version, we store global time relative to attempt start
        self.current_attempt_clicks.append(t)

    def handle_death(self):
        self.death_count += 1
        current_time = self.get_current_time()
        
        # If we survived longer than threshold, save the clicks from this run
        if current_time > self.success_threshold:
            # Filter clicks that happened before death but contributed to progress
            # Simple strategy: Save all clicks from this run if we beat our previous best significantly
            # Or merge with existing patterns if they align
            
            # For simplicity: Add these clicks to learned patterns with a weight
            new_patterns = [(t, 1.0) for t in self.current_attempt_clicks] # 1.0 confidence
            
            # Merge logic could go here, for now we append
            self.learned_patterns.extend([t for t, _ in new_patterns])
            self.learned_patterns.sort()
            print(f"Death at {current_time:.2f}s. Saved {len(new_patterns)} clicks. Total patterns: {len(self.learned_patterns)}")
            self.save_data()
        else:
            print(f"Death at {current_time:.2f}s. Too short to learn.")
            
        self.current_attempt_clicks = []
        self.attempt_start_time = time.time() # Reset timer for next attempt

    def should_click(self):
        now = time.time()
        if now - self.last_click_time < self.min_click_gap:
            return False

        current_t = self.get_current_time()

        # 1. PLAYBACK MODE
        if self.mode == "PLAYBACK":
            # Find closest learned pattern
            for pt in self.learned_patterns:
                if abs(pt - current_t) < 0.03: # 30ms window
                    # Humanize the timing slightly
                    if np.random.random() > self.misclick_chance:
                        self.last_click_time = now
                        self.click_count += 1
                        return True
            return False

        # 2. SMART MODE (Vision + Learning assist)
        elif self.mode == "SMART":
            # Check vision
            obstacle = self.is_obstacle_detected()
            
            # Check if a learned pattern is coming up soon (predictive)
            upcoming_learned = False
            for pt in self.learned_patterns:
                if 0.05 < (pt - current_t) < 0.15: # Look ahead 50-150ms
                    upcoming_learned = True
                    break
            
            if obstacle or upcoming_learned:
                # Apply reaction time delay simulation
                # In a real loop, we'd wait, but here we just decide to click now
                # adding a small random variance to reaction
                if np.random.random() > self.misclick_chance:
                    self.last_click_time = now
                    self.click_count += 1
                    self.record_click()
                    return True
            return False

        # 3. RHYTHM MODE
        elif self.mode == "RHYTHM":
            if np.random.random() > self.misclick_chance:
                self.last_click_time = now
                self.click_count += 1
                self.record_click()
                return True
            return False

        return False

    def perform_click(self):
        # Apply jitter
        j_x = np.random.uniform(-self.jitter, self.jitter)
        j_y = np.random.uniform(-self.jitter, self.jitter)
        
        current_pos = self.mouse.position
        target_x = current_pos[0] + j_x
        target_y = current_pos[1] + j_y
        
        # Move slightly then click (simulates finger movement)
        self.mouse.position = (target_x, target_y)
        self.mouse.press(MouseButton.left)
        self.mouse.release(MouseButton.left)
        
        # Return to approximate original (optional, GD doesn't care about cursor pos usually)
        # self.mouse.position = current_pos 

    def update(self):
        if not self.running or self.paused:
            return

        if self.should_click():
            self.perform_click()

class OverlayGUI:
    def __init__(self, bot):
        self.bot = bot
        pygame.init()
        
        # Create a transparent overlay window
        info = pygame.display.Info()
        self.width, self.height = info.current_w, info.current_h
        
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.NOFRAME | pygame.FULLSCREEN)
        pygame.display.set_caption("GD Clickbot Overlay")
        
        # Make window click-through except for our UI area (handled manually)
        # Note: True click-through on Windows requires win32api extensions. 
        # We will handle input manually and ignore rest.
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Consolas", 18)
        self.title_font = pygame.font.SysFont("Consolas", 24, bold=True)
        
        # UI State
        self.menu_visible = True
        self.dragging = False
        self.drag_offset = (0, 0)
        
        # UI Rects
        self.panel_rect = pygame.Rect(50, 50, 320, 480)
        self.header_rect = pygame.Rect(50, 50, 320, 40)
        
        # Buttons
        self.btn_start = pygame.Rect(70, 110, 130, 40)
        self.btn_stop = pygame.Rect(220, 110, 130, 40)
        self.btn_pause = pygame.Rect(70, 160, 130, 40)
        self.btn_resume = pygame.Rect(220, 160, 130, 40)
        
        self.btn_set_region = pygame.Rect(70, 220, 280, 30)
        self.btn_capture_color = pygame.Rect(70, 260, 280, 30)
        self.btn_clear_data = pygame.Rect(70, 300, 280, 30)
        
        # Toggles
        self.rect_smart = pygame.Rect(70, 350, 90, 30)
        self.rect_rhythm = pygame.Rect(170, 350, 90, 30)
        self.rect_playback = pygame.Rect(270, 350, 90, 30)
        
        # Sliders (simplified as text for now)
        self.slider_cps_rect = pygame.Rect(70, 400, 200, 10)
        
        self.running = True
        self.region_setting_mode = False

    def draw_text(self, text, pos, color=(255, 255, 255), font=None):
        f = font or self.font
        surf = f.render(text, True, color)
        self.screen.blit(surf, pos)

    def draw_button(self, rect, text, active=False, color=(60, 60, 60)):
        if active:
            color = (100, 200, 100)
        pygame.draw.rect(self.screen, color, rect, border_radius=5)
        pygame.draw.rect(self.screen, (200, 200, 200), rect, 2, border_radius=5)
        
        # Center text
        text_surf = self.font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def draw_learning_graph(self):
        # Draw a mini graph of learned patterns
        graph_rect = pygame.Rect(70, 430, 280, 40)
        pygame.draw.rect(self.screen, (30, 30, 30), graph_rect, border_radius=3)
        pygame.draw.rect(self.screen, (100, 100, 100), graph_rect, 1, border_radius=3)
        
        if not self.bot.learned_patterns:
            self.draw_text("No patterns learned yet", (75, 435), (150, 150, 150))
            return

        # Normalize patterns to fit graph (show last 5 seconds)
        max_time = max(self.bot.learned_patterns[-1], 5.0)
        scale_x = graph_rect.width / max_time
        scale_y = graph_rect.height
        
        for t in self.bot.learned_patterns:
            if t > max_time - 5.0: # Only show recent
                x = graph_rect.x + (t - (max_time - 5.0)) * scale_x
                y = graph_rect.y + scale_y - 5
                pygame.draw.circle(self.screen, (0, 255, 255), (int(x), int(y)), 2)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_INSERT:
                    self.menu_visible = not self.menu_visible
                
                if event.key == pygame.K_ESCAPE and self.region_setting_mode:
                    self.region_setting_mode = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    pos = event.pos
                    
                    # Drag logic
                    if self.header_rect.collidepoint(pos):
                        self.dragging = True
                        self.drag_offset = (pos[0] - self.panel_rect.x, pos[1] - self.panel_rect.y)
                    
                    # Button Logic
                    if self.btn_start.collidepoint(pos):
                        self.bot.running = True
                        self.bot.paused = False
                        self.bot.attempt_start_time = time.time()
                    elif self.btn_stop.collidepoint(pos):
                        self.bot.running = False
                        self.bot.paused = False
                    elif self.btn_pause.collidepoint(pos):
                        self.bot.paused = True
                    elif self.btn_resume.collidepoint(pos):
                        self.bot.paused = False
                    
                    elif self.btn_set_region.collidepoint(pos):
                        self.start_region_setup()
                    elif self.btn_capture_color.collidepoint(pos):
                        col = self.bot.capture_ground_color()
                        print(f"Captured color: {col}")
                    elif self.btn_clear_data.collidepoint(pos):
                        self.bot.learned_patterns = []
                        self.bot.save_data()
                    
                    # Mode Selection
                    elif self.rect_smart.collidepoint(pos):
                        self.bot.mode = "SMART"
                    elif self.rect_rhythm.collidepoint(pos):
                        self.bot.mode = "RHYTHM"
                    elif self.rect_playback.collidepoint(pos):
                        self.bot.mode = "PLAYBACK"

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False
                    if self.region_setting_mode:
                        self.finalize_region_setup(event.pos)

            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    self.panel_rect.x = event.pos[0] - self.drag_offset[0]
                    self.panel_rect.y = event.pos[1] - self.drag_offset[1]
                    # Update children rects
                    offset_x = self.panel_rect.x - 50
                    offset_y = self.panel_rect.y - 50
                    
                    self.header_rect.x = 50 + offset_x
                    self.header_rect.y = 50 + offset_y
                    
                    self.btn_start.x = 70 + offset_x; self.btn_start.y = 110 + offset_y
                    self.btn_stop.x = 220 + offset_x; self.btn_stop.y = 110 + offset_y
                    self.btn_pause.x = 70 + offset_x; self.btn_pause.y = 160 + offset_y
                    self.btn_resume.x = 220 + offset_x; self.btn_resume.y = 160 + offset_y
                    
                    self.btn_set_region.x = 70 + offset_x; self.btn_set_region.y = 220 + offset_y
                    self.btn_capture_color.x = 70 + offset_x; self.btn_capture_color.y = 260 + offset_y
                    self.btn_clear_data.x = 70 + offset_x; self.btn_clear_data.y = 300 + offset_y
                    
                    self.rect_smart.x = 70 + offset_x; self.rect_smart.y = 350 + offset_y
                    self.rect_rhythm.x = 170 + offset_x; self.rect_rhythm.y = 350 + offset_y
                    self.rect_playback.x = 270 + offset_x; self.rect_playback.y = 350 + offset_y
                    
                    self.slider_cps_rect.x = 70 + offset_x; self.slider_cps_rect.y = 400 + offset_y

    def start_region_setup(self):
        self.region_setting_mode = True
        self.temp_start = None
        print("Click and drag on the game screen to define the scan area...")

    def finalize_region_setup(self, end_pos):
        if self.temp_start:
            x1, y1 = self.temp_start
            x2, y2 = end_pos
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            x = min(x1, x2)
            y = min(y1, y2)
            if w > 10 and h > 10:
                self.bot.set_scan_region(x, y, w, h)
                print(f"Scan region set: {x}, {y}, {w}, {h}")
        self.region_setting_mode = False

    def draw(self):
        # Clear screen (transparent black)
        self.screen.fill((0, 0, 0))
        self.screen.set_alpha(0) # Fully transparent background
        
        if self.menu_visible:
            # Draw Panel Background
            panel_surf = pygame.Surface((self.panel_rect.w, self.panel_rect.h), pygame.SRCALPHA)
            panel_surf.fill((20, 20, 20, 220)) # Dark grey with alpha
            pygame.draw.rect(panel_surf, (100, 100, 100), (0,0, self.panel_rect.w, self.panel_rect.h), 2, border_radius=8)
            self.screen.blit(panel_surf, (self.panel_rect.x, self.panel_rect.y))
            
            # Header
            pygame.draw.rect(self.screen, (50, 50, 50), self.header_rect, border_top_left_radius=8, border_top_right_radius=8)
            self.draw_text("GD Clickbot Pro", (self.panel_rect.x + 10, self.panel_rect.y + 10), (255, 255, 255), self.title_font)
            
            # Status
            status = "RUNNING" if self.bot.running and not self.bot.paused else ("PAUSED" if self.bot.paused else "STOPPED")
            color = (0, 255, 0) if self.bot.running and not self.bot.paused else (255, 0, 0)
            self.draw_text(f"Status: {status}", (self.panel_rect.x + 10, self.panel_rect.y + 50), color)
            self.draw_text(f"Mode: {self.bot.mode}", (self.panel_rect.x + 150, self.panel_rect.y + 50), (200, 200, 200))
            self.draw_text(f"Clicks: {self.bot.click_count}", (self.panel_rect.x + 10, self.panel_rect.y + 75), (200, 200, 200))
            self.draw_text(f"Deaths: {self.bot.death_count}", (self.panel_rect.x + 150, self.panel_rect.y + 75), (200, 200, 200))
            self.draw_text(f"Patterns: {len(self.bot.learned_patterns)}", (self.panel_rect.x + 10, self.panel_rect.y + 90), (100, 255, 255))

            # Buttons
            self.draw_button(self.btn_start, "START", active=self.bot.running and not self.bot.paused, color=(40, 100, 40))
            self.draw_button(self.btn_stop, "STOP", color=(100, 40, 40))
            self.draw_button(self.btn_pause, "PAUSE", active=self.bot.paused, color=(100, 100, 40))
            self.draw_button(self.btn_resume, "RESUME", color=(40, 100, 100))
            
            self.draw_button(self.btn_set_region, "1. Set Scan Region", color=(40, 40, 100))
            self.draw_button(self.btn_capture_color, "2. Capture Ground", color=(40, 40, 100))
            self.draw_button(self.btn_clear_data, "Clear Learned Data", color=(80, 40, 40))
            
            # Modes
            c_smart = (0, 200, 0) if self.bot.mode == "SMART" else (50, 50, 50)
            c_rhythm = (0, 200, 0) if self.bot.mode == "RHYTHM" else (50, 50, 50)
            c_play = (0, 200, 0) if self.bot.mode == "PLAYBACK" else (50, 50, 50)
            
            pygame.draw.rect(self.screen, c_smart, self.rect_smart, border_radius=4)
            self.draw_text("SMART", (self.rect_smart.x+10, self.rect_smart.y+5), (255,255,255))
            
            pygame.draw.rect(self.screen, c_rhythm, self.rect_rhythm, border_radius=4)
            self.draw_text("RHYTHM", (self.rect_rhythm.x+5, self.rect_rhythm.y+5), (255,255,255))
            
            pygame.draw.rect(self.screen, c_play, self.rect_playback, border_radius=4)
            self.draw_text("PLAY", (self.rect_playback.x+15, self.rect_playback.y+5), (255,255,255))
            
            # Graph
            self.draw_learning_graph()
            
            # Instructions
            if self.region_setting_mode:
                inst_surf = self.font.render("DRAG ON SCREEN TO SET REGION", True, (255, 255, 0))
                self.screen.blit(inst_surf, (self.panel_rect.x, self.panel_rect.y - 30))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.bot.update()
            self.draw()
            self.clock.tick(60) # Limit to 60 FPS for UI
        
        pygame.quit()

def main():
    print("Starting GD Clickbot Overlay...")
    print("Press INSERT to toggle menu visibility.")
    
    bot = ClickBotEngine()
    gui = OverlayGUI(bot)
    
    try:
        gui.run()
    except KeyboardInterrupt:
        pass
    finally:
        bot.save_data()

if __name__ == "__main__":
    main()
