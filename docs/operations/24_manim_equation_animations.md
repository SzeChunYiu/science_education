# Manim CE Equation Animations

## Overview

Manim Community Edition (Manim CE) replaces PIL text rendering for equations, enabling:

- **LaTeX-quality math** — proper fractions, subscripts, Greek letters, vectors
- **Smooth morphing** — `TransformMatchingTex` animates term-by-term transitions between equation forms
- **Color-coded highlighting** — individual terms (mass, velocity, force) get semantic colors
- **Transparent exports** — Manim renders with alpha channel, composited over any background

This is the single biggest visual quality upgrade available to the pipeline.

---

## Installation on LUNARC

Manim is installed in the `science_edu` conda environment:

```bash
module load Anaconda3/2024.06-1
CONDARC=/projects/hep/fs10/shared/nnbar/billy/science_education/condarc_tmp.yaml \
  conda install -p /projects/hep/fs10/shared/nnbar/billy/packages/science_edu \
  manim -c conda-forge -y
```

Verify:
```bash
/projects/hep/fs10/shared/nnbar/billy/packages/science_edu/bin/python -c "import manim; print(manim.__version__)"
```

---

## Architecture: Equation Clip Cache

Manim renders are cached per-equation to avoid redundant rendering across 189 episodes.

```
output/assets/equation_clips/
  F_equals_ma.mp4          ← "F = ma"
  p_equals_mv.mp4          ← "p = mv"
  F_equals_dp_dt.mp4       ← "F = dp/dt"
  ...
```

The cache is keyed by equation string (normalized). When `episode_renderer.py` encounters an equation scene, it:
1. Checks the cache
2. If miss → generates the Manim clip (writes to cache)
3. Composites the clip into the scene at the correct position/timing

---

## Example: Equation Morph Scene

```python
from manim import *

class EquationReveal(Scene):
    def construct(self):
        # Equation with color-coded terms
        eq1 = MathTex(
            r"p", r"=", r"m", r"v",
            substrings_to_isolate=["p", "m", "v"]
        )
        eq1.set_color_by_tex("p", BLUE)
        eq1.set_color_by_tex("m", RED)
        eq1.set_color_by_tex("v", GREEN)

        # Morph to second form
        eq2 = MathTex(r"F = \frac{dp}{dt}")

        self.play(Write(eq1), run_time=1.5)
        self.wait(0.5)
        self.play(TransformMatchingTex(eq1, eq2), run_time=1.5)
        self.wait(1)
```

Render to transparent PNG sequence:
```bash
manim -qm --format=png --transparent equation_scene.py EquationReveal
```

---

## Integration Plan

### Phase 1 — Standalone equation renderer (current approach)

Add `src/animation/manim_equations.py`:

```python
def render_equation_clip(
    equation_latex: str,
    output_path: str,
    color: str = "#FFFFFF",
    bg_transparent: bool = True,
    duration: float = 3.0,
) -> str:
    """Render a single equation as a Manim MP4 clip with optional transparency."""
    ...

def render_equation_morph(
    from_latex: str,
    to_latex: str,
    output_path: str,
    duration: float = 2.5,
) -> str:
    """Render a TransformMatchingTex morphing animation between two equations."""
    ...
```

### Phase 2 — Cache integration in episode_renderer

`episode_renderer.py` checks `output/assets/equation_clips/` before calling PIL text rendering. If a Manim clip exists for the equation, it composites the clip instead of drawing text.

### Phase 3 — Derivation sequences

The `derivation_step_scene` factory gets upgraded to use a sequence of Manim morphs:

```
p = mv  →  F = Δp/Δt  →  F = dp/dt  →  F = ma
```

Each arrow is a `TransformMatchingTex` with 1.5s transition, building the full derivation visually.

---

## Render Performance Expectations

| Scene type | PIL (current) | Manim |
|------------|---------------|-------|
| Plain text equation | ~0.1s | ~8–15s |
| Equation morph | N/A | ~20–40s |
| Full derivation (4 steps) | ~0.5s | ~60–90s |

On LUNARC with 189 parallel jobs, the Manim slowdown is absorbed — each job still completes well within the 1-hour time limit. Locally, Manim for all equations would be prohibitively slow.

---

## Equation Inventory

Core equations across the curriculum (candidates for Manim rendering):

| Topic | Equation |
|-------|----------|
| Newton's 2nd Law | `F = ma`, `F = dp/dt` |
| Momentum | `p = mv`, `\Delta p = F \Delta t` |
| Kinetic Energy | `KE = \frac{1}{2}mv^2` |
| Work-Energy | `W = F \cdot d`, `W = \Delta KE` |
| Conservation of Energy | `E = KE + PE = \text{const}` |
| Gravitation | `F = G\frac{m_1 m_2}{r^2}` |
| Orbital velocity | `v = \sqrt{\frac{GM}{r}}` |
| Special Relativity | `E = mc^2`, `E^2 = (pc)^2 + (mc^2)^2` |
| Lorentz factor | `\gamma = \frac{1}{\sqrt{1-v^2/c^2}}` |
| Schrödinger | `i\hbar\frac{\partial\psi}{\partial t} = \hat{H}\psi` |
| Heisenberg | `\Delta x \cdot \Delta p \geq \frac{\hbar}{2}` |

Pre-rendering all ~50 core equations as a one-time batch is feasible and builds the full cache before mass video production.
