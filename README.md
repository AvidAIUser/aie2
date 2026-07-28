# AI-Assisted Humanized Clickbot for Geometry Dash v2.0

![Version](https://img.shields.io/badge/version-2.0-blue)

Advanced clickbot that injects sophisticated human imperfections using AI-driven pattern prediction, multi-layer jitter synthesis, and behavioral biometrics. Now includes **rhythm-based clicking** that works without memory offsets!

## 🚀 New Features in v2.0

### AI & Machine Learning
- **LSTM-Based Timing Prediction**: Uses PyTorch LSTM networks to predict and adapt to timing patterns
- **Simple Pattern Predictor**: Fallback linear predictor when PyTorch is unavailable
- **Dynamic Adaptation**: Multiple learning strategies including trend detection and statistical analysis

### Advanced Humanization
- **Multi-Layer Jitter Synthesis**:
  - Perlin noise for smooth continuous movement
  - Fourier series for periodic tremor
  - Biomechanical tremor (8-12Hz physiological simulation)
  - Micro-saccades for tiny rapid adjustments
- **Behavioral Fingerprinting**: Unique session-specific behavioral profile
- **Pressure Curve Simulation**: Realistic mouse pressure during clicks (gaussian/linear/exponential)
- **Warmup & Fatigue Dynamics**: Non-linear fatigue with cooldown benefits

### Context Awareness
- **Game State Detection**: Automatically detects menu, playing, paused, dead states
- **Difficulty Adaptation**: Adjusts behavior based on perceived difficulty level
- **Focus Mode**: Tighter timing and reduced jitter during challenging sections

### Analytics & Persistence
- **Real-Time Analytics Dashboard**: Live statistics tracking
- **Session Persistence**: Saves and loads behavioral profiles between sessions
- **Data Export**: Optional export of detailed click analytics
- **Success Streak Tracking**: Monitors performance over time

### Misclick System
- **Multiple Misclick Types**: hesitation, early_release, late_release, double_click, triple_click
- **Smart Correction Behavior**: Attempts to correct obvious misclicks
- **Click-Type Awareness**: Different misclick probabilities for rapid vs precision clicks

### Rhythm Mode (NEW!)
- **No Memory Offsets Required**: Works immediately without finding GD memory addresses
- **Predictive Obstacle Detection**: Estimates obstacle positions based on typical GD patterns
- **Adaptive Timing**: Adjusts click timing based on game mode (cube, ship, UFO, ball)

## Installation

```bash
pip install -r requirements.txt
```

### Optional: Full AI Features
For LSTM-based prediction:
```bash
pip install torch>=2.0.0
```

## Usage

### GUI Mode (Recommended)
```bash
python humanized_clickbot.py
```
A graphical interface will open where you can:
- Start/Stop the clickbot with button clicks
- Select click mode (rhythm/obstacle/spam)
- Adjust click interval
- Configure humanization settings
- View status and helpful tips

### Basic Command Line Usage
```bash
python humanized_clickbot.py
```

### Programmatic Usage
```python
from humanized_clickbot import HumanizedClickbot, HumanizationConfig

# Create custom configuration
config = HumanizationConfig(
    base_reaction_time=45.0,
    reaction_time_variance=25.0,
    misclick_probability=0.015,
    jitter_amplitude=1.5,
    fatigue_rate=0.0008,
    use_lstm_prediction=True,  # Enable LSTM if available
    enable_analytics=True,
)

# Initialize and start
bot = HumanizedClickbot(config)
bot.start()

# Choose your mode:
# 'obstacle' - Smart obstacle-based clicking (requires memory access)
# 'rhythm' - Rhythm-based clicking (works without memory access) RECOMMENDED
# 'spam' - Constant clicking at interval
bot.auto_click(click_interval=0.017, mode='rhythm')
bot.stop()
```

### Click Modes Explained

#### Rhythm Mode (Recommended for most users)
```python
bot.auto_click(click_interval=0.017, mode='rhythm')
```
- **No setup required** - works immediately
- Predicts obstacle positions based on typical GD patterns
- Adapts to different game modes (cube, ship, UFO, ball)
- Best for regular levels with consistent obstacle spacing

#### Obstacle Mode (Advanced)
```python
bot.auto_click(click_interval=0.017, mode='obstacle')
```
- Requires GD memory offsets to be configured
- Reads actual obstacle positions from game memory
- More precise but requires Cheat Engine setup
- Best for users who can find their GD version's offsets

#### Spam Mode (Legacy)
```python
bot.auto_click(click_interval=0.017, mode='spam')
```
- Constant clicking at specified interval
- Old behavior, less human-like
- Useful for testing or specific scenarios

## Configuration Options

### Core Timing Parameters
| Parameter | Description | Default |
|-----------|-------------|---------|
| `base_reaction_time` | Base delay before clicking (ms) | 50.0 |
| `reaction_time_variance` | Standard deviation (ms) | 30.0 |
| `timing_precision` | Consistency (1.0=robot, 0.5=human) | 0.85 |

### Misclick System
| Parameter | Description | Default |
|-----------|-------------|---------|
| `misclick_probability` | Base chance of misclick | 0.02 |
| `double_click_probability` | Accidental double-click chance | 0.01 |
| `triple_click_probability` | Accidental triple-click chance | 0.002 |
| `early_release_probability` | Releasing too soon | 0.015 |
| `late_release_probability` | Holding too long | 0.025 |
| `correction_behavior` | Auto-correct misclicks | True |

### Jitter Configuration
| Parameter | Description | Default |
|-----------|-------------|---------|
| `jitter_amplitude` | Mouse movement noise (pixels) | 2.0 |
| `jitter_frequency` | Base oscillation speed (Hz) | 15.0 |
| `perlin_octaves` | Perlin noise detail levels | 4 |
| `biomechanical_tremor` | Physiological tremor intensity | 0.3 |
| `micro_saccades` | Enable tiny rapid movements | True |

### AI & Learning
| Parameter | Description | Default |
|-----------|-------------|---------|
| `use_lstm_prediction` | Enable LSTM prediction | Auto |
| `adaptation_rate` | Learning speed | 0.05 |
| `pattern_memory_size` | Click history size | 200 |
| `prediction_horizon` | Frames to predict ahead | 10 |

### Anti-Detection
| Parameter | Description | Default |
|-----------|-------------|---------|
| `session_uniqueness` | Variation between sessions | 0.15 |
| `behavioral_drift` | Gradual change over session | 0.02 |
| `randomize_seeds` | Unique random seeds per session | True |

## How It Works

### 1. Behavioral Fingerprinting
Each session generates a unique behavioral profile including:
- Reaction time distribution
- Jitter frequency weights
- Movement arc preferences
- Hesitation patterns

### 2. Multi-Layer Jitter Generation
```
Jitter = Perlin_Noise + Fourier_Series + Biomechanical_Tremor + Micro_Saccades + Gaussian_Noise
```

### 3. Pattern Learning Pipeline
1. Collect inter-click intervals
2. Statistical analysis (mean, std, trends)
3. LSTM/Simple predictor training
4. Adaptive offset calculation
5. Real-time adjustment

### 4. Context-Aware Behavior
- **Menu State**: Slower, more jittery, higher hesitation
- **Playing State**: Normal behavior
- **Focus Mode** (high difficulty): Tighter timing, reduced jitter

### 5. Fatigue Dynamics
```
Fatigue_Increase = base_rate * (1 + current_fatigue)
Recovery = base_recovery * cooldown_multiplier (after rests > 5s)
```

### 6. Rhythm-Based Obstacle Prediction (NEW!)
When memory access isn't available:
1. Estimate player position from last known state
2. Predict next obstacle based on typical GD spacing (150-250 pixels)
3. Add variation to simulate different level patterns
4. Time clicks based on predicted obstacle distance

## Architecture

```
HumanizedClickbot
├── BehavioralFingerprint (unique session profile)
├── PatternPredictor (LSTM or Simple)
├── ClickAnalytics (real-time stats)
├── JitterGenerator (multi-layer synthesis)
├── GameStateDetector (context awareness)
├── ObstaclePredictor (rhythm-based detection)
└── SessionManager (persistence)
```

## API Reference

### Main Class Methods
```python
bot.find_geometry_dash()      # Detect game process
bot.open_process()            # Open with memory access
bot.detect_game_state()       # Get current state
bot.adapt_to_difficulty(f)    # Adjust for difficulty
bot.auto_click(interval, mode) # Start auto-clicking
bot.start()                   # Initialize
bot.stop()                    # Cleanup
```

### Memory Access
```python
bot.read_memory(address, size)
bot.write_memory(address, value, size)
bot.scan_pattern(pattern_bytes)
```

### Analytics
```python
stats = bot.analytics.get_stats()
# Returns: total_clicks, misclicks, avg_reaction, streak, etc.
```

## Performance Metrics

The analytics system tracks:
- Total clicks and misclick rate
- Average/min/max reaction times
- Jitter magnitude (exponential moving average)
- Success streaks (current and best)
- Clicks per second
- Fatigue history

## Legal Notice

⚠️ **Use responsibly and only in single-player modes.** Respect game terms of service. This tool is intended for educational purposes and legitimate accessibility use cases.

## Troubleshooting

### "PyTorch not available"
Install PyTorch for LSTM features, or the bot will use the simple predictor automatically.

### "Geometry Dash not found"
Ensure the game is running before starting the bot.

### High misclick rate
Reduce `misclick_probability` in the config for more consistent clicking.

### Can't find memory offsets
Use **rhythm mode** which doesn't require memory access:
```python
bot.auto_click(click_interval=0.017, mode='rhythm')
```

### Finding Memory Offsets (Advanced)
If you want to use obstacle mode with memory access:
1. Download Cheat Engine
2. Attach to GeometryDash.exe
3. Find player X coordinate (float value that changes as you move)
4. Note the address and offset chain
5. Update `GD_BASE_ADDRESS` and offset constants in the code

## Contributing

Contributions welcome! Areas for improvement:
- Enhanced screen-based obstacle detection (template matching)
- Additional game state detection methods
- More sophisticated ML models
- Enhanced anti-detection measures
- GUI interface

## License

MIT License - See LICENSE file for details.