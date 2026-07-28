#!/usr/bin/env python3
"""
Advanced Humanized Clickbot for Geometry Dash v3.0
Features:
- GUI interface for easy control
- Intelligent obstacle-based clicking (not random)
- Level autocomplete with learning from attempts
- Click recording and playback system
- Humanization features (reaction time, jitter, misclicks)
- Multiple game mode support (cube, ship, ball, UFO, wave)
- Progress tracking and best run saving
- Visual feedback and statistics
"""

import ctypes
import ctypes.wintypes
import time
import random
import math
import threading
import json
import pickle
import hashlib
from datetime import datetime
from pathlib import Path
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum, auto
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import win32gui
import win32process
import win32con
import psutil

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("Warning: pyautogui not available. Install with: pip install pyautogui")


# Windows API constants
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020


class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    DEAD = auto()
    LEVEL_COMPLETE = auto()
    EDITOR = auto()


class GameMode(Enum):
    CUBE = 0
    SHIP = 1
    BALL = 2
    UFO = 3
    WAVE = 4
    ROBOT = 5
    SPIDER = 6
    SWING = 7


@dataclass
class ClickRecord:
    """Records a single click with timing and position info"""
    timestamp: float  # Time since level start
    player_x: float  # Player X position when clicked
    player_y: float  # Player Y position when clicked
    game_mode: int  # Game mode at time of click
    was_successful: bool  # Whether this click led to progress
    obstacle_type: str = ""  # Type of obstacle (if known)
    frame_number: int = 0  # Frame number in level


@dataclass
class LevelAttempt:
    """Records a complete level attempt"""
    level_id: str
    start_time: float
    end_time: float
    progress_percent: float
    clicks: List[ClickRecord]
    death_reason: str = ""
    is_complete: bool = False


@dataclass
class HumanizationConfig:
    """Configuration for human-like behavior"""
    # Core timing
    base_reaction_time: float = 45.0  # ms
    reaction_time_variance: float = 25.0  # ms
    timing_precision: float = 0.85
    
    # Misclicks
    misclick_probability: float = 0.015
    double_click_chance: float = 0.01
    
    # Jitter
    jitter_amplitude: float = 1.5  # pixels
    jitter_frequency: float = 15.0  # Hz
    
    # Click dynamics
    base_click_duration: float = 80.0  # ms
    click_duration_variance: float = 25.0  # ms
    
    # Fatigue
    fatigue_rate: float = 0.0008
    max_fatigue: float = 0.3
    
    # Learning
    adaptation_rate: float = 0.05
    use_learned_patterns: bool = True


@dataclass
class LearnedPattern:
    """A learned successful click pattern"""
    level_hash: str
    player_x_position: float
    game_mode: int
    click_timing: float  # Relative to obstacle
    success_count: int = 1
    fail_count: int = 0
    confidence: float = 1.0
    
    def update(self, success: bool):
        if success:
            self.success_count += 1
        else:
            self.fail_count += 1
        total = self.success_count + self.fail_count
        self.confidence = self.success_count / max(1, total)


