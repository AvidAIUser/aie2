#!/usr/bin/env python3
"""
AI-Assisted Humanized Clickbot for Geometry Dash
Injects natural human imperfections: variable reaction times, slight misclicks, and mouse jitter.
"""

import ctypes
import ctypes.wintypes
import time
import random
import math
import threading
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List
import win32gui
import win32process
import win32con
import psutil

# Windows API constants
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020

@dataclass
class HumanizationConfig:
    """Configuration for human-like behavior"""
    # Reaction time variations (milliseconds)
    base_reaction_time: float = 50.0
    reaction_time_variance: float = 30.0
    reaction_time_drift: float = 5.0  # Gradual drift over time
    
    # Misclick probability and patterns
    misclick_probability: float = 0.02  # 2% chance of misclick
    misclick_delay_range: Tuple[float, float] = (80.0, 150.0)  # Delay when misclick occurs
    double_click_probability: float = 0.01  # 1% chance of accidental double click
    
    # Mouse jitter parameters
    jitter_amplitude: float = 2.0  # Pixels
    jitter_frequency: float = 15.0  # Hz
    jitter_decay: float = 0.95  # Decay factor during sustained clicks
    
    # Click duration variations
    base_click_duration: float = 80.0  # ms
    click_duration_variance: float = 25.0  # ms
    
    # Fatigue simulation (performance degrades over time)
    fatigue_rate: float = 0.001  # Per second
    max_fatigue: float = 0.3  # Maximum fatigue effect
    fatigue_recovery: float = 0.01  # Recovery per second of rest
    
    # Learning/adaptation
    adaptation_rate: float = 0.05  # How quickly to adapt to patterns
    pattern_memory_size: int = 100  # Number of recent clicks to analyze


