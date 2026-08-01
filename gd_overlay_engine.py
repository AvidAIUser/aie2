"""
GD Overlay Engine (Standalone Process)
This script runs as a separate lightweight process to render the click-through overlay.
It communicates with the main controller via multiprocessing queues.
"""
import tkinter as tk
import sys
import json
import os
from multiprocessing import Queue

class OverlayEngine:
    def __init__(self, input_queue: Queue, output_queue: Queue):
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.root = None
        self.canvas = None
        self.is_click_through = False
        self.overlay_data = {
            'enabled': False,
            'regions': [],
            'colors': [],
            'snap_rect': None,
            'text': ""
        }
        self.setup_gui()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("GD Overlay")
        
        # Fullscreen transparent window
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        
        self.root.geometry(f"{screen_w}x{screen_h}+0+0")
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)  # Slightly visible background for debug, can be 0.0
        self.root.overrideredirect(True)  # No title bar
        
        # Make background transparent (Windows specific)
        self.root.wm_attributes("-transparentcolor", "black")
        
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initial click-through state
        self.set_click_through(True)
        
        # Start polling for messages
        self.poll_queue()
        
        # Handle close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def set_click_through(self, enable: bool):
        # Only update if state actually changes
        if self.is_click_through == enable:
            return
        
        # Prevent rapid state changes that cause blinking (minimum 150ms between changes)
        import time
        if not hasattr(self, 'last_state_change'):
            self.last_state_change = 0
        current_time = time.time()
        if current_time - self.last_state_change < 0.15:
            return
        
        self.last_state_change = current_time
        self.is_click_through = enable
        
        try:
            hwnd = self.root.winfo_id()
            import ctypes
            user32 = ctypes.windll.user32
            ex_style = user32.GetWindowLongW(hwnd, -20) # GWL_EXSTYLE
            
            if enable:
                # Add WS_EX_TRANSPARENT (0x20) while keeping WS_EX_LAYERED (0x80)
                new_style = ex_style | 0x20 | 0x80
            else:
                # Remove WS_EX_TRANSPARENT but keep WS_EX_LAYERED
                new_style = ex_style & ~0x20 | 0x80
            
            # Only call SetWindowLongW if style actually changed
            if new_style != ex_style:
                user32.SetWindowLongW(hwnd, -20, new_style)
                # Force a single redraw after style change
                user32.RedrawWindow(hwnd, None, None, 0x0411) # RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN
        except Exception:
            pass

    def poll_queue(self):
        """Non-blocking check for messages from main process"""
        try:
            while not self.input_queue.empty():
                msg = self.input_queue.get_nowait()
                self.handle_message(msg)
        except Exception:
            pass
        
        # Only render if overlay is enabled to reduce CPU usage
        if self.overlay_data.get('enabled', False):
            self.render()
        
        # Schedule next poll (100ms = 10 FPS for overlay updates - reduces flicker)
        self.root.after(100, self.poll_queue)

    def handle_message(self, msg):
        cmd = msg.get('cmd')
        if cmd == 'update':
            self.overlay_data = msg.get('data', {})
        elif cmd == 'toggle_click':
            self.set_click_through(msg.get('state', True))
        elif cmd == 'quit':
            self.on_close()
        elif cmd == 'show':
            self.root.deiconify()
            self.root.attributes('-topmost', True)
        elif cmd == 'hide':
            self.root.withdraw()

    def render(self):
        self.canvas.delete("all")
        
        if not self.overlay_data.get('enabled', False):
            return

        # Draw Snap Rect (GD Window Boundary)
        snap = self.overlay_data.get('snap_rect')
        if snap:
            x, y, w, h = snap
            # Draw border
            self.canvas.create_rectangle(x, y, x+w, y+h, outline="#00FF00", width=2, tags="snap")
            self.canvas.create_text(x+10, y+10, text="GD WINDOW", fill="#00FF00", anchor="nw", font=("Arial", 10, "bold"))

        # Draw Click Regions
        regions = self.overlay_data.get('regions', [])
        colors = self.overlay_data.get('colors', ['#FF0000'])
        
        for i, reg in enumerate(regions):
            rx, ry, rw, rh = reg
            color = colors[i % len(colors)]
            # Semi-transparent fill simulation (outline only for performance in Tkinter)
            self.canvas.create_rectangle(rx, ry, rx+rw, ry+rh, outline=color, width=2, stipple="gray50")
            self.canvas.create_text(rx+5, ry+5, text=f"Region {i+1}", fill=color, anchor="nw", font=("Arial", 8))

        # Draw Text Info
        text_info = self.overlay_data.get('text', "")
        if text_info:
            self.canvas.create_text(100, 100, text=text_info, fill="#FFFFFF", anchor="nw", font=("Consolas", 12))

    def on_close(self):
        try:
            self.output_queue.put({'cmd': 'overlay_closed'})
        except Exception:
            pass
        self.root.destroy()
        sys.exit(0)

def run_overlay(input_q, output_q):
    app = OverlayEngine(input_q, output_q)
    app.root.mainloop()

if __name__ == "__main__":
    # Standalone test mode if run directly without args (for debugging)
    if len(sys.argv) < 2:
        print("Overlay Engine started in standalone debug mode.")
        # Create dummy queues for testing
        q_in = Queue()
        q_out = Queue()
        run_overlay(q_in, q_out)
    else:
        # Production mode: queues passed via pickle (handled by multiprocessing spawn)
        # Note: In this simple structure, we rely on the parent to manage the queues 
        # and this script is spawned as a target function usually. 
        # However, for a separate .py file execution, we need a handshake.
        # Since multiprocessing.Process(target=...) passes args differently than CLI,
        # this block is technically for direct execution debugging.
        # The main script will call run_overlay directly in a Process target.
        pass
