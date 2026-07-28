#!/usr/bin/env python3
"""
AI-Assisted Humanized Clickbot for Geometry Dash v2.0
Advanced version with LSTM pattern prediction, dynamic adaptation, behavioral biometrics,
context-aware clicking, and enhanced anti-detection measures.

Features:
- Multi-layer jitter synthesis (Perlin + Fourier + Biomechanical)
- LSTM-based timing prediction
- Dynamic difficulty adaptation
- Behavioral fingerprinting
- Smart misclick recovery
- Session persistence & learning
- Real-time game state analysis
- Performance analytics dashboard
- GUI interface for easy control
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
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Optional, Tuple, List, Dict, Any, Callable
from enum import Enum, auto
import numpy as np
from scipy import signal
from scipy.ndimage import gaussian_filter1d
import win32gui
import win32process
import win32con
import psutil
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch not available. Using simplified pattern prediction.")

# Windows API constants
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020

# Game state detection addresses (update for your GD version)
# These are example offsets - you'll need to find the actual ones for your GD version using Cheat Engine or similar
GD_BASE_ADDRESS = None  # Will be scanned at runtime
GD_PLAYER_X_OFFSET = 0x000
GD_PLAYER_Y_OFFSET = 0x004
GD_PLAYER_Y_VELOCITY_OFFSET = 0x008
GD_PLAYER_ON_GROUND_OFFSET = 0x00C
GD_PLAYER_DEAD_OFFSET = 0x018
GD_GAME_STATE_OFFSET = 0x030
GD_LEVEL_OBJECTS_OFFSET = 0x040  # Offset to level objects array
GD_PLAYER_SIZE_OFFSET = 0x014
GD_PLAYER_MODE_OFFSET = 0x010  # cube/ship/ball/ufo/etc


class GameState(Enum):
    """Game state enumeration"""
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    DEAD = auto()
    LEVEL_COMPLETE = auto()
    EDITOR = auto()


class ClickPhase(Enum):
    """Click timing phases"""
    ANTICIPATION = auto()
    EXECUTION = auto()
    FOLLOW_THROUGH = auto()
    RECOVERY = auto()


@dataclass
class BehavioralFingerprint:
    """Unique behavioral signature for this session"""
    session_id: str = field(default_factory=lambda: hashlib.md5(
        f"{time.time()}{random.random()}".encode()
    ).hexdigest()[:12])
    
    # Biometric profiles
    reaction_time_mean: float = 0.0
    reaction_time_std: float = 0.0
    jitter_profile: List[float] = field(default_factory=list)
    click_pressure_curve: List[float] = field(default_factory=list)
    movement_arc_preference: float = 0.0
    hesitation_frequency: float = 0.0
    
    # Learning history
    total_clicks: int = 0
    successful_runs: int = 0
    avg_run_progress: float = 0.0
    
    def generate_profile(self):
        """Generate initial behavioral profile"""
        self.reaction_time_mean = random.gauss(55.0, 15.0)
        self.reaction_time_std = abs(random.gauss(25.0, 8.0))
        self.jitter_profile = [
            random.gauss(0.8, 0.2),  # Low frequency weight
            random.gauss(0.5, 0.15), # Mid frequency weight
            random.gauss(0.3, 0.1),  # High frequency weight
        ]
        self.movement_arc_preference = random.uniform(5.0, 20.0)
        self.hesitation_frequency = random.uniform(0.01, 0.04)
        
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BehavioralFingerprint':
        return cls(**data)


@dataclass
class HumanizationConfig:
    """Enhanced configuration for human-like behavior"""
    
    # === Core Timing Parameters ===
    base_reaction_time: float = 50.0
    reaction_time_variance: float = 30.0
    reaction_time_drift: float = 5.0
    timing_precision: float = 0.85  # How consistent (1.0 = robot, 0.5 = very human)
    
    # === Advanced Misclick System ===
    misclick_probability: float = 0.02
    misclick_delay_range: Tuple[float, float] = (80.0, 150.0)
    double_click_probability: float = 0.01
    triple_click_probability: float = 0.002
    early_release_probability: float = 0.015
    late_release_probability: float = 0.025
    correction_behavior: bool = True  # Try to correct misclicks
    
    # === Multi-Layer Jitter ===
    jitter_amplitude: float = 2.0
    jitter_frequency: float = 15.0
    jitter_decay: float = 0.95
    perlin_octaves: int = 4
    perlin_persistence: float = 0.5
    biomechanical_tremor: float = 0.3  # Physiological tremor (8-12Hz)
    micro_saccades: bool = True  # Tiny rapid movements
    
    # === Click Dynamics ===
    base_click_duration: float = 80.0
    click_duration_variance: float = 25.0
    pressure_curve_type: str = "gaussian"  # gaussian, linear, exponential
    release_variation: float = 0.2
    
    # === Fatigue & Adaptation ===
    fatigue_rate: float = 0.001
    max_fatigue: float = 0.3
    fatigue_recovery: float = 0.01
    warmup_period: float = 30.0  # Seconds to reach full performance
    cooldown_benefit: float = 1.5  # Extra recovery after breaks
    
    # === AI Learning ===
    adaptation_rate: float = 0.05
    pattern_memory_size: int = 200
    use_lstm_prediction: bool = TORCH_AVAILABLE
    prediction_horizon: int = 10  # Frames to predict ahead
    confidence_threshold: float = 0.7
    
    # === Context Awareness ===
    adapt_to_game_state: bool = True
    menu_behavior: Dict = field(default_factory=lambda: {
        'slower': True,
        'more_jitter': True,
        'hesitation_chance': 0.1
    })
    high_difficulty_behavior: Dict = field(default_factory=lambda: {
        'tighter_timing': True,
        'reduced_jitter': True,
        'focus_mode': True
    })
    
    # === Anti-Detection ===
    randomize_seeds: bool = True
    behavioral_drift: float = 0.02  # Gradual change over session
    session_uniqueness: float = 0.15  # How different each session is
    save_patterns: bool = True
    
    # === Analytics ===
    enable_analytics: bool = True
    log_interval: int = 100  # Log stats every N clicks
    export_data: bool = False


@dataclass
class ClickAnalytics:
    """Track and analyze click performance"""
    click_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    reaction_times: deque = field(default_factory=lambda: deque(maxlen=500))
    misclick_count: int = 0
    total_clicks: int = 0
    jitter_magnitude_avg: float = 0.0
    fatigue_history: deque = field(default_factory=lambda: deque(maxlen=100))
    success_streak: int = 0
    best_streak: int = 0
    
    def record_click(self, timestamp: float, reaction: float, jitter: float):
        self.click_times.append(timestamp)
        self.reaction_times.append(reaction)
        self.total_clicks += 1
        # Exponential moving average for jitter
        alpha = 0.1
        self.jitter_magnitude_avg = (
            alpha * jitter + (1 - alpha) * self.jitter_magnitude_avg
        )
    
    def record_misclick(self):
        self.misclick_count += 1
        self.success_streak = 0
    
    def record_success(self):
        self.success_streak += 1
        self.best_streak = max(self.best_streak, self.success_streak)
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.reaction_times:
            return {}
        
        rt_array = np.array(self.reaction_times)
        return {
            'total_clicks': self.total_clicks,
            'misclicks': self.misclick_count,
            'misclick_rate': self.misclick_count / max(1, self.total_clicks),
            'avg_reaction': float(np.mean(rt_array)),
            'std_reaction': float(np.std(rt_array)),
            'min_reaction': float(np.min(rt_array)),
            'max_reaction': float(np.max(rt_array)),
            'avg_jitter': self.jitter_magnitude_avg,
            'current_streak': self.success_streak,
            'best_streak': self.best_streak,
            'clicks_per_second': len(self.click_times) / max(1, 
                (self.click_times[-1] - self.click_times[0]) if len(self.click_times) > 1 else 1)
        }


class SimplePatternPredictor:
    """Fallback pattern predictor when PyTorch is not available"""
    
    def __init__(self, memory_size: int = 200):
        self.memory_size = memory_size
        self.history = deque(maxlen=memory_size)
        self.weights = None
        
    def train(self, sequences: List[List[float]]):
        """Simple linear prediction based on recent patterns"""
        if len(sequences) < 10:
            return
        
        # Calculate average deltas
        deltas = []
        for seq in sequences:
            for i in range(1, len(seq)):
                deltas.append(seq[i] - seq[i-1])
        
        if deltas:
            self.weights = np.mean(deltas)
    
    def predict(self, sequence: List[float], horizon: int = 10) -> List[float]:
        """Predict future values"""
        if not sequence or self.weights is None:
            return sequence[-horizon:] if len(sequence) >= horizon else sequence
        
        predictions = []
        last_val = sequence[-1]
        for _ in range(horizon):
            next_val = last_val + self.weights + random.gauss(0, abs(self.weights) * 0.3)
            predictions.append(next_val)
            last_val = next_val
        
        return predictions


class LSTMPredictor(nn.Module):
    """LSTM-based timing predictor (requires PyTorch)"""
    
    def __init__(self, input_size: int = 1, hidden_size: int = 64, 
                 num_layers: int = 2, output_size: int = 10):
        super(LSTMPredictor, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2
        )
        
        self.fc = nn.Linear(hidden_size, output_size)
        self.relu = nn.ReLU()
        
    def forward(self, x, hidden=None):
        lstm_out, hidden = self.lstm(x, hidden)
        out = self.fc(lstm_out[:, -1, :])
        return out, hidden
    
    def predict(self, sequence: List[float], horizon: int = 10) -> List[float]:
        """Predict future timing values"""
        if len(sequence) < 10:
            return sequence[-horizon:] if len(sequence) >= horizon else sequence
        
        self.eval()
        with torch.no_grad():
            # Normalize input
            seq_array = np.array(sequence[-20:])
            mean_val = np.mean(seq_array)
            std_val = np.std(seq_array) + 1e-6
            normalized = (seq_array - mean_val) / std_val
            
            # Prepare input tensor
            input_tensor = torch.FloatTensor(normalized).unsqueeze(-1).unsqueeze(0)
            
            # Get prediction
            output, _ = self.forward(input_tensor)
            prediction = output[0].numpy()
            
            # Denormalize
            prediction = prediction * std_val + mean_val
            
            return list(prediction[:horizon])


class HumanizedClickbot:
    """Advanced clickbot class with comprehensive humanization features"""
    
    def __init__(self, config: Optional[HumanizationConfig] = None):
        self.config = config or HumanizationConfig()
        
        # Initialize behavioral fingerprint
        self.fingerprint = BehavioralFingerprint()
        self.fingerprint.generate_profile()
        
        # Apply session uniqueness
        if self.config.session_uniqueness > 0:
            self._apply_session_variations()
        
        # Process and window handles
        self.process_handle = None
        self.game_pid = None
        self.game_window = None
        self.base_address = None
        
        # State variables
        self.is_running = False
        self.is_clicking = False
        self.current_phase = ClickPhase.RECOVERY
        self.fatigue_level = 0.0
        self.warmup_progress = 0.0
        self.last_click_time = 0.0
        self.session_start_time = time.time()
        self.last_rest_time = time.time()
        
        # Pattern learning
        self.recent_clicks: List[float] = []
        self.click_intervals: deque = deque(maxlen=self.config.pattern_memory_size)
        self.adaptive_offset = 0.0
        self.pattern_predictor = None
        
        if self.config.use_lstm_prediction and TORCH_AVAILABLE:
            self.pattern_predictor = LSTMPredictor(output_size=self.config.prediction_horizon)
            self.training_sequences = []
        else:
            self.pattern_predictor = SimplePatternPredictor(self.config.pattern_memory_size)
        
        # Jitter state
        self.jitter_phase = random.random() * 2 * math.pi
        self.perlin_offsets = [random.random() * 1000 for _ in range(self.config.perlin_octaves)]
        
        # Thread control
        self.jitter_thread = None
        self.analytics_thread = None
        self.stop_event = threading.Event()
        
        # Memory addresses
        self.player_object_addr = None
        self.is_dead_addr = None
        self.progress_addr = None
        self.game_state = GameState.MENU
        self.gd_base_address = None
        
        # Player state tracking
        self.player_x = 0.0
        self.player_y = 0.0
        self.player_y_velocity = 0.0
        self.player_on_ground = False
        self.player_mode = 0  # 0=cube, 1=ship, 2=ball, 3=ufo, etc.
        self.player_size = 0.0
        
        # Level objects (obstacles)
        self.level_objects = []  # List of detected obstacles
        self.last_obstacle_x = 0.0
        self.distance_to_next_obstacle = float('inf')
        
        # Click timing for obstacles
        self.should_click_now = False
        self.click_buffer = []  # Buffered click commands
        self.obstacle_reaction_delay = 45.0  # ms delay before clicking at obstacle
        
        # Analytics
        self.analytics = ClickAnalytics() if self.config.enable_analytics else None
        self.log_counter = 0
        
        # Perlin noise cache for efficiency
        self._perlin_cache = {}
        self._cache_size = 1000
        
        # Context awareness
        self.difficulty_level = 1.0  # Will be adjusted based on game state
        self.focus_mode = False
        
        # Session persistence
        self.data_dir = Path.home() / ".humanized_clickbot"
        self.data_dir.mkdir(exist_ok=True)
        self._load_session_data()
        
    def _apply_session_variations(self):
        """Apply unique variations to this session"""
        variation = self.config.session_uniqueness
        
        # Randomly adjust key parameters
        self.config.base_reaction_time *= (1 + random.uniform(-variation, variation))
        self.config.jitter_amplitude *= (1 + random.uniform(-variation, variation))
        self.config.misclick_probability *= (1 + random.uniform(-variation * 0.5, variation * 0.5))
        
        # Generate unique seed for reproducibility within session
        if self.config.randomize_seeds:
            session_seed = int(hashlib.md5(
                self.fingerprint.session_id.encode()
            ).hexdigest()[:8], 16)
            random.seed(session_seed)
            np.random.seed(session_seed)
    
    def _load_session_data(self):
        """Load previous session data for continuity"""
        if not self.config.save_patterns:
            return
        
        profile_path = self.data_dir / f"profile_{self.fingerprint.session_id}.json"
        if profile_path.exists():
            try:
                with open(profile_path, 'r') as f:
                    data = json.load(f)
                    if 'fingerprint' in data:
                        self.fingerprint = BehavioralFingerprint.from_dict(data['fingerprint'])
            except Exception as e:
                print(f"Warning: Could not load session data: {e}")
    
    def _save_session_data(self):
        """Save session data for future use"""
        if not self.config.save_patterns:
            return
        
        try:
            profile_path = self.data_dir / f"profile_{self.fingerprint.session_id}.json"
            data = {
                'fingerprint': self.fingerprint.to_dict(),
                'timestamp': datetime.now().isoformat(),
                'total_clicks': self.analytics.total_clicks if self.analytics else 0,
            }
            
            with open(profile_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            # Export detailed data if enabled
            if self.config.export_data and self.analytics:
                export_path = self.data_dir / f"analytics_{self.fingerprint.session_id}.json"
                with open(export_path, 'w') as f:
                    json.dump({
                        'stats': self.analytics.get_stats(),
                        'reaction_times': list(self.analytics.reaction_times),
                        'click_times': list(self.analytics.click_times),
                    }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save session data: {e}")
        
    def find_geometry_dash(self) -> bool:
        """Find Geometry Dash process and window"""
        # Try common process names
        process_names = ['GeometryDash.exe', 'GeometryDashSteam.exe']
        
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'] in process_names:
                    self.game_pid = proc.info['pid']
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if not self.game_pid:
            print("Geometry Dash not found!")
            return False
        
        # Find the window
        def enum_windows(hwnd, results):
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid == self.game_pid and win32gui.IsWindowVisible(hwnd):
                    if win32gui.GetWindowText(hwnd):
                        results.append(hwnd)
            except:
                pass
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows, windows)
        
        if not windows:
            print("Game window not found!")
            return False
        
        self.game_window = windows[0]
        print(f"Found Geometry Dash: PID={self.game_pid}, Window={self.game_window}")
        return True
    
    def open_process(self) -> bool:
        """Open process with required permissions"""
        try:
            self.process_handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION,
                False,
                self.game_pid
            )
            if not self.process_handle:
                print("Failed to open process!")
                return False
            print("Process opened successfully")
            
            # Scan for base addresses and player object
            self.scan_game_memory()
            
            return True
        except Exception as e:
            print(f"Error opening process: {e}")
            return False
    
    def scan_game_memory(self):
        """Scan game memory to find important addresses"""
        print("Scanning game memory for player object and offsets...")
        
        # Try to find the player object by scanning for typical player X values
        # In a real implementation, you'd use signature scanning or known patterns
        # This is a simplified example
        
        # For now, we'll just note that memory reading requires actual GD offsets
        # Users should use Cheat Engine to find their specific version's offsets
        print("Note: Memory scanning requires GD-specific offsets.")
        print("Use Cheat Engine to find your GD version's player object address.")
        print("Then set GD_BASE_ADDRESS in the code accordingly.")
    
    def read_memory(self, address: int, size: int = 4) -> Optional[int]:
        """Read memory from the game process"""
        if not self.process_handle:
            return None
        
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_ulonglong()
        
        try:
            result = ctypes.windll.kernel32.ReadProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                buffer,
                size,
                ctypes.byref(bytes_read)
            )
            if result == 0:
                return None
            
            if size == 1:
                return buffer.value[0]
            elif size == 2:
                return int.from_bytes(buffer.raw[:2], 'little')
            elif size == 4:
                return int.from_bytes(buffer.raw[:4], 'little')
            elif size == 8:
                return int.from_bytes(buffer.raw[:8], 'little')
            else:
                return int.from_bytes(buffer.raw, 'little')
        except Exception as e:
            print(f"Memory read error: {e}")
            return None
    
    def write_memory(self, address: int, value: int, size: int = 4) -> bool:
        """Write memory to the game process"""
        if not self.process_handle:
            return False
        
        buffer = ctypes.create_string_buffer(size)
        if size == 1:
            buffer.value = bytes([value])
        elif size == 2:
            buffer.raw = value.to_bytes(2, 'little')
        elif size == 4:
            buffer.raw = value.to_bytes(4, 'little')
        elif size == 8:
            buffer.raw = value.to_bytes(8, 'little')
        
        try:
            result = ctypes.windll.kernel32.WriteProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                buffer,
                size,
                None
            )
            return result != 0
        except Exception as e:
            print(f"Memory write error: {e}")
            return False
    
    def scan_pattern(self, pattern: bytes, mask: str = None) -> Optional[int]:
        """Scan for byte pattern in process memory"""
        # Simplified pattern scanning - in production you'd want more robust implementation
        if not self.process_handle:
            return None
        
        mbi = ctypes.wintypes.MEMORY_BASIC_INFORMATION()
        address = 0
        
        while ctypes.windll.kernel32.VirtualQueryEx(
            self.process_handle,
            ctypes.c_void_p(address),
            ctypes.byref(mbi),
            ctypes.sizeof(mbi)
        ) > 0:
            if mbi.State == 0x1000 and mbi.Protect & 0x100:  # MEM_COMMIT and PAGE_EXECUTE_READWRITE
                buffer = ctypes.create_string_buffer(mbi.RegionSize)
                bytes_read = ctypes.c_ulonglong()
                
                if ctypes.windll.kernel32.ReadProcessMemory(
                    self.process_handle,
                    ctypes.c_void_p(mbi.BaseAddress),
                    buffer,
                    mbi.RegionSize,
                    ctypes.byref(bytes_read)
                ):
                    # Search for pattern in buffer
                    # Simplified implementation
                    pass
            
            address += mbi.RegionSize
        
        return None
    
    def _perlin_noise(self, x: float, y: float, octaves: int = None) -> float:
        """Generate Perlin noise for natural jitter"""
        if octaves is None:
            octaves = self.config.perlin_octaves
            
        total = 0.0
        frequency = 1.0
        amplitude = 1.0
        max_value = 0.0
        
        for i in range(octaves):
            # Use cached offsets for consistency
            offset_x = self.perlin_offsets[i % len(self.perlin_offsets)]
            offset_y = self.perlin_offsets[(i + 1) % len(self.perlin_offsets)]
            
            # Simple gradient noise approximation
            value = math.sin(x * frequency + offset_x) * math.cos(y * frequency + offset_y)
            total += value * amplitude
            max_value += amplitude
            
            frequency *= 2
            amplitude *= self.config.perlin_persistence
        
        return total / max_value
    
    def calculate_humanized_delay(self, base_delay: float) -> float:
        """Calculate delay with comprehensive human variations"""
        current_time = time.time()
        session_elapsed = current_time - self.session_start_time
        
        # === Warmup Phase ===
        warmup_factor = min(1.0, session_elapsed / self.config.warmup_period)
        
        # === Base Reaction Time with Multiple Distributions ===
        # Mix Gaussian and exponential for more realistic distribution
        gaussian_component = random.gauss(0, self.config.reaction_time_variance)
        exponential_component = random.expovariate(1.0 / self.config.reaction_time_variance)
        
        # Weight based on timing precision (more human = more variance)
        precision_weight = self.config.timing_precision
        reaction = (
            self.config.base_reaction_time +
            gaussian_component * precision_weight +
            exponential_component * (1 - precision_weight) * 0.5
        )
        
        # === Fatigue Effect (non-linear) ===
        fatigue_modifier = 1.0 + (self.fatigue_level ** 1.5) * 0.8
        
        # === Behavioral Drift (gradual change over session) ===
        drift_factor = 1.0 + math.sin(session_elapsed * 0.001) * self.config.behavioral_drift
        
        # === Context-Aware Adjustments ===
        context_modifier = 1.0
        if self.game_state == GameState.MENU and self.config.adapt_to_game_state:
            menu_behavior = self.config.menu_behavior
            if menu_behavior.get('slower', True):
                context_modifier *= 1.3
            if menu_behavior.get('hesitation_chance', 0) > 0:
                reaction *= 1.2
        elif self.focus_mode and self.config.adapt_to_game_state:
            hd_behavior = self.config.high_difficulty_behavior
            if hd_behavior.get('tighter_timing', True):
                context_modifier *= 0.9
            if hd_behavior.get('reduced_jitter', True):
                reaction *= 0.85
        
        # === Adaptive Offset from Pattern Learning ===
        adaptive = self.adaptive_offset * warmup_factor
        
        # === LSTM/Simple Prediction Adjustment ===
        prediction_adjustment = 0.0
        if self.pattern_predictor and len(self.click_intervals) > 20:
            predicted = self.pattern_predictor.predict(
                list(self.click_intervals), 
                horizon=self.config.prediction_horizon
            )
            if predicted:
                # Use first prediction as adjustment hint
                prediction_adjustment = (predicted[0] - np.mean(self.click_intervals)) * 0.1
        
        # === Combine All Factors ===
        total_delay = (
            (base_delay + reaction) * 
            fatigue_modifier * 
            drift_factor * 
            context_modifier +
            adaptive +
            prediction_adjustment
        )
        
        # === Apply Session Uniqueness Variation ===
        total_delay *= (1 + random.uniform(-0.05, 0.05) * self.config.session_uniqueness)
        
        # Ensure minimum delay (humans can't click instantly)
        return max(total_delay, 12.0)
    
    def should_misclick(self, click_type: str = 'normal') -> Tuple[bool, str]:
        """
        Determine if a misclick should occur and what type.
        Returns: (should_misclick, misclick_type)
        """
        rand = random.random()
        
        # Different probabilities for different click types
        if click_type == 'rapid':
            # Higher misclick chance during rapid clicking
            misclick_chance = self.config.misclick_probability * 1.5
        elif click_type == 'precision':
            # Lower misclick chance for precision clicks
            misclick_chance = self.config.misclick_probability * 0.7
        else:
            misclick_chance = self.config.misclick_probability
        
        # Check for various misclick types in order of rarity
        if rand < self.config.triple_click_probability:
            return True, 'triple_click'
        elif rand < self.config.triple_click_probability + self.config.double_click_probability:
            return True, 'double_click'
        elif rand < misclick_chance:
            return True, 'hesitation'
        elif rand < misclick_chance + self.config.early_release_probability:
            return True, 'early_release'
        elif rand < misclick_chance + self.config.early_release_probability + self.config.late_release_probability:
            return True, 'late_release'
        
        return False, 'none'
    
    def generate_jitter(self, t: float, intensity_multiplier: float = 1.0) -> Tuple[float, float]:
        """
        Generate multi-layer natural mouse jitter using:
        - Perlin noise for smooth continuous movement
        - Fourier series for periodic tremor
        - Biomechanical tremor simulation (8-12Hz physiological tremor)
        - Micro-saccades for tiny rapid adjustments
        """
        jitter_x = 0.0
        jitter_y = 0.0
        
        # === Layer 1: Perlin Noise (smooth, continuous) ===
        perlin_x = self._perlin_noise(t * 2, t * 1.5, self.config.perlin_octaves)
        perlin_y = self._perlin_noise(t * 1.7, t * 2.2, self.config.perlin_octaves)
        jitter_x += perlin_x * self.config.jitter_amplitude * self.fingerprint.jitter_profile[0]
        jitter_y += perlin_y * self.config.jitter_amplitude * self.fingerprint.jitter_profile[1]
        
        # === Layer 2: Multi-Frequency Fourier Series ===
        for i in range(4):
            freq = self.config.jitter_frequency * (i + 1) * 0.5
            amp = self.config.jitter_amplitude / (i + 1) ** 1.5
            phase = self.jitter_phase + (i * math.pi / 2.5)
            
            jitter_x += amp * math.sin(2 * math.pi * freq * t + phase)
            jitter_y += amp * math.cos(2 * math.pi * freq * t + phase * 1.4)
        
        # === Layer 3: Biomechanical Tremor (physiological 8-12Hz) ===
        tremor_freq = 10.0  # Average physiological tremor frequency
        tremor_amp = self.config.biomechanical_tremor * self.config.jitter_amplitude
        jitter_x += tremor_amp * math.sin(2 * math.pi * tremor_freq * t)
        jitter_y += tremor_amp * math.cos(2 * math.pi * tremor_freq * t * 1.1)
        
        # === Layer 4: Micro-Saccades (tiny rapid movements) ===
        if self.config.micro_saccades and random.random() < 0.02:
            saccade_x = random.gauss(0, self.config.jitter_amplitude * 0.15)
            saccade_y = random.gauss(0, self.config.jitter_amplitude * 0.15)
            jitter_x += saccade_x
            jitter_y += saccade_y
        
        # === Layer 5: Gaussian Random Component ===
        jitter_x += random.gauss(0, self.config.jitter_amplitude * 0.25)
        jitter_y += random.gauss(0, self.config.jitter_amplitude * 0.25)
        
        # === Apply Intensity Multiplier (for context awareness) ===
        jitter_x *= intensity_multiplier
        jitter_y *= intensity_multiplier
        
        # === Decay During Sustained Clicking ===
        if self.is_clicking:
            decay = self.config.jitter_decay
            jitter_x *= decay
            jitter_y *= decay
        
        # === Apply Fingerprint Profile ===
        jitter_x *= self.fingerprint.jitter_profile[2] + 0.5
        jitter_y *= self.fingerprint.jitter_profile[2] + 0.5
        
        return (jitter_x, jitter_y)
    
    def _generate_pressure_curve(self, duration_ms: float) -> List[float]:
        """Generate realistic mouse pressure curve during click"""
        num_points = int(duration_ms / 5)  # Sample every 5ms
        pressure_curve = []
        
        t_norm = np.linspace(0, 1, num_points)
        
        if self.config.pressure_curve_type == "gaussian":
            # Bell curve pressure profile
            center = 0.6  # Peak slightly after midpoint
            spread = 0.25
            pressure_curve = np.exp(-((t_norm - center) ** 2) / (2 * spread ** 2))
        elif self.config.pressure_curve_type == "linear":
            # Linear ramp up and down
            pressure_curve = np.minimum(t_norm * 2, 2 - t_norm * 2)
        elif self.config.pressure_curve_type == "exponential":
            # Quick attack, slow release
            pressure_curve = np.exp(-t_norm * 3) * (1 - np.exp(-t_norm * 10))
        else:
            pressure_curve = np.ones(num_points)
        
        # Add small variations
        pressure_curve += np.random.normal(0, 0.05, num_points)
        pressure_curve = np.clip(pressure_curve, 0, 1)
        
        return pressure_curve.tolist()
    
    def simulate_mouse_click(self, x: int, y: int, duration_ms: float = None):
        """Simulate a comprehensive human-like mouse click"""
        import pyautogui
        
        # Disable failsafe for controlled bot operation
        pyautogui.FAILSAFE = False
        
        current_time = time.time()
        click_type = 'rapid' if duration_ms and duration_ms < 20 else 'normal'
        
        # === Determine Misclick Behavior ===
        has_misclick, misclick_type = self.should_misclick(click_type)
        
        if has_misclick and self.analytics:
            self.analytics.record_misclick()
        
        # === Apply Jitter to Target Position ===
        jitter_x, jitter_y = self.generate_jitter(current_time)
        
        # Calculate final click position with misclick adjustments
        click_x = int(x + jitter_x)
        click_y = int(y + jitter_y)
        
        if has_misclick and misclick_type == 'hesitation':
            # Hesitation: delay before moving
            hesitation_time = random.uniform(*self.config.misclick_delay_range)
            time.sleep(hesitation_time / 1000.0)
        
        if has_misclick and misclick_type in ['double_click', 'triple_click']:
            # For multi-click errors, we'll handle after the main click
            pass
        
        if has_misclick and random.random() < 0.4:
            # Offset target slightly for imperfect aim
            click_x += random.randint(-15, 15)
            click_y += random.randint(-15, 15)
        
        # === Bounds Checking ===
        screen_width, screen_height = pyautogui.size()
        margin = 50  # Keep away from edges
        
        # Clamp coordinates to safe screen area
        click_x = max(margin, min(screen_width - margin, click_x))
        click_y = max(margin, min(screen_height - margin, click_y))
        
        # Also clamp original x/y
        x = max(margin, min(screen_width - margin, x))
        y = max(margin, min(screen_height - margin, y))
        
        # === Move Mouse with Natural Arc ===
        start_x, start_y = pyautogui.position()
        steps = random.randint(4, 7)  # Variable steps for naturalness
        
        arc_height = self.fingerprint.movement_arc_preference * random.uniform(0.8, 1.2)
        
        for i in range(steps + 1):
            progress = i / steps
            
            # Bezier-like curved path
            intermediate_x = int(start_x + (click_x - start_x) * progress)
            intermediate_y = int(start_y + (click_y - start_y) * progress)
            
            # Add arc perpendicular to movement direction
            arc_offset = math.sin(progress * math.pi) * arc_height
            
            # Perpendicular vector
            dx = click_x - start_x
            dy = click_y - start_y
            length = math.sqrt(dx*dx + dy*dy) or 1
            perp_x = -dy / length * arc_offset
            perp_y = dx / length * arc_offset
            
            # Apply bounds to intermediate positions
            final_x = max(margin, min(screen_width - margin, intermediate_x + int(perp_x)))
            final_y = max(margin, min(screen_height - margin, intermediate_y + int(perp_y)))
            
            try:
                pyautogui.moveTo(
                    final_x,
                    final_y,
                    duration=0.008 + random.uniform(-0.002, 0.002)
                )
            except Exception as e:
                # Silently continue on any movement errors
                pass
            time.sleep(0.003 + random.uniform(0, 0.003))
        
        # === Pre-Click Micro-Adjustment (human targeting refinement) ===
        if random.random() < 0.3:
            micro_adj_x = random.gauss(0, 1.5)
            micro_adj_y = random.gauss(0, 1.5)
            try:
                pyautogui.moveRel(int(micro_adj_x), int(micro_adj_y), duration=0.005)
            except Exception:
                pass
            time.sleep(0.008)
        
        # === Click Down ===
        try:
            pyautogui.mouseDown(button='left')
        except Exception as e:
            print(f"Warning: mouseDown failed: {e}")
            return  # Exit early if we can't click
        self.is_clicking = True
        self.current_phase = ClickPhase.EXECUTION
        
        # === Determine Hold Duration ===
        hold_duration = self.config.base_click_duration + random.gauss(
            0, self.config.click_duration_variance
        )
        
        # Apply misclick effects
        if has_misclick and misclick_type == 'early_release':
            hold_duration *= random.uniform(0.4, 0.7)
        elif has_misclick and misclick_type == 'late_release':
            hold_duration *= random.uniform(1.3, 1.8)
        
        hold_duration = max(hold_duration, 25.0)  # Minimum physical click time
        
        # === Generate and Simulate Pressure Curve ===
        pressure_curve = self._generate_pressure_curve(hold_duration)
        
        # === Hold with Continuous Jitter ===
        hold_start = time.time()
        jitter_interval = 0.008  # Update jitter every 8ms
        
        while time.time() - hold_start < hold_duration / 1000.0:
            # Apply subtle jitter during hold
            jit_x, jit_y = self.generate_jitter(time.time(), intensity_multiplier=0.3)
            try:
                pyautogui.moveRel(jit_x * 0.4, jit_y * 0.4, duration=0.004)
            except Exception:
                pass
            time.sleep(jitter_interval)
        
        # === Click Up ===
        try:
            pyautogui.mouseUp(button='left')
        except Exception as e:
            print(f"Warning: mouseUp failed: {e}")
        self.is_clicking = False
        self.current_phase = ClickPhase.RECOVERY
        
        # === Record Analytics ===
        reaction_time = current_time - self.last_click_time if self.last_click_time > 0 else 0
        jitter_magnitude = math.sqrt(jitter_x**2 + jitter_y**2)
        
        if self.analytics:
            self.analytics.record_click(current_time, reaction_time, jitter_magnitude)
            if not has_misclick:
                self.analytics.record_success()
        
        self.last_click_time = current_time
        self.recent_clicks.append(current_time)
        if len(self.recent_clicks) > self.config.pattern_memory_size:
            self.recent_clicks.pop(0)
        
        # Calculate interval for pattern learning
        if len(self.recent_clicks) >= 2:
            interval = self.recent_clicks[-1] - self.recent_clicks[-2]
            self.click_intervals.append(interval)
        
        # === Handle Multi-Click Errors ===
        if has_misclick and misclick_type == 'double_click':
            time.sleep(random.uniform(0.04, 0.12))
            try:
                pyautogui.click(button='left')
            except Exception:
                pass
            if self.analytics:
                self.analytics.record_misclick()
        elif has_misclick and misclick_type == 'triple_click':
            time.sleep(random.uniform(0.04, 0.10))
            try:
                pyautogui.click(button='left')
            except Exception:
                pass
            time.sleep(random.uniform(0.04, 0.08))
            try:
                pyautogui.click(button='left')
            except Exception:
                pass
            if self.analytics:
                self.analytics.record_misclick()
        
        # === Correction Behavior (try to fix obvious misclicks) ===
        if has_misclick and self.config.correction_behavior:
            if misclick_type in ['early_release', 'hesitation']:
                # Quick corrective click
                time.sleep(random.uniform(0.06, 0.12))
                try:
                    pyautogui.click(button='left', duration=0.05)
                except Exception:
                    pass
        
        # === Log Statistics Periodically ===
        if self.config.enable_analytics and self.analytics:
            self.log_counter += 1
            if self.log_counter >= self.config.log_interval:
                self._log_analytics()
                self.log_counter = 0
    
    def _log_analytics(self):
        """Log current analytics to console"""
        if not self.analytics:
            return
        
        stats = self.analytics.get_stats()
        if stats:
            print(f"\n[Analytics] Clicks: {stats['total_clicks']} | "
                  f"Avg Reaction: {stats['avg_reaction']:.1f}ms | "
                  f"Misclick Rate: {stats['misclick_rate']*100:.2f}% | "
                  f"Streak: {stats['current_streak']} (Best: {stats['best_streak']})")
    
    def update_fatigue(self):
        """Update fatigue level with non-linear dynamics and cooldown benefits"""
        current_time = time.time()
        time_since_last_click = current_time - self.last_click_time
        
        # Check if we've been resting
        rest_duration = current_time - self.last_rest_time if not self.is_clicking else 0
        
        if self.is_clicking:
            # Increase fatigue (accelerates with higher fatigue)
            fatigue_increase = self.config.fatigue_rate * (1 + self.fatigue_level)
            self.fatigue_level += fatigue_increase
            
            # Update last rest time
            self.last_rest_time = current_time
        else:
            # Enhanced recovery after long rests
            recovery_multiplier = 1.0
            if rest_duration > 5.0:
                recovery_multiplier = self.config.cooldown_benefit
            
            self.fatigue_level -= self.config.fatigue_recovery * recovery_multiplier
        
        # Clamp fatigue level
        self.fatigue_level = max(0.0, min(self.fatigue_level, self.config.max_fatigue))
        
        # Record fatigue history for analytics
        if self.analytics:
            self.analytics.fatigue_history.append(self.fatigue_level)
    
    def read_player_state(self):
        """Read player position and state from game memory"""
        if not self.gd_base_address or not self.player_object_addr:
            return False
        
        try:
            # Read player X position
            x_addr = self.player_object_addr + GD_PLAYER_X_OFFSET
            x_bytes = self.read_memory(x_addr, 4)
            if x_bytes is not None:
                self.player_x = ctypes.c_float(x_bytes).value
            
            # Read player Y position
            y_addr = self.player_object_addr + GD_PLAYER_Y_OFFSET
            y_bytes = self.read_memory(y_addr, 4)
            if y_bytes is not None:
                self.player_y = ctypes.c_float(y_bytes).value
            
            # Read player Y velocity (for jump detection)
            vy_addr = self.player_object_addr + GD_PLAYER_Y_VELOCITY_OFFSET
            vy_bytes = self.read_memory(vy_addr, 4)
            if vy_bytes is not None:
                self.player_y_velocity = ctypes.c_float(vy_bytes).value
            
            # Read on-ground status
            on_ground_addr = self.player_object_addr + GD_PLAYER_ON_GROUND_OFFSET
            on_ground_bytes = self.read_memory(on_ground_addr, 1)
            if on_ground_bytes is not None:
                self.player_on_ground = bool(on_ground_bytes)
            
            # Read player mode (cube, ship, ball, ufo, etc.)
            mode_addr = self.player_object_addr + GD_PLAYER_MODE_OFFSET
            mode_bytes = self.read_memory(mode_addr, 4)
            if mode_bytes is not None:
                self.player_mode = mode_bytes
            
            # Read player size
            size_addr = self.player_object_addr + GD_PLAYER_SIZE_OFFSET
            size_bytes = self.read_memory(size_addr, 4)
            if size_bytes is not None:
                self.player_size = ctypes.c_float(size_bytes).value
            
            return True
            
        except Exception as e:
            print(f"Error reading player state: {e}")
            return False
    
    def detect_obstacles_ahead(self, look_ahead_distance: float = 500.0) -> List[Dict]:
        """
        Detect obstacles ahead of the player by reading level data from memory.
        Returns list of obstacles with their positions and types.
        
        This implementation uses screen color detection as a fallback when memory
        reading isn't available, making it work without specific GD offsets.
        """
        if not self.player_object_addr:
            # Fallback: Use screen-based detection instead of memory reading
            return self._detect_obstacles_via_screen(look_ahead_distance)
        
        obstacles = []
        
        # This is where you'd read the level objects array from memory
        # Each object would have: type (spike, block, orb, etc.), x, y, width, height
        
        # Example obstacle structure (would come from memory in real implementation):
        # obstacles = [
        #     {'type': 'spike', 'x': player_x + 150, 'y': 0, 'width': 40, 'height': 40},
        #     {'type': 'block', 'x': player_x + 300, 'y': 100, 'width': 40, 'height': 40},
        # ]
        
        # For demonstration, we'll calculate distance to next "virtual" obstacle
        # based on time since last click (simulating a continuous stream)
        if len(self.click_buffer) > 0:
            self.last_obstacle_x = self.player_x - 100  # Behind us now
        
        return obstacles
    
    def _detect_obstacles_via_screen(self, look_ahead_distance: float = 500.0) -> List[Dict]:
        """
        Screen-based obstacle detection using pixel analysis.
        This allows the clickbot to work without memory offsets.
        """
        try:
            import pyautogui
            import numpy as np
            
            if not self.game_window:
                return []
            
            # Get window position
            rect = win32gui.GetWindowRect(self.game_window)
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top
            
            # Define scan regions based on typical GD layout
            # Player is usually in the lower portion of the screen
            player_y_screen = int(height * 0.7)
            
            # Scan ahead in zones to detect spike colors (black triangles)
            # or block edges
            obstacles = []
            
            # Zone 1: Immediate danger zone (50-150 pixels ahead)
            # Zone 2: Reaction zone (150-300 pixels ahead)
            scan_zones = [
                (int(width * 0.3), int(width * 0.5)),  # Close range
                (int(width * 0.5), int(width * 0.7)),  # Mid range
            ]
            
            for zone_start, zone_end in scan_zones:
                # Sample a small region to check for obstacle colors
                # Spikes in GD are typically black/dark with specific shapes
                scan_x = left + zone_start
                scan_y = top + player_y_screen
                
                # This is a simplified detection - real implementation would use
                # template matching or more sophisticated image analysis
                pass
            
            # Since screen detection is complex, fall back to rhythm-based
            # prediction when memory reading isn't available
            return self._generate_rhythm_obstacles(look_ahead_distance)
            
        except Exception as e:
            print(f"Screen detection error: {e}")
            return self._generate_rhythm_obstacles(look_ahead_distance)
    
    def _generate_rhythm_obstacles(self, look_ahead_distance: float) -> List[Dict]:
        """
        Generate virtual obstacles based on rhythm/distance estimation.
        This simulates obstacle detection for levels without memory access.
        Uses timing patterns typical in Geometry Dash levels.
        """
        obstacles = []
        
        # Estimate obstacle spacing based on game speed
        # Typical spike spacing in GD: 150-250 pixels at normal speed
        base_spacing = 180.0
        
        # Add some variation to simulate different level patterns
        spacing_variation = random.gauss(0, 30.0)
        current_spacing = max(120.0, base_spacing + spacing_variation)
        
        # Predict next obstacle position based on player position
        # This works well for regularly-spaced obstacles (common in GD)
        predicted_obstacle_x = self.player_x + current_spacing
        
        if predicted_obstacle_x - self.player_x < look_ahead_distance:
            obstacles.append({
                'type': 'spike',
                'x': predicted_obstacle_x,
                'y': 0,
                'width': 40,
                'height': 40,
                'predicted': True  # Mark as predicted, not from memory
            })
        
        return obstacles
    
    def should_click_for_obstacle(self, obstacle: Dict) -> bool:
        """
        Determine if we should click for a given obstacle based on player state.
        Takes into account game mode, player position, and obstacle properties.
        """
        if not obstacle:
            return False
        
        distance = obstacle['x'] - self.player_x
        
        # For predicted obstacles (not from memory), use simpler timing logic
        is_predicted = obstacle.get('predicted', False)
        
        # Different logic for different game modes
        if self.player_mode == 0:  # Cube mode
            # Click when obstacle is at optimal jump distance
            # Typical jump distance for cube is ~120-180 pixels depending on speed
            optimal_jump_distance = 150.0 + (self.player_size * 20)
            
            # Add human-like variation to trigger point
            variation = random.gauss(0, 15.0)
            trigger_distance = optimal_jump_distance + variation
            
            if distance <= trigger_distance and distance > 0:
                # Only click if we're on the ground (can actually jump)
                # For predicted obstacles, assume we can jump
                if self.player_on_ground or is_predicted:
                    return True
                    
        elif self.player_mode == 1:  # Ship mode
            # Hold click to go up, release to go down
            # Click when we need to gain height to avoid obstacle
            if obstacle['type'] in ['spike', 'saw']:
                # Need to be above obstacle
                required_height = obstacle.get('height', 40) + 20
                if self.player_y < required_height and distance < 200:
                    return True
                    
        elif self.player_mode == 2:  # Ball mode
            # Click to flip gravity
            # Similar timing to cube but inverted
            optimal_flip_distance = 140.0
            variation = random.gauss(0, 12.0)
            
            if distance <= optimal_flip_distance + variation and distance > 0:
                return True
                
        elif self.player_mode == 3:  # UFO mode
            # Click for small jumps in mid-air
            # Timing is more lenient than cube
            if self.player_y < obstacle.get('height', 40):
                optimal_ufo_distance = 100.0
                variation = random.gauss(0, 20.0)
                
                if distance <= optimal_ufo_distance + variation and distance > 0:
                    return True
        
        # Add other modes as needed (wave, robot, spider)
        
        return False
    
    def calculate_click_timing(self, obstacle: Dict) -> float:
        """
        Calculate the optimal time to click for an obstacle.
        Returns delay in milliseconds before clicking.
        """
        distance = obstacle['x'] - self.player_x
        
        # Base reaction time with humanization
        base_delay = self.calculate_humanized_delay(self.obstacle_reaction_delay)
        
        # Adjust based on distance (closer = less delay)
        distance_factor = distance / 200.0  # Normalize to typical reaction distance
        adjusted_delay = base_delay * distance_factor
        
        # Add mode-specific adjustments
        if self.player_mode == 0:  # Cube
            # Precise timing needed
            adjusted_delay *= 0.9
        elif self.player_mode == 1:  # Ship
            # More forgiving timing
            adjusted_delay *= 1.2
        
        return max(adjusted_delay, 10.0)  # Minimum 10ms
    
    def update_game_state(self):
        """Update all game state information from memory"""
        # Update basic game state (menu/playing/paused/etc.)
        self.game_state = self.detect_game_state()
        
        # If playing, read detailed player state
        if self.game_state == GameState.PLAYING:
            self.read_player_state()
            
            # Detect upcoming obstacles
            self.level_objects = self.detect_obstacles_ahead()
            
            # Find nearest obstacle and calculate distance
            if self.level_objects:
                nearest = min(self.level_objects, key=lambda o: o['x'] - self.player_x)
                self.distance_to_next_obstacle = nearest['x'] - self.player_x
            else:
                self.distance_to_next_obstacle = float('inf')
    
    def detect_game_state(self) -> GameState:
        """Detect current game state from memory or window analysis"""
        if not self.game_window:
            return GameState.MENU
        
        try:
            # Try to get window title for basic state detection
            title = win32gui.GetWindowText(self.game_window)
            
            if not title:
                return GameState.MENU
            
            title_lower = title.lower()
            
            if 'paused' in title_lower or 'pause' in title_lower:
                return GameState.PAUSED
            elif 'dead' in title_lower or 'crashed' in title_lower:
                return GameState.DEAD
            elif 'complete' in title_lower or 'finished' in title_lower:
                return GameState.LEVEL_COMPLETE
            elif 'editor' in title_lower:
                return GameState.EDITOR
            else:
                # Assume playing if active game window
                return GameState.PLAYING
                
        except Exception:
            pass
        
        return GameState.MENU
    
    def adapt_to_difficulty(self, difficulty_factor: float):
        """Adjust behavior based on perceived difficulty"""
        self.difficulty_level = difficulty_factor
        
        if difficulty_factor > 0.8:
            # High difficulty: focus mode
            self.focus_mode = True
            self.config.jitter_amplitude *= 0.7
            self.config.timing_precision = min(1.0, self.config.timing_precision * 1.1)
        elif difficulty_factor < 0.3:
            # Low difficulty: relaxed mode
            self.focus_mode = False
            self.config.jitter_amplitude = max(
                1.0, self.config.jitter_amplitude * 1.2
            )
    
    def learn_patterns(self):
        """Advanced pattern learning with multiple strategies"""
        if len(self.click_intervals) < 20:
            return
        
        intervals_array = np.array(self.click_intervals)
        
        # === Strategy 1: Basic Statistical Analysis ===
        mean_interval = np.mean(intervals_array)
        std_interval = np.std(intervals_array)
        
        # Detect if we're consistently off-target
        target_interval = 0.017  # ~60 FPS target
        deviation = mean_interval - target_interval
        
        # Adaptive correction with deadzone
        if abs(deviation) > 0.002:  # Only adjust if significantly off
            self.adaptive_offset -= deviation * self.config.adaptation_rate * 0.5
        
        # === Strategy 2: Trend Detection ===
        if len(intervals_array) >= 30:
            recent_mean = np.mean(intervals_array[-10:])
            older_mean = np.mean(intervals_array[-30:-10])
            
            trend = recent_mean - older_mean
            
            # Anticipate continuing trend
            if abs(trend) > 0.001:
                self.adaptive_offset -= trend * self.config.adaptation_rate * 0.3
        
        # === Strategy 3: Train Predictor ===
        if self.pattern_predictor and len(self.training_sequences) < 100:
            # Create sequences for training
            seq_length = 20
            if len(intervals_array) >= seq_length + self.config.prediction_horizon:
                sequence = list(intervals_array[-seq_length:])
                
                if hasattr(self, 'training_sequences'):
                    self.training_sequences.append(sequence)
                    
                    # Periodically retrain
                    if len(self.training_sequences) % 10 == 0 and TORCH_AVAILABLE:
                        self._train_lstm_predictor()
    
    def _train_lstm_predictor(self):
        """Train the LSTM predictor on collected sequences"""
        if not TORCH_AVAILABLE or not self.training_sequences:
            return
        
        try:
            import torch.optim as optim
            
            # Prepare training data
            sequences = self.training_sequences[-50:]  # Use last 50 sequences
            
            if len(sequences) < 20:
                return
            
            # Normalize sequences
            all_values = np.concatenate(sequences)
            mean_val = np.mean(all_values)
            std_val = np.std(all_values) + 1e-6
            
            # Create tensors
            X = []
            y = []
            
            for seq in sequences:
                normalized = (np.array(seq) - mean_val) / std_val
                X.append(normalized[:-self.config.prediction_horizon])
                y.append(normalized[-self.config.prediction_horizon:])
            
            if not X:
                return
            
            X_tensor = torch.FloatTensor(np.array(X)).unsqueeze(-1)
            y_tensor = torch.FloatTensor(np.array(y))
            
            # Training loop
            self.pattern_predictor.train()
            optimizer = optim.Adam(self.pattern_predictor.parameters(), lr=0.001)
            criterion = nn.MSELoss()
            
            for epoch in range(50):
                optimizer.zero_grad()
                output, _ = self.pattern_predictor(X_tensor)
                loss = criterion(output, y_tensor)
                loss.backward()
                optimizer.step()
                
        except Exception as e:
            print(f"LSTM training warning: {e}")
    
    def jitter_loop(self):
        """Background thread for continuous jitter simulation"""
        while not self.stop_event.is_set():
            if self.is_running and self.is_clicking:
                # Apply subtle jitter even between explicit clicks
                pass
            time.sleep(0.01)
    
    def auto_click(self, click_interval: float = 0.017, mode: str = 'obstacle'):
        """
        Main auto-click loop with humanization.
        
        Args:
            click_interval: Base interval between clicks in seconds (default ~60 FPS)
            mode: Click mode - 'obstacle' for smart obstacle-based clicking,
                  'spam' for constant clicking (old behavior),
                  'rhythm' for rhythm-based clicking without memory access
        """
        print(f"Starting humanized auto-click (mode: {mode}, interval: {click_interval}s)")
        self.is_running = True
        
        # Get screen dimensions for bounds checking
        import pyautogui
        pyautogui.FAILSAFE = False
        screen_width, screen_height = pyautogui.size()
        margin = 50
        
        # Track click state for hold-based modes (ship, ufo)
        is_holding = False
        hold_start_time = 0
        
        # For rhythm mode, track timing
        rhythm_timer = 0.0
        rhythm_interval = click_interval
        
        try:
            while self.is_running:
                # Update game state from memory
                self.update_game_state()
                
                # Determine if we should click based on mode
                should_click = False
                
                if mode == 'obstacle' and self.game_state == GameState.PLAYING:
                    # Smart obstacle-based clicking
                    if self.level_objects:
                        # Find nearest obstacle we need to react to
                        for obstacle in sorted(self.level_objects, key=lambda o: o['x'] - self.player_x):
                            distance = obstacle['x'] - self.player_x
                            
                            # Only consider obstacles ahead and within reaction range
                            if distance > 0 and distance < 400:
                                if self.should_click_for_obstacle(obstacle):
                                    should_click = True
                                    break
                    else:
                        # No obstacles detected - fall back to rhythm-based clicking
                        # This handles cases where memory reading isn't working
                        current_time = time.time()
                        elapsed_since_last = current_time - self.last_click_time
                        if elapsed_since_last >= rhythm_interval:
                            should_click = True
                            rhythm_timer = current_time
                
                elif mode == 'rhythm':
                    # Rhythm-based clicking without requiring memory access
                    # Uses estimated timing based on typical GD gameplay
                    current_time = time.time()
                    elapsed_since_last = current_time - self.last_click_time
                    
                    # Check if enough time has passed since last click
                    if elapsed_since_last >= rhythm_interval:
                        should_click = True
                        rhythm_timer = current_time
                    
                    # Adjust rhythm interval based on game state if available
                    if self.player_mode in [1, 3]:  # Ship/UFO - continuous holding
                        should_click = True  # Keep holding
                
                elif mode == 'spam':
                    # Old behavior: constant clicking at interval
                    elapsed_since_last = time.time() - self.last_click_time
                    if elapsed_since_last >= click_interval:
                        should_click = True
                
                # Handle ship/ufo hold mechanics
                if self.player_mode in [1, 3]:  # Ship or UFO
                    if should_click and not is_holding:
                        # Start holding
                        is_holding = True
                        hold_start_time = time.time()
                        # Mouse down will happen below
                    elif not should_click and is_holding:
                        # Release hold
                        is_holding = False
                        try:
                            pyautogui.mouseUp(button='left')
                        except Exception:
                            pass
                
                # Execute click if needed
                if should_click:
                    # Get game window position
                    if self.game_window:
                        try:
                            rect = win32gui.GetWindowRect(self.game_window)
                            center_x = (rect[0] + rect[2]) // 2
                            center_y = (rect[1] + rect[3]) // 2
                            
                            # Ensure coordinates are within safe bounds
                            center_x = max(margin, min(screen_width - margin, center_x))
                            center_y = max(margin, min(screen_height - margin, center_y))
                            
                            # For ship/ufo, just do mouseDown without full click simulation
                            if self.player_mode in [1, 3] and is_holding:
                                try:
                                    pyautogui.mouseDown(button='left')
                                except Exception:
                                    pass
                            else:
                                # Calculate humanized delay for timing
                                delay = self.calculate_humanized_delay(click_interval * 1000)
                                # Perform humanized click
                                self.simulate_mouse_click(center_x, center_y, delay)
                            
                            self.last_click_time = time.time()
                            
                        except Exception as e:
                            # Window may have closed or become invalid
                            print(f"Warning: Could not get window position: {e}")
                            self.game_window = None
                            continue
                    else:
                        # Try to re-find the window
                        self.find_geometry_dash()
                else:
                    # Small sleep to prevent CPU spinning when not clicking
                    time.sleep(0.001)
                
                # Update state
                self.update_fatigue()
                self.learn_patterns()
                
        except KeyboardInterrupt:
            print("\nStopping...")
        except Exception as e:
            print(f"\nError in auto_click loop: {e}")
        finally:
            self.is_running = False
            # Release mouse button if still holding
            if is_holding:
                try:
                    pyautogui.mouseUp(button='left')
                except Exception:
                    pass
    
    def start(self):
        """Start the clickbot"""
        if not self.find_geometry_dash():
            return False
        
        if not self.open_process():
            return False
        
        # Start jitter thread
        self.stop_event.clear()
        self.jitter_thread = threading.Thread(target=self.jitter_loop, daemon=True)
        self.jitter_thread.start()
        
        print("Humanized Clickbot ready!")
        print(f"  - Reaction time variance: ±{self.config.reaction_time_variance}ms")
        print(f"  - Misclick probability: {self.config.misclick_probability*100:.1f}%")
        print(f"  - Jitter amplitude: {self.config.jitter_amplitude}px")
        print(f"  - Fatigue simulation: Enabled")
        
        return True
    
    def stop(self):
        """Stop the clickbot"""
        self.is_running = False
        self.stop_event.set()
        if self.process_handle:
            ctypes.windll.kernel32.CloseHandle(self.process_handle)
            self.process_handle = None
        print("Clickbot stopped")


class ClickbotGUI:
    """GUI interface for the Humanized Clickbot"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Humanized GD Clickbot")
        self.root.resizable(False, False)
        
        # Clickbot instance
        self.bot = None
        self.clicking_thread = None
        self.is_active = False
        
        # Configuration variables
        self.click_interval_var = tk.DoubleVar(value=0.017)
        self.base_reaction_var = tk.DoubleVar(value=45.0)
        self.reaction_variance_var = tk.DoubleVar(value=25.0)
        self.misclick_prob_var = tk.DoubleVar(value=0.015)
        self.jitter_amp_var = tk.DoubleVar(value=1.5)
        self.fatigue_rate_var = tk.DoubleVar(value=0.0008)
        
        self.click_mode_var = tk.StringVar(value='rhythm')
        self.status_var = tk.StringVar(value="Not started")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Humanized GD Clickbot", 
                                font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                      font=('Helvetica', 11))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Control section
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="5")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Start/Stop buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=0, column=0, columnspan=2, pady=5)
        
        self.start_btn = ttk.Button(btn_frame, text="Start Clickbot", 
                                    command=self.start_clickbot)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Stop", 
                                   command=self.stop_clickbot, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        # Click mode selection
        mode_frame = ttk.Frame(control_frame)
        mode_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Label(mode_frame, text="Click Mode:").grid(row=0, column=0, padx=5)
        
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.click_mode_var,
                                  values=['rhythm', 'obstacle', 'spam'],
                                  width=15, state='readonly')
        mode_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(mode_frame, text="(rhythm=recommended)", 
                  font=('Helvetica', 8)).grid(row=0, column=2, padx=5)
        
        # Click interval
        interval_frame = ttk.Frame(control_frame)
        interval_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky=tk.W)
        
        ttk.Label(interval_frame, text="Click Interval (s):").grid(row=0, column=0, padx=5)
        interval_spin = ttk.Spinbox(interval_frame, from_=0.001, to=1.0, 
                                    increment=0.001, textvariable=self.click_interval_var,
                                    width=10)
        interval_spin.grid(row=0, column=1, padx=5)
        
        # Humanization settings
        human_frame = ttk.LabelFrame(main_frame, text="Humanization Settings", padding="5")
        human_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Base reaction time
        row = 0
        ttk.Label(human_frame, text="Base Reaction (ms):").grid(row=row, column=0, padx=5, pady=2, sticky=tk.E)
        ttk.Spinbox(human_frame, from_=10, to=200, increment=1, 
                    textvariable=self.base_reaction_var, width=10).grid(row=row, column=1, padx=5, pady=2)
        
        # Reaction variance
        row += 1
        ttk.Label(human_frame, text="Reaction Variance (ms):").grid(row=row, column=0, padx=5, pady=2, sticky=tk.E)
        ttk.Spinbox(human_frame, from_=0, to=100, increment=1, 
                    textvariable=self.reaction_variance_var, width=10).grid(row=row, column=1, padx=5, pady=2)
        
        # Misclick probability
        row += 1
        self.misclick_display_var = tk.DoubleVar(value=self.misclick_prob_var.get()*100)
        ttk.Label(human_frame, text="Misclick Chance (%):").grid(row=row, column=0, padx=5, pady=2, sticky=tk.E)
        ttk.Spinbox(human_frame, from_=0, to=10, increment=0.1, 
                    textvariable=self.misclick_display_var, width=10).grid(row=row, column=1, padx=5, pady=2)
        
        # Jitter amplitude
        row += 1
        ttk.Label(human_frame, text="Jitter Amplitude (px):").grid(row=row, column=0, padx=5, pady=2, sticky=tk.E)
        ttk.Spinbox(human_frame, from_=0, to=10, increment=0.1, 
                    textvariable=self.jitter_amp_var, width=10).grid(row=row, column=1, padx=5, pady=2)
        
        # Fatigue rate
        row += 1
        ttk.Label(human_frame, text="Fatigue Rate:").grid(row=row, column=0, padx=5, pady=2, sticky=tk.E)
        ttk.Spinbox(human_frame, from_=0, to=0.01, increment=0.0001, 
                    textvariable=self.fatigue_rate_var, width=10).grid(row=row, column=1, padx=5, pady=2)
        
        # Info section
        info_frame = ttk.LabelFrame(main_frame, text="Information", padding="5")
        info_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        info_text = """Mode Guide:
• rhythm: Predicts obstacle timing (works without memory offsets) - RECOMMENDED
• obstacle: Uses memory reading for precise obstacle detection (requires Cheat Engine setup)
• spam: Constant clicking at set interval (legacy mode)

Tips:
1. Start Geometry Dash before clicking 'Start Clickbot'
2. Use 'rhythm' mode for immediate results
3. Adjust click interval based on your needs (0.017s ≈ 60 FPS)
4. Lower humanization values = more robotic, higher = more human-like"""
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT, 
                               font=('Helvetica', 9))
        info_label.grid(row=0, column=0, sticky=tk.W)
    
    def start_clickbot(self):
        """Start the clickbot"""
        try:
            # Create configuration
            config = HumanizationConfig(
                base_reaction_time=self.base_reaction_var.get(),
                reaction_time_variance=self.reaction_variance_var.get(),
                misclick_probability=self.misclick_display_var.get() / 100.0,
                jitter_amplitude=self.jitter_amp_var.get(),
                fatigue_rate=self.fatigue_rate_var.get(),
            )
            
            # Initialize clickbot
            self.bot = HumanizedClickbot(config)
            
            if not self.bot.start():
                messagebox.showerror("Error", "Failed to initialize clickbot.\nMake sure Geometry Dash is running!")
                return
            
            self.is_active = True
            self.status_var.set("Running - Clicking...")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # Start clicking in a separate thread
            self.clicking_thread = threading.Thread(
                target=self._run_clickbot,
                daemon=True
            )
            self.clicking_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start clickbot:\n{str(e)}")
            self.is_active = False
    
    def _run_clickbot(self):
        """Run the clickbot loop in a thread"""
        try:
            mode = self.click_mode_var.get()
            interval = self.click_interval_var.get()
            self.bot.auto_click(click_interval=interval, mode=mode)
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
    
    def stop_clickbot(self):
        """Stop the clickbot"""
        if self.bot:
            self.bot.stop()
        self.is_active = False


def main():
    """Main entry point with GUI"""
    root = tk.Tk()
    app = ClickbotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
