# AI-Assisted Humanized Clickbot for Geometry Dash

This clickbot injects natural human imperfections to make automated clicking appear more human-like.

## Features

- **Variable Reaction Times**: Gaussian-distributed reaction time variations
- **Mouse Jitter**: Natural hand tremor simulation using multi-frequency sine waves
- **Misclick Simulation**: Occasional hesitation and wrong-position clicks
- **Fatigue System**: Performance degrades over time, recovers during rest
- **Pattern Learning**: Adapts timing based on recent click history
- **Accidental Double-Clicks**: Rare unintended double-click events
- **Memory Access**: Can read/write game memory for advanced features

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python humanized_clickbot.py
```

## Configuration

Edit the `HumanizationConfig` in the script to customize behavior:

```python
config = HumanizationConfig(
    base_reaction_time=45.0,      # Base reaction delay (ms)
    reaction_time_variance=25.0,  # Standard deviation (ms)
    misclick_probability=0.015,   # 1.5% chance of misclick
    jitter_amplitude=1.5,         # Mouse jitter in pixels
    fatigue_rate=0.0008,          # Fatigue accumulation rate
)
```

## Humanization Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `base_reaction_time` | Base delay before clicking | 50ms |
| `reaction_time_variance` | Random variation in reaction | ±30ms |
| `misclick_probability` | Chance of hesitation/wrong click | 2% |
| `jitter_amplitude` | Mouse movement noise | 2px |
| `jitter_frequency` | Jitter oscillation speed | 15Hz |
| `fatigue_rate` | Performance degradation | 0.1%/s |
| `double_click_probability` | Accidental double-click chance | 1% |

## How It Works

1. **Process Detection**: Finds Geometry Dash process by name
2. **Memory Access**: Opens process with read/write permissions
3. **Humanized Timing**: Calculates delays with Gaussian noise + fatigue
4. **Mouse Simulation**: Uses PyAutoGUI with curved movement paths
5. **Jitter Generation**: Multi-frequency sine waves + Perlin-like noise
6. **Adaptive Learning**: Analyzes click patterns to adjust timing

## Advanced Features

### Memory Reading/Writing
```python
bot.read_memory(address, size=4)
bot.write_memory(address, value, size=4)
```

### Pattern Scanning
```python
address = bot.scan_pattern(b'\x90\x90\x90')
```

## Legal Notice

Use responsibly and only in single-player modes. Respect game terms of service.