class HumanizedClickbot:
    """Main clickbot class with humanization features"""
    
    def __init__(self, config: Optional[HumanizationConfig] = None):
        self.config = config or HumanizationConfig()
        self.process_handle = None
        self.game_pid = None
        self.game_window = None
        self.base_address = None
        
        # State variables
        self.is_running = False
        self.is_clicking = False
        self.fatigue_level = 0.0
        self.last_click_time = 0.0
        self.recent_clicks: List[float] = []
        self.jitter_phase = random.random() * 2 * math.pi
        
        # Pattern learning
        self.click_pattern_history = []
        self.adaptive_offset = 0.0
        
        # Thread control
        self.jitter_thread = None
        self.stop_event = threading.Event()
        
        # Memory addresses (will be updated dynamically)
        self.player_object_addr = None
        self.is_dead_addr = None
        self.progress_addr = None
        
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
            return True
        except Exception as e:
            print(f"Error opening process: {e}")
            return False
    
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
    
    def calculate_humanized_delay(self, base_delay: float) -> float:
        """Calculate delay with human variations"""
        # Base reaction time with variance
        reaction = self.config.base_reaction_time + random.gauss(
            0, 
            self.config.reaction_time_variance
        )
        
        # Add fatigue effect
        fatigue_modifier = 1.0 + (self.fatigue_level * 0.5)
        
        # Add adaptive offset based on learned patterns
        adaptive = self.adaptive_offset
        
        # Combine all factors
        total_delay = (base_delay + reaction) * fatigue_modifier + adaptive
        
        # Ensure minimum delay
        return max(total_delay, 15.0)
    
    def should_misclick(self) -> bool:
        """Determine if a misclick should occur"""
        return random.random() < self.config.misclick_probability
    
    def generate_jitter(self, t: float) -> Tuple[float, float]:
        """Generate natural mouse jitter using Perlin-like noise"""
        # Multiple sine waves for natural movement
        jitter_x = 0.0
        jitter_y = 0.0
        
        for i in range(3):
            freq = self.config.jitter_frequency * (i + 1) * 0.5
            amp = self.config.jitter_amplitude / (i + 1)
            phase = self.jitter_phase + (i * math.pi / 3)
            
            jitter_x += amp * math.sin(2 * math.pi * freq * t + phase)
            jitter_y += amp * math.cos(2 * math.pi * freq * t + phase * 1.3)
        
        # Add some randomness
        jitter_x += random.gauss(0, self.config.jitter_amplitude * 0.3)
        jitter_y += random.gauss(0, self.config.jitter_amplitude * 0.3)
        
        # Decay jitter during sustained clicking
        if self.is_clicking:
            decay = self.config.jitter_decay
            jitter_x *= decay
            jitter_y *= decay
        
        return (jitter_x, jitter_y)
    
    def simulate_mouse_click(self, x: int, y: int, duration_ms: float):
        """Simulate a human-like mouse click with jitter"""
        import pyautogui
        
        # Apply jitter to click position
        t = time.time()
        jitter_x, jitter_y = self.generate_jitter(t)
        
        click_x = int(x + jitter_x)
        click_y = int(y + jitter_y)
        
        # Move mouse with slight curve (Bezier-like)
        start_x, start_y = pyautogui.position()
        steps = 5
        for i in range(steps):
            progress = i / steps
            # Add slight arc to movement
            arc_offset = math.sin(progress * math.pi) * 10
            intermediate_x = int(start_x + (click_x - start_x) * progress)
            intermediate_y = int(start_y + (click_y - start_y) * progress - arc_offset)
            pyautogui.moveTo(intermediate_x, intermediate_y, duration=0.01)
            time.sleep(0.005)
        
        # Check for misclick
        if self.should_misclick():
            # Delay before clicking (hesitation)
            delay = random.uniform(*self.config.misclick_delay_range)
            time.sleep(delay / 1000.0)
            
            # Maybe click wrong position
            if random.random() < 0.5:
                click_x += random.randint(-20, 20)
                click_y += random.randint(-20, 20)
        
        # Click down
        pyautogui.mouseDown(button='left')
        self.is_clicking = True
        
        # Hold with micro-variations
        hold_duration = self.config.base_click_duration + random.gauss(
            0, 
            self.config.click_duration_variance
        )
        hold_duration = max(hold_duration, 30.0)  # Minimum hold time
        
        # Add jitter during hold
        jitter_steps = int(hold_duration / 10)
        for i in range(jitter_steps):
            jitter_x, jitter_y = self.generate_jitter(time.time())
            pyautogui.moveRel(jitter_x * 0.5, jitter_y * 0.5, duration=0.005)
            time.sleep(0.01)
        
        # Click up
        pyautogui.mouseUp(button='left')
        self.is_clicking = False
        
        # Check for accidental double-click
        if random.random() < self.config.double_click_probability:
            time.sleep(random.uniform(0.05, 0.15))
            pyautogui.click(button='left')
        
        # Record click timing for pattern learning
        self.recent_clicks.append(time.time())
        if len(self.recent_clicks) > self.config.pattern_memory_size:
            self.recent_clicks.pop(0)
    
    def update_fatigue(self):
        """Update fatigue level based on activity"""
        current_time = time.time()
        
        if self.is_clicking:
            # Increase fatigue
            self.fatigue_level += self.config.fatigue_rate
        else:
            # Recover from fatigue
            self.fatigue_level -= self.config.fatigue_recovery
        
        # Clamp fatigue level
        self.fatigue_level = max(0.0, min(self.fatigue_level, self.config.max_fatigue))
    
    def learn_patterns(self):
        """Analyze recent clicks to adapt timing"""
        if len(self.recent_clicks) < 10:
            return
        
        # Calculate inter-click intervals
        intervals = []
        for i in range(1, len(self.recent_clicks)):
            interval = self.recent_clicks[i] - self.recent_clicks[i-1]
            intervals.append(interval)
        
        # Detect if we're consistently early or late
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            # Adjust adaptive offset based on deviation
            target_interval = 0.017  # ~60 FPS
            self.adaptive_offset += (target_interval - avg_interval) * self.config.adaptation_rate
    
    def jitter_loop(self):
        """Background thread for continuous jitter simulation"""
        while not self.stop_event.is_set():
            if self.is_running and self.is_clicking:
                # Apply subtle jitter even between explicit clicks
                pass
            time.sleep(0.01)
    
    def auto_click(self, click_interval: float = 0.017):
        """Main auto-click loop with humanization"""
        print(f"Starting humanized auto-click (interval: {click_interval}s)")
        self.is_running = True
        
        try:
            while self.is_running:
                # Calculate humanized delay
                delay = self.calculate_humanized_delay(click_interval * 1000)
                
                # Wait with variation
                time.sleep(delay / 1000.0)
                
                # Get game window position
                if self.game_window:
                    rect = win32gui.GetWindowRect(self.game_window)
                    center_x = (rect[0] + rect[2]) // 2
                    center_y = (rect[1] + rect[3]) // 2
                    
                    # Perform humanized click
                    self.simulate_mouse_click(center_x, center_y, delay)
                
                # Update state
                self.update_fatigue()
                self.learn_patterns()
                
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self.is_running = False
    
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


def main():
    """Main entry point"""
    print("=" * 60)
    print("AI-Assisted Humanized Clickbot for Geometry Dash")
    print("=" * 60)
    print()
    
    # Create custom configuration
    config = HumanizationConfig(
        base_reaction_time=45.0,
        reaction_time_variance=25.0,
        misclick_probability=0.015,
        jitter_amplitude=1.5,
        fatigue_rate=0.0008,
    )
    
    # Initialize clickbot
    bot = HumanizedClickbot(config)
    
    if not bot.start():
        print("Failed to initialize clickbot")
        return
    
    # Start auto-clicking
    # Adjust interval as needed (0.017 ≈ 60 FPS)
    try:
        bot.auto_click(click_interval=0.017)
    except KeyboardInterrupt:
        pass
    finally:
        bot.stop()


if __name__ == "__main__":
    main()
