# Disney Animation Principles — Implementation Guide

Based on "The Illusion of Life" by Frank Thomas & Ollie Johnston (1981).
All techniques below can be implemented in Python using PIL + math only — no 3D engine, no AI.

---

## Priority Order (Biggest Impact First)

| Rank | Principle | PIL Difficulty | Quality Gain |
|------|-----------|---------------|-------------|
| 1 | **Easing (Slow In/Out)** | Easy | ★★★★★ |
| 2 | **Arcs** | Medium | ★★★★★ |
| 3 | **Follow-Through & Overlap** | Medium | ★★★★☆ |
| 4 | **Skeleton Rigging + Pivot Points** | Medium | ★★★★☆ |
| 5 | **Motion Smear** | Medium | ★★★★☆ |
| 6 | **Squash & Stretch** | Medium | ★★★☆☆ |
| 7 | **Anticipation** | Easy | ★★★☆☆ |
| 8 | **Staging** | Easy | ★★★☆☆ |

---

## The 12 Principles

### 1. Squash & Stretch ★★★★☆
Objects compress on impact and elongate during fast movement. Maintains volume (if height ×0.7, width ×1/0.7).

**Formula:**
```python
# Impact: object squashes down
scale_x = 1.0 / compression
scale_y = compression  # e.g. 0.7

# Affine transform (PIL Image.transform AFFINE)
matrix = (scale_x, 0, tx, 0, scale_y, ty)
img.transform(size, Image.AFFINE, matrix)
```

### 2. Anticipation ★★★☆☆
Brief reverse motion before the main action (character dips before jumping).

**Formula:**
```python
# 10-20% of frames used for anticipation (reverse direction)
anticipation_amount = -main_movement * 0.12
position = anticipation_amount * ease_out(t / anticipation_frames)
# Then main action from frame anticipation_frames onward
```

### 3. Staging ★★★☆☆
Position important elements at rule-of-thirds intersections. Slightly blur/dim secondary elements.

```python
# Rule of thirds positions
focus_x = canvas_w * (1/3 or 2/3)
focus_y = canvas_h * (1/3 or 2/3)

# Dim background elements
bg = bg.filter(ImageFilter.GaussianBlur(radius=2))
bg = ImageEnhance.Brightness(bg).enhance(0.85)
```

### 4. Pose to Pose ★★★☆☆
Define key poses at specific frames; interpolate between them with easing.

```python
keyframes = {0: pose_A, 15: pose_B, 30: pose_C}
# Between frame 0 and 15:
t = (current_frame - 0) / (15 - 0)  # 0.0 to 1.0
value = pose_A + (pose_B - pose_A) * ease_in_out(t)
```

### 5. Follow-Through & Overlapping Action ★★★★☆
Body parts settle at different times. Hair/clothing continue moving after the body stops.

**Formula — exponential decay:**
```python
damping = 0.92  # per frame
follow_offset *= damping  # decays toward zero
part_position = main_position + follow_offset

# Overlapping: different parts start moving with a delay
frame_delays = {"head": 0, "shoulders": 2, "hips": 4, "feet": 6}
effective_frame = current_frame - frame_delays[part]
```

### 6. Slow In / Slow Out (Easing) ★★★★★
**THE most important principle.** Nothing moves at constant speed.

```python
# Ease-out: fast start, slow finish
def ease_out(t): return 1 - (1 - t) ** 3

# Ease-in: slow start, fast finish
def ease_in(t): return t ** 3

# Ease-in-out (most natural):
def ease_in_out(t):
    return 4*t**3 if t < 0.5 else 1 - (-2*t+2)**3 / 2

# Spring (bouncy overshoot):
def spring(t):
    c4 = (2 * math.pi) / 3
    return 1 + (2**(-10*t)) * math.sin((t*10 - 0.75) * c4)

# Apply to any interpolation:
position = start + (end - start) * ease_in_out(t)
```

### 7. Arcs ★★★★★
Everything moves in curves, not straight lines. Gravity creates parabolas.

```python
# Parabolic arc (jump, thrown object)
def arc_position(t, x0, y0, vx, vy, gravity=980):
    x = x0 + vx * t
    y = y0 + vy * t - 0.5 * gravity * t**2
    return x, y

# Circular arc (arm swing, head turn)
def circular_arc(t, cx, cy, radius, start_angle, end_angle):
    angle = start_angle + (end_angle - start_angle) * ease_in_out(t)
    x = cx + radius * math.cos(math.radians(angle))
    y = cy + radius * math.sin(math.radians(angle))
    return x, y
```

### 8. Secondary Action ★★★☆☆
Supporting actions that reinforce the main action (character waves while walking).

