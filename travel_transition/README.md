# Austin → Dallas Travel Transition

Broadcast-quality travel transition graphic for YouTube timelines.

## Output

**`Austin_to_Dallas_45_Minutes_Later.mp4`**
- 1920×1080, 30 fps, H.264, no audio
- 5.5 seconds

## Regenerate

```bash
pip install moviepy pillow numpy
python render_transition.py
```

## Animation Timeline

| Time | Event |
|------|-------|
| 0.0s | Texas outline fades in |
| 0.4s | Austin & Dallas markers appear |
| 0.8s | Flight path begins drawing |
| 1.2s | Airplane departs Austin |
| 1.4s | "45 Minutes Later..." fades in |
| 4.8s | Airplane arrives in Dallas |
| 5.2s | Fade to black |
