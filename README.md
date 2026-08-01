# GD Overlay Clickbot - In-Game Menu Edition

![Version](https://img.shields.io/badge/version-3.1-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

**Revolutionary overlay-based clickbot that runs INSIDE Geometry Dash!** No more split-screening or alt-tabbing - the menu overlays directly on top of your game with click-through functionality.

## 🎯 Key Features

### ✨ In-Game Overlay (NEW!)
- **Auto-positioning**: Automatically positions itself over your GD window on startup
- **Click-through toggle**: Enable to play normally, disable to interact with menu
- **Always on top**: Stays visible during gameplay
- **Semi-transparent**: 85% opacity for minimal visual obstruction
- **Borderless design**: No title bar or window decorations
- **Hidden from taskbar**: Clean, unobtrusive presence
- **Compact UI**: Optimized 350x480 footprint

### 🧠 Smart Detection & Learning
- **Screen-based obstacle detection**: No memory offsets required!
- **Auto-learning**: Saves successful click patterns from good runs
- **Playback mode**: Replay learned patterns perfectly
- **Rhythm mode**: Fixed interval clicking for consistent levels

### 👤 Advanced Humanization
- **Reaction time simulation**: Configurable delay with variance
- **Mouse jitter**: Natural micro-movements
- **Misclick chance**: Occasional missed clicks for authenticity
- **Fatigue system**: Performance degrades slightly over time

## Installation

```bash
pip install -r requirements.txt
```

### Requirements
- Python 3.8+
- Windows (for overlay functionality)
- Geometry Dash running in windowed or fullscreen mode

## Usage

### Quick Start
1. **Launch Geometry Dash** and start a level
2. **Run the clickbot**: `python gd_clickbot_unified.py`
3. **Menu auto-positions**: Appears at top-right of GD window
4. **Configure settings**: Set scan region and capture ground color
5. **Enable click-through**: Toggle button turns green
6. **Press START**: Begin automated playing

### Overlay Controls

| Button | Function |
|--------|----------|
| ☑/☐ Click-Through | Toggle whether clicks pass through to GD |
| ▶ START | Begin the clickbot |
| ■ STOP | Stop immediately |
| ⏸ PAUSE | Pause/resume without stopping |

### Operation Modes

#### Smart Mode (Detect & Learn)
- Uses screen color detection to identify obstacles
- Automatically learns successful click timings
- Saves patterns after successful runs (>2 seconds)
- Best for learning new levels

#### Rhythm Mode
- Clicks at fixed intervals
- Good for levels with consistent spacing
- No setup required

#### Playback Mode
- Replays previously learned click patterns
- Perfect for levels you've already learned
- Loads automatically from saved data

### Setup Guide

1. **Set Scan Region**:
   - Click "📍 Region"
   - Click two points: top-left then bottom-right of detection area
   - Recommended: Area just ahead of player showing incoming obstacles

2. **Capture Ground Color**:
   - Position mouse over the ground/wall color in GD
   - Click "🎨 Color"
   - Click once to sample the color
   - The bot detects obstacles by color differences

3. **Enable Click-Through**:
   - Click the "☐ Click-Through: OFF" button
   - Status changes to "☑ Click-Through: ON" (green)
   - Now your clicks go through to GD while overlay stays visible

4. **Start Playing**:
   - Press ▶ START
   - Ensure click-through is ON
   - Let the bot play!

## Configuration

### Settings Explained

| Setting | Description | Recommended |
|---------|-------------|-------------|
| Interval | Time between clicks (rhythm mode) | 0.017s (60 FPS) |
| Reaction (ms) | Delay before clicking obstacle | 40-60ms |
| Jitter (px) | Mouse movement randomness | 1.0-3.0px |

### Tips for Best Results

1. **Scan Region**: Place it where you can see obstacles coming, but not too far ahead
2. **Ground Color**: Sample a color that's consistent (not spikes/triangles)
3. **Reaction Time**: Lower = faster reactions, but too low looks suspicious
4. **Jitter**: Higher = more human-like, but too high affects accuracy

## How It Works

### Screen Detection
1. Continuously screenshots the scan region
2. Compares current colors to captured ground color
3. When difference exceeds threshold → obstacle detected!
4. Triggers click after reaction delay

### Pattern Learning
1. Records all click timings during a run
2. If run lasts >2 seconds, assumes clicks were successful
3. Saves click frame offsets to library
4. Playback mode replays these exact timings

### Overlay Technology
- Uses Windows API for layered windows
- WS_EX_TRANSPARENT allows click-through
- WS_EX_TOPMOST keeps it above GD
- WS_EX_TOOLWINDOW hides from taskbar
- Alpha blending for transparency
- Auto-detects GD window position

## File Structure

```
gd_clickbot_unified.py    # Main application
requirements.txt          # Dependencies
README.md                # This file
~/.gd_clickbot/          # Saved data directory
  └── learned_clicks.json # Your learned patterns
```

## Troubleshooting

### Overlay not appearing correctly?
- Make sure you're on Windows (overlay requires Win32 API)
- Try running as administrator
- Check if GD is blocking overlays (shouldn't, but some anti-cheat might)

### Click-through not working?
- Ensure the toggle button shows "ON" (green)
- Some games may block click-through; try windowed mode
- Restart the application

### Bot not detecting obstacles?
- Verify ground color is captured (check log for ✓ messages)
- Adjust scan region to show more ground/wall
- Make sure obstacle actually changes the color significantly

### Learned patterns not saving?
- Runs must last >2 seconds to save
- Check `~/.gd_clickbot/learned_clicks.json` exists
- Look for "✓ Session clicks saved" in the log

## Legal Notice

⚠️ **Use responsibly and only in single-player modes.** Respect Geometry Dash's terms of service. This tool is intended for educational purposes and accessibility use cases.

## Credits

Built upon the foundation of the AI-Assisted Humanized Clickbot v2.0  
Enhanced with in-game overlay technology for seamless integration

## Changelog

### v3.1 (Current)
- ✨ Auto-positioning: Menu now finds and positions over GD window automatically
- ✨ Hidden from taskbar for cleaner appearance
- ✨ More compact UI design (350x480)
- ✨ Improved click-through toggle with better visual feedback
- ✨ Streamlined helper buttons (Region, Color, Clear)
- ✨ Enhanced logging with checkmark indicators
- ✨ Better font sizing throughout for readability

### v3.0
- Initial overlay implementation
- Click-through functionality
- Semi-transparent borderless design

## License

MIT License - See LICENSE file for details.