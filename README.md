# ⚡ GD Clickbot Overlay v4.0

**Professional In-Game Automation for Geometry Dash**

A sophisticated, overlay-based clickbot that runs **directly on top of Geometry Dash** - no split-screening required! Features advanced color detection, real-time monitoring, and a modern cyberpunk UI.

![Version](https://img.shields.io/badge/version-4.0.0-cyan)
![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)

---

## ✨ Key Features

### 🎯 Core Functionality
- **Seamless In-Game Overlay**: Runs directly on top of Geometry Dash
- **Click-Through Mode**: Mouse passes through menu to game when enabled
- **Always-on-Top**: Stays visible above the game window
- **Auto-Positioning**: Automatically finds and positions over GD window
- **Color-Based Detection**: Triggers clicks when target color appears
- **Real-Time CPS Monitoring**: Live clicks-per-second display with LED indicator

### 🎨 User Experience
- **Cyberpunk Aesthetic**: Modern dark theme with cyan accents
- **Compact Design**: 360x540 borderless window (minimal screen obstruction)
- **Draggable**: Reposition anywhere when click-through is disabled
- **Semi-Transparent**: 95% opacity for subtle presence
- **Hidden from Taskbar**: Clean, professional appearance

### ⚙️ Configuration
- **Adjustable Click Delay**: 1-100ms (slider control)
- **Color Tolerance**: 0-100 sensitivity range
- **Region Selection**: Interactive screen area picker
- **Color Picker**: Sample colors from your selected region
- **Auto-Save**: All settings persist between sessions

### 🛡️ Safety Features
- **Panic Stop (F12)**: Instant bot shutdown via global hotkey
- **Visual Status Indicator**: LED shows running state (green=active, gray=stopped)
- **Minimum Click Gap**: Prevents accidental spam-clicking

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the repository
cd gd-clickbot

# Install dependencies
pip install -r requirements.txt
```

**Required packages:**
- `tkinter` (usually included with Python)
- `numpy`
- `opencv-python` (cv2)
- `Pillow` (PIL)
- `pynput`
- `pywin32` (win32gui, win32con)

### 2. Running

```bash
python gd_clickbot_unified.py
```

The overlay will launch and automatically position itself over your Geometry Dash window.

---

## 📖 How to Use

### Basic Workflow

1. **Launch the overlay** - It should auto-position over GD
2. **Enable Click-Through** (default: ON) - Allows clicking GD through the menu
3. **Select Region** - Click "🎯 Region" and drag to select the detection area
4. **Pick Color** - Click "🖌️ Color" to sample the trigger color from your region
5. **Adjust Settings** - Fine-tune delay and tolerance as needed
6. **Start Bot** - Press "▶ START BOT" to begin automation
7. **Stop** - Press "⏹ STOP BOT" or hit **F12** for emergency stop

### Overlay Controls

| Control | Function |
|---------|----------|
| **☑ CLICK-THROUGH: ON/OFF** | Toggle whether mouse clicks pass through to GD |
| **▶ START BOT** | Begin color-detection automation |
| **⏹ STOP BOT** | Stop automation |
| **🎯 Region** | Open region selection overlay |
| **🖌️ Color** | Pick color from center of selected region |
| **Click Delay Slider** | Adjust time between clicks (1-100ms) |
| **Tolerance Slider** | Adjust color detection sensitivity (0-100) |

### Tips for Best Results

- **Region Selection**: Choose a small, specific area where your trigger color appears
- **Color Choice**: Pick a unique color that only appears when you need to click
- **Tolerance**: Start low (20-30), increase if detection is inconsistent
- **Click Delay**: Match to your level's rhythm (17ms = 60 FPS, 10ms = 100 CPS max)
- **Positioning**: If auto-position fails, disable click-through and drag manually

---

## 🔧 Advanced Features

### Configuration File

Settings are saved to `gd_clickbot_config.json`:

```json
{
  "click_delay": 0.017,
  "target_color": [255, 255, 255],
  "color_tolerance": 30,
  "region": [100, 200, 50, 50]
}
```

You can edit this file directly for precise values.

### Global Hotkeys

| Key | Action |
|-----|--------|
| **F12** | Panic stop (immediately stops bot) |

### Window Behavior

The overlay uses Windows API features:
- `WS_EX_TRANSPARENT`: Makes window click-through
- `WS_EX_TOPMOST`: Keeps window always on top
- `WS_EX_TOOLWINDOW`: Hides from taskbar
- `overrideredirect(True)`: Removes window borders/title bar

---

## 🆕 What's New in v4.0

### Major Improvements
- ✅ **Complete Code Rewrite**: Cleaner, more maintainable architecture
- ✅ **Enhanced Overlay System**: More reliable click-through and positioning
- ✅ **Real-Time CPS Display**: Live clicks-per-second monitoring
- ✅ **LED Status Indicator**: Visual running state (green/gray)
- ✅ **Improved GD Detection**: Multiple fallback methods for finding game window
- ✅ **Better Auto-Positioning**: Smarter placement at top-right of GD window
- ✅ **Cyberpunk Theme**: Modern dark UI with cyan accents
- ✅ **Compact Design**: Reduced footprint (360x540)
- ✅ **Config Class**: Centralized configuration management
- ✅ **Auto-Save on Changes**: Settings persist immediately

### Technical Enhancements
- Removed legacy code (HumanizationConfig, ClickBotEngine classes simplified)
- Consolidated into single, streamlined `GDClickbotOverlay` class
- Improved error handling throughout
- Better thread management for bot loop
- Optimized screen capture performance
- Cleaner separation of concerns (UI, logic, Windows API)

---

## 🐛 Troubleshooting

### Overlay doesn't appear over GD
- Make sure Geometry Dash is running first
- Try manually dragging the overlay (disable click-through first)
- Check if GD window title contains "Geometry Dash" or uses Unity

### Clicks not registering
- Ensure click-through is ON (green button)
- Verify your selected region actually contains the target color
- Lower the tolerance value for stricter detection
- Make sure GD window is in focus

### Can't interact with the menu
- Toggle click-through OFF to make the menu interactive
- The menu is only draggable when click-through is OFF

### Region/color selection not working
- Make sure you have proper permissions for screen capture
- Try running as administrator if issues persist

### High CPU usage
- Reduce the scan region size
- Increase click delay slightly
- Close other resource-intensive applications

---

## ⚠️ Disclaimer

This tool is intended for:
- Practice and skill development
- Accessibility assistance
- Educational purposes (learning computer vision, automation)

**Use responsibly.** Excessive automation may violate Geometry Dash's terms of service or diminish the intended challenge of the game. Always respect community guidelines and compete fairly.

---

## 📄 License

This project is provided as-is for educational purposes.

---

## 🙏 Credits

Built with:
- **Python 3.x**
- **Tkinter** (GUI framework)
- **OpenCV** (computer vision)
- **Pillow** (image processing)
- **pynput** (input control)
- **pywin32** (Windows API integration)

---

**Enjoy! 🎮** If you encounter issues or have feature requests, feel free to contribute improvements.
