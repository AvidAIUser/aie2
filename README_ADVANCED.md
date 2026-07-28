# Advanced Humanized Clickbot for Geometry Dash v3.0

A sophisticated clickbot with GUI interface, intelligent obstacle-based clicking, level autocomplete with learning, and humanization features.

## Features

### Core Functionality
- **GUI Interface**: Easy-to-use graphical interface with Start/Stop controls
- **Intelligent Clicking**: No more random clicking! The bot intelligently times clicks based on:
  - Predicted obstacle positions
  - Learned patterns from previous attempts
  - Game state awareness
- **Multiple Click Modes**:
  - `smart`: Intelligently times clicks based on predicted obstacles (RECOMMENDED)
  - `rhythm`: Clicks at regular intervals based on typical GD patterns
  - `learned`: Uses only previously learned successful click positions
  - `spam`: Constant clicking (legacy mode)

### Learning System
- **Click Recording**: Every click is recorded during attempts with position and timing data
- **Pattern Learning**: Successful clicks are saved and associated with specific positions
- **Confidence Building**: Patterns gain confidence with repeated success
- **Autocomplete**: Over multiple attempts, the bot builds a complete solution
- **Playback**: Replay your most successful run using learned patterns
- **Persistence**: All data is saved to disk between sessions

### Humanization Features
- **Reaction Time Variance**: Makes timing less robotic and more human-like
- **Jitter**: Adds subtle mouse movement variations
- **Misclick Simulation**: Optional chance to simulate human error
- **Fatigue System**: Performance degrades over long sessions
- **Adaptation**: Bot learns and adapts to level difficulty

### Statistics & Analytics
- Real-time progress tracking
- Attempt history with completion rates
- Best run tracking
- Learned pattern visualization
- Export runs to JSON

## Installation

```bash
pip install numpy pyautogui pywin32 psutil
```

**Note**: This tool is designed for Windows (requires pywin32 for window detection).

## Usage

### Quick Start
1. Launch Geometry Dash and enter a level
2. Run the clickbot: `python gd_clickbot_advanced.py`
3. Click "Start Clickbot" in the GUI
4. The bot will automatically detect the game window and start clicking intelligently

### GUI Controls
- **Start Clickbot**: Begin automated clicking
- **Stop**: Stop the clickbot
- **New Attempt**: Start recording a new attempt manually
- **Playback Best**: View information about your best recorded run
- **Level ID**: Set a custom identifier for the current level
- **Click Mode**: Choose between smart, rhythm, learned, or spam modes
- **Game Mode**: Select auto-detection or force a specific mode (cube, ship, ball, ufo, wave)
- **Humanization Settings**: Adjust reaction time, jitter, misclick chance, etc.

### Statistics Panel
The statistics panel shows:
- Current game state and player position
- Fatigue level
- Total attempts and completion rate
- Best and average progress
- Total clicks recorded
- Number of learned patterns

## How It Works

### Smart Clicking Algorithm
1. **Obstacle Prediction**: Generates predicted obstacle positions based on typical GD patterns (150-250 pixel spacing)
2. **Reaction Timing**: Calculates when to click based on distance to obstacle and human reaction time
3. **Learning Integration**: Checks if there's a learned pattern at the current position
4. **Humanization**: Applies jitter, reaction variance, and optional misclicks

### Learning Process
1. **Recording**: During each attempt, every click is recorded with:
   - Timestamp
   - Player X/Y position
   - Game mode
   - Frame number
2. **Success Marking**: When an attempt ends, clicks that contributed to progress are marked as successful
3. **Pattern Creation**: Successful clicks create or update learned patterns at their positions
4. **Confidence Building**: Patterns used successfully multiple times gain higher confidence
5. **Playback Generation**: High-confidence patterns (≥70%) are used to generate optimal click sequences

### File Storage
All data is saved to `~/.gd_clickbot/attempts.json`:
- Complete attempt history
- Learned patterns with confidence scores
- Best run for each level

## Configuration Options

### Humanization Settings
- **Base Reaction (ms)**: Average reaction time (default: 45ms)
- **Reaction Variance (ms)**: How much reaction time varies (default: 25ms)
- **Misclick Chance (%)**: Probability of missing a click (default: 1.5%)
- **Jitter Amplitude (px)**: Mouse movement variation (default: 1.5px)
- **Fatigue Rate**: How quickly performance degrades (default: 0.0008)
- **Adaptation Rate**: How quickly the bot learns (default: 0.05)

### Click Interval
- Controls minimum time between clicks
- Default: 0.017s (~60 FPS)
- Lower values = faster clicking but less human-like

## Advanced Features

### Multiple Game Modes
The bot supports all GD game modes:
- **Cube**: Standard jumping
- **Ship**: Hold-to-fly mechanics
- **Ball**: Gravity-flipping jumps
- **UFO**: Tap-to-jump in air
- **Wave**: Rapid clicking for zigzag movement
- **Robot**: Charge-and-release jumps
- **Spider**: Orb-clicking mechanics

### Auto-Restart
When the player dies, the bot automatically:
1. Records the death and progress
2. Saves the attempt
3. Waits 0.5 seconds
4. Starts a new attempt

This allows for unattended practice sessions.

### Export/Import
- Export all attempts and learned patterns to JSON
- Share runs with others
- Backup your progress
- Import runs from other players

## Tips for Best Results

1. **Use Smart Mode**: The `smart` mode provides the best balance of intelligence and reliability
2. **Let It Learn**: Run multiple attempts to build up learned patterns
3. **Adjust Humanization**: Lower values for more precision, higher for more human-like behavior
4. **Set Level IDs**: Use descriptive level IDs to organize your runs
5. **Monitor Progress**: Watch the statistics to see improvement over time
6. **Export Regularly**: Backup your learned patterns periodically

## Troubleshooting

### "Could not find Geometry Dash window"
- Make sure Geometry Dash is running before starting the clickbot
- Ensure the window title contains "Geometry Dash"
- Try running as administrator

### Clicking Too Fast/Slow
- Adjust the click interval in the GUI
- Lower values = faster, higher = slower
- Typical values: 0.015-0.020s

### Not Learning Patterns
- Make sure you're making progress (even small amounts)
- Check that "use_learned_patterns" is enabled
- Verify clicks are being recorded in statistics

### Bot Stops Unexpectedly
- Check for game crashes or pauses
- Ensure the game window remains open
- Look for error messages in the status bar

## Disclaimer

This tool is intended for:
- Practicing difficult levels
- Creating level showcases
- Testing custom levels
- Educational purposes

Use responsibly and respect server rules. Some online platforms may prohibit automated gameplay.

## License

MIT License - Feel free to modify and distribute.

## Contributing

Contributions welcome! Areas for improvement:
- Better memory reading for precise player position
- Support for more game modes
- Improved obstacle prediction algorithms
- Visual overlay showing predicted obstacles
- Integration with Discord/webhook notifications
