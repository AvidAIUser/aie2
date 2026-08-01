# 🎮 GD Clickbot Overlay v5.0 - Ultimate Edition

**Professional in-game automation tool for Geometry Dash**  
Runs seamlessly as an overlay directly on top of your game - no split-screening needed!

![Version](https://img.shields.io/badge/version-5.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Python](https://img.shields.io/badge/python-3.8+-green)

---

## ✨ Key Features

### 🎯 Core Functionality
- **Seamless In-Game Overlay**: Runs directly on top of Geometry Dash
- **Ghost Mode**: Click-through technology lets you play while menu is visible
- **Smart Auto-Positioning**: Automatically snaps to your GD window on launch
- **Real-Time Monitoring**: Live CPS counter and latency display
- **Color-Based Automation**: Detects colors and auto-clicks with precision

### 🎨 User Interface
- **Modern Cyberpunk Design**: Dark theme with neon cyan accents
- **Live Mini-Preview**: See exactly what the bot is monitoring
- **Status LED Indicator**: Visual feedback (green = running, gray = stopped)
- **Intelligent Hover System**: 
  - Hover over menu → becomes interactive (cursor appears)
  - Move away → becomes ghost-like (clicks pass through to game)
- **Draggable Anywhere**: Reposition by dragging when interactive

### ⚙ Configuration
- **Adjustable Click Delay**: 1-100ms precision control
- **Color Tolerance Slider**: Fine-tune detection sensitivity (0-100)
- **Region Selection**: Monitor specific screen areas
- **Color Sampling**: Pick colors directly from live feed
- **Profile System**: Save/load configurations instantly
- **Auto-Save Settings**: Changes persist immediately

---

## 🚀 Quick Start

### Installation

```bash
# Clone or download the repository
cd gd-clickbot

# Install dependencies
pip install -r requirements.txt
```

### Requirements
- Python 3.8+
- Windows OS (for overlay functionality)
- Dependencies: `mss`, `numpy`, `opencv-python`, `Pillow`, `pynput`, `pywin32`, `screeninfo`

### Running

```bash
python gd_clickbot_unified.py
```

The overlay will automatically position itself at the top-right corner of your Geometry Dash window!

---

## 📖 Usage Guide

### Step 1: Launch & Position
1. Start Geometry Dash
2. Run `python gd_clickbot_unified.py`
3. Menu auto-snaps to GD window (or drag manually if GD not detected)

### Step 2: Configure Region
1. Hover over the menu to make it interactive
2. Click **"🎯 Select Region"**
3. By default, selects center screen (edit `gd_clickbot_config.json` for precision)
4. Position the region over your target area in GD

### Step 3: Sample Color
1. Start the bot temporarily to get live feed
2. Click **"🎨 Sample Color"** to pick the center pixel color
3. Or manually set RGB values in config

### Step 4: Adjust Settings
- **Click Delay**: Lower = faster clicks (15ms recommended)
- **Color Tolerance**: Higher = more lenient detection (30 default)

### Step 5: Activate
1. Click **"▶ START BOT"**
2. Move your cursor AWAY from the menu (activates ghost mode)
3. Bot will auto-click when target color is detected
4. Hover back over menu to stop/edit

---

## 🎛 Interface Overview

```
┌─────────────────────────────┐
│ 🎮 GD CLICKBOT v5    [LED] │ ← Status indicator
├─────────────────────────────┤
│ ┌─────────────────────┐     │
│ │  Live Feed Preview  │     │ ← Real-time monitor
│ └─────────────────────┘     │
├─────────────────────────────┤
│ CPS: 0.0      Latency: 0ms  │ ← Performance stats
├─────────────────────────────┤
│   ▶ START BOT               │ ← Toggle button
├─────────────────────────────┤
│ ⚙ Configuration             │
│ Click Delay (ms) [====|==]  │ ← Adjustable slider
│ Color Tolerance  [===|===]  │ ← Sensitivity control
├─────────────────────────────┤
│ [🎯 Select Region] [🎨 Color]│ ← Action buttons
├─────────────────────────────┤
│ [💾 Save]      [📂 Load]    │ ← Profile management
└─────────────────────────────┘
   Hover to Interact | Play
```

---

## 🔧 Advanced Configuration

### Manual Config Editing
Edit `gd_clickbot_config.json` directly:

```json
{
  "click_delay": 15,
  "color_tolerance": 30,
  "target_color": [255, 255, 255],
  "region": [960, 540, 100, 100],
  "opacity": 240,
  "theme_color": "#00ffff"
}
```

### Region Format
`[x, y, width, height]` - Coordinates from top-left of primary monitor

### Profile System
- **Save**: Creates `profile_<name>.json` with current settings
- **Load**: Shows available profiles (manual selection via file browser)

---

## 🛠 Troubleshooting

### Menu doesn't snap to GD
- Ensure Geometry Dash window title contains "Geometry Dash"
- Manually drag menu to desired position
- Run as Administrator if needed

### Clicks not registering
- Verify region is positioned correctly
- Check live preview shows target area
- Increase color tolerance if detection is too strict
- Ensure GD is in focus/windowed mode

### Menu blocks gameplay
- Move cursor away from menu (activates click-through)
- Menu becomes transparent and non-interactive
- Reposition to corner of screen

### High CPU usage
- Reduce capture rate in code (currently ~120 FPS)
- Decrease monitored region size
- Close unnecessary background apps

---

## ⚠ Safety & Ethics

- **Use responsibly**: For personal practice and learning only
- **Check server rules**: Some platforms prohibit automation
- **Not for online leaderboards**: Respect fair play policies
- **Single-player only**: Intended for offline practice modes

---

## 📝 Changelog

### v5.0 (Current) - Ultimate Edition
✨ **Major Overhaul**
- Complete codebase rewrite for stability
- Intelligent hover-to-interact system
- Enhanced ghost mode with smooth transitions
- Live mini-preview window
- Real-time CPS and latency monitoring
- Profile save/load system
- Improved cyberpunk UI design
- Better error handling throughout
- Optimized threading architecture

### v4.0
- Added auto-positioning over GD window
- Real-time CPS display
- LED status indicator
- Modern dark theme
- Centralized config system

### v3.1
- Hidden from taskbar
- Compact UI redesign
- Better click-through toggle

### v3.0
- Initial overlay implementation
- Click-through capability
- Always-on-top positioning

---

## 📄 License

MIT License - Free for personal use and modification

---

## 💡 Tips & Tricks

1. **Optimal Placement**: Position menu in corner opposite your mouse hand
2. **Color Selection**: Use unique colors in level for reliable detection
3. **Delay Tuning**: Start at 15ms, adjust based on level requirements
4. **Tolerance Sweet Spot**: 25-35 works for most cases
5. **Practice Mode**: Perfect for practicing consistent timing

---

**Enjoy automated practice sessions! 🎵**