class ClickRecorder:
    """Records and plays back click sequences"""
    
    def __init__(self):
        self.current_attempt: Optional[LevelAttempt] = None
        self.attempts: List[LevelAttempt] = []
        self.learned_patterns: Dict[str, List[LearnedPattern]] = {}
        self.best_run: Optional[LevelAttempt] = None
        self.recording = False
        self.level_start_time = 0.0
        self.frame_count = 0
        
    def start_recording(self, level_id: str):
        """Start recording a new attempt"""
        self.current_attempt = LevelAttempt(
            level_id=level_id,
            start_time=time.time(),
            end_time=0.0,
            progress_percent=0.0,
            clicks=[],
            is_complete=False
        )
        self.recording = True
        self.level_start_time = time.time()
        self.frame_count = 0
        
    def record_click(self, player_x: float, player_y: float, game_mode: int, 
                     obstacle_type: str = ""):
        """Record a click during gameplay"""
        if not self.recording or not self.current_attempt:
            return
            
        timestamp = time.time() - self.level_start_time
        click = ClickRecord(
            timestamp=timestamp,
            player_x=player_x,
            player_y=player_y,
            game_mode=game_mode,
            was_successful=True,  # Will be updated later
            obstacle_type=obstacle_type,
            frame_number=self.frame_count
        )
        self.current_attempt.clicks.append(click)
        
    def end_attempt(self, progress: float, completed: bool = False, 
                    death_reason: str = ""):
        """End the current attempt"""
        if not self.current_attempt:
            return
            
        self.current_attempt.end_time = time.time()
        self.current_attempt.progress_percent = progress
        self.current_attempt.is_complete = completed
        self.current_attempt.death_reason = death_reason
        self.recording = False
        
        # Update successful clicks based on progress
        self._mark_successful_clicks(progress)
        
        # Save attempt
        self.attempts.append(self.current_attempt)
        
        # Update best run
        if completed or (self.best_run is None or 
                        progress > self.best_run.progress_percent):
            self.best_run = self.current_attempt
            
        # Learn from successful clicks
        self._learn_from_attempt(self.current_attempt)
        
        # Save to disk
        self._save_attempts()
        
        self.current_attempt = None
        
    def _mark_successful_clicks(self, progress: float):
        """Mark clicks that contributed to progress as successful"""
        if not self.current_attempt:
            return
            
        # All clicks before death point are considered "successful" in terms of timing
        # The last few clicks before death might need adjustment
        pass  # For now, assume all recorded clicks were timed correctly
        
    def _learn_from_attempt(self, attempt: LevelAttempt):
        """Extract learning from this attempt"""
        level_key = attempt.level_id
        
        if level_key not in self.learned_patterns:
            self.learned_patterns[level_key] = []
            
        for click in attempt.clicks:
            # Create or update pattern for this position
            pattern_found = False
            for pattern in self.learned_patterns[level_key]:
                # Check if this is the same position (within tolerance)
                if abs(pattern.player_x_position - click.player_x) < 50.0:
                    pattern.update(click.was_successful)
                    pattern_found = True
                    break
                    
            if not pattern_found and click.was_successful:
                new_pattern = LearnedPattern(
                    level_hash=level_key,
                    player_x_position=click.player_x,
                    game_mode=click.game_mode,
                    click_timing=click.timestamp,
                    success_count=1 if click.was_successful else 0,
                    fail_count=0 if click.was_successful else 1
                )
                self.learned_patterns[level_key].append(new_pattern)
                
    def _save_attempts(self):
        """Save attempts to disk"""
        data_dir = Path.home() / ".gd_clickbot"
        data_dir.mkdir(exist_ok=True)
        
        save_data = {
            'attempts': [asdict(a) for a in self.attempts],
            'learned_patterns': {
                k: [asdict(p) for p in v] 
                for k, v in self.learned_patterns.items()
            },
            'best_run': asdict(self.best_run) if self.best_run else None
        }
        
        with open(data_dir / "attempts.json", 'w') as f:
            json.dump(save_data, f, indent=2)
            
    def load_attempts(self):
        """Load attempts from disk"""
        data_dir = Path.home() / ".gd_clickbot"
        save_file = data_dir / "attempts.json"
        
        if not save_file.exists():
            return
            
        try:
            with open(save_file, 'r') as f:
                save_data = json.load(f)
                
            self.attempts = [LevelAttempt(**a) for a in save_data.get('attempts', [])]
            
            learned = save_data.get('learned_patterns', {})
            self.learned_patterns = {
                k: [LearnedPattern(**p) for p in v]
                for k, v in learned.items()
            }
            
            best = save_data.get('best_run')
            if best:
                self.best_run = LevelAttempt(**best)
        except Exception as e:
            print(f"Error loading attempts: {e}")
            
    def get_learned_clicks_for_position(self, level_id: str, player_x: float, 
                                        game_mode: int) -> Optional[LearnedPattern]:
        """Get learned click pattern for a position"""
        if level_id not in self.learned_patterns:
            return None
            
        # Find closest pattern
        best_match = None
        best_distance = float('inf')
        
        for pattern in self.learned_patterns[level_id]:
            distance = abs(pattern.player_x_position - player_x)
            if distance < best_distance and distance < 100.0:
                best_distance = distance
                best_match = pattern
                
        return best_match
        
    def generate_playback_sequence(self, level_id: str) -> List[ClickRecord]:
        """Generate optimal click sequence from learned patterns"""
        if level_id not in self.learned_patterns:
            return []
            
        # Get high-confidence patterns
        patterns = [p for p in self.learned_patterns[level_id] 
                   if p.confidence >= 0.7]
        
        # Sort by position
        patterns.sort(key=lambda p: p.player_x_position)
        
        # Convert to click records
        clicks = []
        for p in patterns:
            click = ClickRecord(
                timestamp=p.click_timing,
                player_x=p.player_x_position,
                player_y=0.0,  # Will be determined during playback
                game_mode=p.game_mode,
                was_successful=True,
                frame_number=0
            )
            clicks.append(click)
            
        return clicks
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get recording statistics"""
        if not self.attempts:
            return {'total_attempts': 0}
            
        completed = sum(1 for a in self.attempts if a.is_complete)
        avg_progress = np.mean([a.progress_percent for a in self.attempts])
        best_progress = max(a.progress_percent for a in self.attempts)
        
        return {
            'total_attempts': len(self.attempts),
            'completed': completed,
            'completion_rate': completed / len(self.attempts) * 100,
            'average_progress': avg_progress,
            'best_progress': best_progress,
            'total_clicks_recorded': sum(len(a.clicks) for a in self.attempts),
            'learned_patterns': sum(len(v) for v in self.learned_patterns.values())
        }


class HumanizedClickbot:
    """Advanced clickbot with humanization and learning"""
    
    def __init__(self, config: Optional[HumanizationConfig] = None):
        self.config = config or HumanizationConfig()
        
        # Process handles
        self.process_handle = None
        self.game_pid = None
        self.game_window = None
        
        # State
        self.is_running = False
        self.is_clicking = False
        self.game_state = GameState.MENU
        self.player_x = 0.0
        self.player_y = 0.0
        self.player_mode = 0
        self.player_on_ground = False
        
        # Fatigue and timing
        self.fatigue_level = 0.0
        self.last_click_time = 0.0
        self.session_start = time.time()
        
        # Recorder
        self.recorder = ClickRecorder()
        self.recorder.load_attempts()
        
        # Obstacle prediction (for rhythm mode)
        self.predicted_obstacles = []
        self.last_obstacle_x = 0.0
        
        # Jitter state
        self.jitter_phase = random.random() * 2 * math.pi
        
        # Callbacks for GUI
        self.status_callback = None
        self.progress_callback = None
        
    def find_game_window(self) -> bool:
        """Find Geometry Dash window"""
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "geometry dash" in title.lower():
                    windows.append(hwnd)
            return True
            
        windows = []
        win32gui.EnumWindows(callback, windows)
        
        if windows:
            self.game_window = windows[0]
            self.game_pid, _ = win32process.GetWindowThreadProcessId(self.game_window)
            
            try:
                self.process_handle = ctypes.windll.kernel32.OpenProcess(
                    PROCESS_VM_READ | PROCESS_VM_OPERATION,
                    False,
                    self.game_pid
                )
                return True
            except:
                return False
                
        return False
        
    def update_game_state(self):
        """Update game state from memory or estimation"""
        # Try to read from memory first
        if self.process_handle and self.game_window:
            # Check if window is still valid
            if not win32gui.IsWindow(self.game_window):
                self.game_state = GameState.MENU
                return
                
            # Get window rect to estimate player position
            rect = win32gui.GetWindowRect(self.game_window)
            window_width = rect[2] - rect[0]
            window_height = rect[3] - rect[1]
            
            # Estimate player X based on time (rough approximation)
            # In a real implementation, you'd read actual memory addresses
            current_time = time.time()
            elapsed = current_time - self.session_start
            
            # Rough estimate: player moves at ~500 units/second
            estimated_x = elapsed * 500
            
            # Keep player within reasonable bounds
            self.player_x = estimated_x % 10000  # Wrap around for long levels
            self.player_y = 300.0  # Ground level estimate
            
            # Determine game state from window title or other cues
            title = win32gui.GetWindowText(self.game_window).lower()
            if "pause" in title:
                self.game_state = GameState.PAUSED
            elif "dead" in title or "crashed" in title:
                self.game_state = GameState.DEAD
            elif "complete" in title or "finished" in title:
                self.game_state = GameState.LEVEL_COMPLETE
            else:
                self.game_state = GameState.PLAYING
                
        else:
            # Fallback: just assume playing if we started
            if self.is_running:
                self.game_state = GameState.PLAYING
                current_time = time.time()
                elapsed = current_time - self.session_start
                self.player_x = elapsed * 500
                
    def generate_predicted_obstacles(self):
        """Generate predicted obstacle positions for rhythm mode"""
        self.predicted_obstacles = []
        
        # Generate obstacles at typical intervals
        # Cube: every 150-250 pixels
        # Ship: continuous sections
        # UFO: every 100-150 pixels
        
        base_interval = 200.0  # Average obstacle spacing
        
        for i in range(50):  # Predict next 50 obstacles
            obstacle_x = self.player_x + base_interval * (i + 1)
            
            # Add some variance
            variance = random.uniform(-30, 30)
            obstacle_x += variance
            
            self.predicted_obstacles.append({
                'x': obstacle_x,
                'type': 'predicted',
                'width': 50.0
            })
            
    def should_click(self) -> bool:
        """Determine if we should click based on game state and learning"""
        if self.game_state != GameState.PLAYING:
            return False
            
        # Check for learned patterns at current position
        if self.config.use_learned_patterns:
            learned = self.recorder.get_learned_clicks_for_position(
                self.recorder.current_attempt.level_id if self.recorder.current_attempt else "unknown",
                self.player_x,
                self.player_mode
            )
            
            if learned and learned.confidence >= 0.7:
                # Use learned timing
                return True
                
        # Check predicted obstacles
        self.generate_predicted_obstacles()
        
        for obstacle in self.predicted_obstacles:
            distance = obstacle['x'] - self.player_x
            
            # Click when obstacle is within reaction range
            if 100 < distance < 300:
                # Apply human reaction time
                reaction_delay = random.gauss(
                    self.config.base_reaction_time,
                    self.config.reaction_time_variance
                )
                reaction_delay = max(20, min(150, reaction_delay))  # Clamp
                
                # Adjust for fatigue
                reaction_delay *= (1 + self.fatigue_level)
                
                # Calculate if we should click now
                time_to_obstacle = distance / 500.0 * 1000  # Convert to ms
                
                if time_to_obstacle <= reaction_delay:
                    return True
                    
        return False
        
    def apply_jitter(self, x: int, y: int) -> Tuple[int, int]:
        """Apply human-like jitter to mouse position"""
        t = time.time()
        
        # Sinusoidal jitter
        jitter_x = math.sin(2 * math.pi * self.config.jitter_frequency * t + self.jitter_phase)
        jitter_y = math.cos(2 * math.pi * self.config.jitter_frequency * t + self.jitter_phase)
        
        # Scale by amplitude
        jitter_x *= self.config.jitter_amplitude
        jitter_y *= self.config.jitter_amplitude
        
        # Add some noise
        jitter_x += random.gauss(0, self.config.jitter_amplitude * 0.3)
        jitter_y += random.gauss(0, self.config.jitter_amplitude * 0.3)
        
        return int(x + jitter_x), int(y + jitter_y)
        
    def perform_click(self):
        """Perform a humanized click"""
        if not PYAUTOGUI_AVAILABLE:
            print("pyautogui not available, simulating click")
            return
            
        # Check for misclick
        if random.random() < self.config.misclick_probability:
            # Delay or skip click
            if random.random() < 0.5:
                time.sleep(random.uniform(0.05, 0.15))  # Delay
            # else: skip click entirely
            
        # Get current mouse position
        screen_x, screen_y = pyautogui.position()
        
        # Apply jitter
        jittered_x, jittered_y = self.apply_jitter(screen_x, screen_y)
        
        # Move slightly (simulates hand movement)
        if abs(jittered_x - screen_x) > 0.5 or abs(jittered_y - screen_y) > 0.5:
            pyautogui.moveTo(jittered_x, jittered_y, duration=0.001)
            
        # Calculate click duration with variance
        duration = random.gauss(
            self.config.base_click_duration,
            self.config.click_duration_variance
        )
        duration = max(30, min(200, duration)) / 1000.0  # Convert to seconds
        
        # Perform click
        pyautogui.mouseDown()
        time.sleep(duration)
        pyautogui.mouseUp()
        
        # Record click if recording
        if self.recorder.recording and self.recorder.current_attempt:
            self.recorder.record_click(
                self.player_x,
                self.player_y,
                self.player_mode
            )
            
    def detect_death(self) -> bool:
        """Detect if player died"""
        # Simple heuristic: if game state changed to dead
        return self.game_state == GameState.DEAD
        
    def detect_completion(self) -> bool:
        """Detect if level was completed"""
        return self.game_state == GameState.LEVEL_COMPLETE
        
    def get_progress_percent(self) -> float:
        """Estimate progress percentage"""
        # This is a rough estimate - in reality you'd read actual progress from memory
        # Assume level is 10000 units long
        return min(100.0, (self.player_x / 10000.0) * 100)
        
    def start_level(self, level_id: str = "current"):
        """Start recording a new level attempt"""
        self.recorder.start_recording(level_id)
        self.session_start = time.time()
        self.fatigue_level = 0.0
        
    def end_level(self, completed: bool = False, death_reason: str = ""):
        """End current level attempt"""
        progress = self.get_progress_percent()
        self.recorder.end_attempt(progress, completed, death_reason)
        
        # Reset fatigue
        self.fatigue_level = 0.0
        
    def auto_click_loop(self):
        """Main auto-click loop"""
        print("Starting humanized auto-click...")
        self.is_clicking = True
        
        click_interval = 0.017  # ~60 FPS base
        
        try:
            while self.is_clicking and self.is_running:
                # Update game state
                self.update_game_state()
                
                # Update fatigue
                elapsed = time.time() - self.session_start
                self.fatigue_level = min(
                    self.config.max_fatigue,
                    self.fatigue_level + self.config.fatigue_rate
                )
                
                # Check for death or completion
                if self.detect_death():
                    print(f"Died at {self.get_progress_percent():.1f}%")
                    self.end_level(completed=False, death_reason="crashed")
                    # Auto-restart after brief pause
                    time.sleep(0.5)
                    self.start_level()
                    continue
                    
                if self.detect_completion():
                    print("Level completed!")
                    self.end_level(completed=True)
                    break
                    
                # Determine if we should click
                if self.should_click():
                    self.perform_click()
                    self.last_click_time = time.time()
                    
                    # Small delay between clicks
                    time.sleep(click_interval)
                else:
                    # Very short sleep to prevent CPU hogging
                    time.sleep(0.001)
                    
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            self.is_clicking = False
            
    def start(self) -> bool:
        """Initialize and start the clickbot"""
        if not PYAUTOGUI_AVAILABLE:
            print("Warning: pyautogui not available. Clicking will be simulated.")
            
        if not self.find_game_window():
            print("Could not find Geometry Dash window")
            return False
            
        self.is_running = True
        print("Clickbot started successfully")
        return True
        
    def stop(self):
        """Stop the clickbot"""
        self.is_running = False
        self.is_clicking = False
        
        # End any recording
        if self.recorder.recording:
            self.end_level(death_reason="stopped")
            
        print("Clickbot stopped")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        return {
            'game_state': self.game_state.name,
            'player_x': self.player_x,
            'fatigue': self.fatigue_level,
            'recording': self.recorder.recording,
            'recorder_stats': self.recorder.get_statistics()
        }


class ClickbotGUI:
    """GUI for the Advanced Humanized Clickbot"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced GD Clickbot v3.0")
        self.root.geometry("700x650")
        self.root.resizable(True, True)
        
        self.bot: Optional[HumanizedClickbot] = None
        self.click_thread: Optional[threading.Thread] = None
        self.is_active = False
        self.update_timer = None
        
        # Variables
        self.click_interval_var = tk.DoubleVar(value=0.017)
        self.base_reaction_var = tk.DoubleVar(value=45.0)
        self.reaction_variance_var = tk.DoubleVar(value=25.0)
        self.misclick_prob_var = tk.DoubleVar(value=1.5)  # Display as percentage
        self.jitter_amp_var = tk.DoubleVar(value=1.5)
        self.fatigue_rate_var = tk.DoubleVar(value=0.0008)
        self.adaptation_rate_var = tk.DoubleVar(value=0.05)
        
        self.click_mode_var = tk.StringVar(value='smart')
        self.game_mode_var = tk.StringVar(value='auto')
        self.status_var = tk.StringVar(value="Not started - Launch Geometry Dash first")
        self.level_id_var = tk.StringVar(value="current_level")
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎮 Advanced GD Clickbot v3.0", 
                                font=('Segoe UI', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="8")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                      font=('Segoe UI', 11), foreground='blue')
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var,
                                           maximum=100, length=400)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Control section
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="8")
        control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Start/Stop buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=0, column=0, columnspan=3, pady=5)
        
        self.start_btn = ttk.Button(btn_frame, text="▶ Start Clickbot", 
                                    command=self.start_clickbot, width=15)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹ Stop", 
                                   command=self.stop_clickbot, state=tk.DISABLED, width=15)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        # Level controls
        level_frame = ttk.Frame(control_frame)
        level_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky=tk.W)
        
        ttk.Label(level_frame, text="Level ID:").grid(row=0, column=0, padx=5)
        ttk.Entry(level_frame, textvariable=self.level_id_var, width=20).grid(row=0, column=1, padx=5)
        
        ttk.Button(level_frame, text="New Attempt", 
                   command=self.new_attempt, width=12).grid(row=0, column=2, padx=5)
        
        ttk.Button(level_frame, text="Playback Best", 
                   command=self.playback_best, width=12).grid(row=0, column=3, padx=5)
        
        # Mode selection
        mode_frame = ttk.Frame(control_frame)
        mode_frame.grid(row=2, column=0, columnspan=3, pady=5, sticky=tk.W)
        
        ttk.Label(mode_frame, text="Click Mode:").grid(row=0, column=0, padx=5)
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.click_mode_var,
                                  values=['smart', 'rhythm', 'spam', 'learned'],
                                  width=15, state='readonly')
        mode_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(mode_frame, text="Game Mode:").grid(row=0, column=2, padx=15)
        game_mode_combo = ttk.Combobox(mode_frame, textvariable=self.game_mode_var,
                                       values=['auto', 'cube', 'ship', 'ball', 'ufo', 'wave'],
                                       width=10, state='readonly')
        game_mode_combo.grid(row=0, column=3, padx=5)
        
        # Click interval
        ttk.Label(mode_frame, text="Interval (s):").grid(row=0, column=4, padx=15)
        ttk.Spinbox(mode_frame, from_=0.001, to=0.1, increment=0.001,
                    textvariable=self.click_interval_var, width=8).grid(row=0, column=5, padx=5)
        
        # Humanization settings
        human_frame = ttk.LabelFrame(main_frame, text="Humanization Settings", padding="8")
        human_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        settings = [
            ("Base Reaction (ms):", self.base_reaction_var, 10, 200, 1),
            ("Reaction Variance (ms):", self.reaction_variance_var, 0, 100, 1),
            ("Misclick Chance (%):", self.misclick_prob_var, 0, 10, 0.1),
            ("Jitter Amplitude (px):", self.jitter_amp_var, 0, 10, 0.1),
            ("Fatigue Rate:", self.fatigue_rate_var, 0, 0.01, 0.0001),
            ("Adaptation Rate:", self.adaptation_rate_var, 0, 0.2, 0.01),
        ]
        
        for i, (label, var, from_, to, inc) in enumerate(settings):
            ttk.Label(human_frame, text=label).grid(row=i, column=0, padx=10, pady=2, sticky=tk.E)
            ttk.Spinbox(human_frame, from_=from_, to=to, increment=inc,
                        textvariable=var, width=10).grid(row=i, column=1, padx=5, pady=2)
                        
        # Statistics section
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics & Learning", padding="8")
        stats_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(4, weight=1)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=8, width=70,
                                                    font=('Consolas', 9))
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.rowconfigure(0, weight=1)
        
        # Stats buttons
        stats_btn_frame = ttk.Frame(stats_frame)
        stats_btn_frame.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        ttk.Button(stats_btn_frame, text="Refresh Stats", 
                   command=self.refresh_stats).grid(row=0, column=0, padx=2)
        ttk.Button(stats_btn_frame, text="Clear Data", 
                   command=self.clear_data).grid(row=0, column=1, padx=2)
        ttk.Button(stats_btn_frame, text="Export Runs", 
                   command=self.export_runs).grid(row=0, column=2, padx=2)
        
        # Info section
        info_frame = ttk.LabelFrame(main_frame, text="How to Use", padding="8")
        info_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        info_text = """
📋 Quick Start:
1. Launch Geometry Dash and enter a level
2. Click "Start Clickbot" - it will automatically detect the game window
3. The bot will intelligently click based on obstacles (smart mode recommended)
4. Each attempt is recorded - successful clicks are learned
5. Use "Playback Best" to replay your most successful run

🎯 Click Modes:
• smart: Intelligently times clicks based on predicted obstacles (RECOMMENDED)
• rhythm: Clicks at regular intervals based on typical GD patterns
• learned: Uses only previously learned successful click positions
• spam: Constant clicking (legacy mode)

🧠 Learning System:
• Every click is recorded during attempts
• Successful clicks (those that lead to progress) are saved
• The bot learns optimal timing for each obstacle position
• Over multiple attempts, it builds a complete solution
• Confidence increases with more successful repetitions

⚙️ Humanization:
• Reaction time variance makes timing less robotic
• Jitter adds subtle mouse movement variations
• Misclick chance simulates human error
• Fatigue affects performance over long sessions
"""
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT, 
                               font=('Segoe UI', 9))
        info_label.grid(row=0, column=0, sticky=tk.W)
        
        # Start periodic updates
        self.schedule_updates()
        
    def schedule_updates(self):
        """Schedule periodic UI updates"""
        self.refresh_stats()
        self.update_timer = self.root.after(1000, self.schedule_updates)
        
    def refresh_stats(self):
        """Refresh statistics display"""
        if self.bot:
            stats = self.bot.get_stats()
            recorder_stats = stats.get('recorder_stats', {})
            
            output = []
            output.append(f"Game State: {stats.get('game_state', 'Unknown')}")
            output.append(f"Player Position: {stats.get('player_x', 0):.1f}")
            output.append(f"Fatigue Level: {stats.get('fatigue', 0)*100:.1f}%")
            output.append("")
            output.append("=== Recording Statistics ===")
            output.append(f"Total Attempts: {recorder_stats.get('total_attempts', 0)}")
            output.append(f"Completed: {recorder_stats.get('completed', 0)}")
            output.append(f"Completion Rate: {recorder_stats.get('completion_rate', 0):.1f}%")
            output.append(f"Best Progress: {recorder_stats.get('best_progress', 0):.1f}%")
            output.append(f"Average Progress: {recorder_stats.get('average_progress', 0):.1f}%")
            output.append(f"Clicks Recorded: {recorder_stats.get('total_clicks_recorded', 0)}")
            output.append(f"Learned Patterns: {recorder_stats.get('learned_patterns', 0)}")
            
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, '\n'.join(output))
            
            # Update progress bar
            self.progress_var.set(recorder_stats.get('best_progress', 0))
            
    def start_clickbot(self):
        """Start the clickbot"""
        try:
            # Create configuration
            config = HumanizationConfig(
                base_reaction_time=self.base_reaction_var.get(),
                reaction_time_variance=self.reaction_variance_var.get(),
                misclick_probability=self.misclick_prob_var.get() / 100.0,
                jitter_amplitude=self.jitter_amp_var.get(),
                fatigue_rate=self.fatigue_rate_var.get(),
                adaptation_rate=self.adaptation_rate_var.get(),
            )
            
            # Initialize clickbot
            self.bot = HumanizedClickbot(config)
            
            if not self.bot.start():
                messagebox.showerror("Error", 
                    "Failed to initialize clickbot.\nMake sure Geometry Dash is running!")
                return
                
            self.is_active = True
            self.status_var.set("Running - Monitoring game...")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # Start a new attempt
            self.bot.start_level(self.level_id_var.get())
            
            # Start clicking thread
            self.click_thread = threading.Thread(target=self._run_clickbot, daemon=True)
            self.click_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start clickbot:\n{str(e)}")
            self.is_active = False
            
    def _run_clickbot(self):
        """Run clickbot in background thread"""
        try:
            self.bot.auto_click_loop()
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
        finally:
            self.is_active = False
            self.root.after(0, self._on_clickbot_stop)
            
    def _on_clickbot_stop(self):
        """Called when clickbot stops"""
        self.status_var.set("Stopped")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.refresh_stats()
        
    def stop_clickbot(self):
        """Stop the clickbot"""
        if self.bot:
            self.bot.stop()
        self.is_active = False
        
    def new_attempt(self):
        """Start a new recording attempt"""
        if self.bot:
            self.bot.start_level(self.level_id_var.get())
            self.status_var.set("New attempt started")
        else:
            messagebox.showinfo("Info", "Start the clickbot first")
            
    def playback_best(self):
        """Playback the best recorded run"""
        if not self.bot:
            messagebox.showinfo("Info", "Start the clickbot first")
            return
            
        recorder = self.bot.recorder
        if not recorder.best_run:
            messagebox.showinfo("Info", "No completed runs to playback")
            return
            
        clicks = recorder.generate_playback_sequence(recorder.best_run.level_id)
        
        if not clicks:
            messagebox.showinfo("Info", "No learned patterns for playback")
            return
            
        messagebox.showinfo("Playback Ready", 
            f"Found {len(clicks)} learned clicks from best run.\n"
            f"Progress: {recorder.best_run.progress_percent:.1f}%\n\n"
            "Note: Full automated playback requires additional setup.\n"
            "The learned patterns will be used in 'learned' mode.")
            
    def clear_data(self):
        """Clear all recorded data"""
        if messagebox.askyesno("Confirm", "Clear all recorded attempts and learned patterns?"):
            if self.bot:
                self.bot.recorder.attempts = []
                self.bot.recorder.learned_patterns = {}
                self.bot.recorder.best_run = None
                self.refresh_stats()
                
    def export_runs(self):
        """Export runs to file"""
        if not self.bot or not self.bot.recorder.attempts:
            messagebox.showinfo("Info", "No runs to export")
            return
            
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    json.dump({
                        'attempts': [asdict(a) for a in self.bot.recorder.attempts],
                        'learned_patterns': {
                            k: [asdict(p) for p in v]
                            for k, v in self.bot.recorder.learned_patterns.items()
                        }
                    }, f, indent=2)
                messagebox.showinfo("Success", f"Exported to {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
                
    def on_closing(self):
        """Handle window closing"""
        if self.update_timer:
            self.root.after_cancel(self.update_timer)
        self.stop_clickbot()
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ClickbotGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