```python
# Secondary action = 10-15% amplitude of main action, slight delay
secondary_offset = main_amplitude * 0.12
secondary_position = main_position + secondary_offset * ease_out(t - 0.1)
```

### 9. Timing ★★★☆☆
Number of frames = perceived weight and personality.

| Action | Frames (24fps) | Feel |
|--------|---------------|------|
| Fast eye blink | 3–4 | Snappy |
| Head turn | 8–12 | Normal |
| Heavy object falling | 24–36 | Slow/weighty |
| Light bounce | 6–8 | Quick/light |

### 10. Exaggeration ★★★☆☆
Push movements 1.5–2× beyond realistic limits.

```python
exaggeration = 1.6  # style-dependent
animated_value = base_value + (target_value - base_value) * exaggeration
```

### 11. Solid Drawing ★★★☆☆
Consistent silhouettes. Characters should read clearly as distinct shapes.
**In our pipeline:** use the pre-illustrated chibi assets from `data/assets/physics/`.

### 12. Appeal ★★★★☆
Distinct designs, expressive faces, appealing color choices.
**In our pipeline:** the chibi character style from `data/assets/physics/test_v3/` already achieves this.

---

## Paper Cut-Out Animation (Digital Layer System)

This is the technique used in South Park and Spider-Man: Into the Spider-Verse. Characters are built from PNG layers with pivot points.

### Skeleton Hierarchy
```
torso (root)
├── head          (pivot: neck joint)
│   ├── left_eye  (pivot: eye centre)
│   └── right_eye
├── left_arm      (pivot: shoulder)
│   └── left_forearm (pivot: elbow)
├── right_arm     (pivot: shoulder)
└── left_leg      (pivot: hip)
    └── left_lower_leg (pivot: knee)
```

### Transform Inheritance (Forward Kinematics)
```python
# 2D affine matrix for rotation around pivot point:
def rotation_matrix(angle_deg, pivot_x, pivot_y):
    a = math.radians(angle_deg)
    cos_a, sin_a = math.cos(a), math.sin(a)
    # Translate to pivot, rotate, translate back
    tx = pivot_x - cos_a * pivot_x + sin_a * pivot_y
    ty = pivot_y - sin_a * pivot_x - cos_a * pivot_y
    return (cos_a, -sin_a, tx, sin_a, cos_a, ty)

# Compose parent + child transforms
def compose(parent_m, child_m):
    # 3×3 matrix multiply (flattened)
    ...

# Render bone with accumulated transform
img.transform(size, Image.AFFINE, bone.world_transform)
```

### Motion Smear (Spider-Verse Style)
```python
# Draw object at previous N positions with decreasing opacity
history = [pos_t, pos_t_minus_1, pos_t_minus_2]
for i, pos in enumerate(history):
    alpha = int(255 * (1.0 - i / len(history)) * 0.5)
    frame.paste(sprite, pos, mask=sprite_with_alpha(alpha))
```

### Chromatic Aberration (Comic Book Effect)
```python
r, g, b, a = img.split()
# Shift channels by 1–3 pixels
r = ImageChops.offset(r, 2, 0)
b = ImageChops.offset(b, -2, 0)
result = Image.merge('RGBA', (r, g, b, a))
```

---

## Implementation Roadmap for This Project

### Phase 1 — Already Done ✅
- Easing functions (linear, ease_in, ease_out, ease_in_out, spring, bounce)
- FadeIn, SlideIn, ScaleIn, Pop animations
- Keyframe-based ElementTimeline

### Phase 2 — Next Priority
- **Arc motion paths** — replace straight-line SlideIn with parabolic arcs
- **Follow-through** — characters overshoot and settle with spring easing
- **Breathing idle** — characters slowly scale ±2% in a loop (feels alive)

### Phase 3 — Major Upgrade
- **Paper cut-out rigging** — build character as layered PNGs with pivot points
- **Motion smear** — add to fast SlideIn/SlideOut animations
- **Proper skeleton system** — replace single-image characters with rigged layers

### Phase 4 — Polish
- Squash & stretch on character entrances
- Anticipation frames on all main actions
- Secondary action (equipment/prop movement during narration)

---

## References
- "The Illusion of Life: Disney Animation" — Frank Thomas & Ollie Johnston
- [Twelve basic principles of animation — Wikipedia](https://en.wikipedia.org/wiki/Twelve_basic_principles_of_animation)
- [Easing Functions Cheat Sheet](https://easings.net/)
- [Spider-Man: Into the Spider-Verse animation breakdown — CGSpectrum](https://www.cgspectrum.com/blog/spider-man-into-the-spider-verse-how-they-got-that-mind-blowing-look/)
- [Motion smear in 2D animation — canmom](https://canmom.art/animation/smears/)
