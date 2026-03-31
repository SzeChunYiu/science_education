# Scene Template Catalog
**Synthesized from:** 545 `[Visual: ...]` tags across 74 YouTube Long scripts, plus implied visual analysis of 90+ additional scripts without explicit tags
**Coverage target:** 12 templates covering 90%+ of all visual needs

## Status

This file is still useful as a broad research catalog of scene families.

It is not the main implementation contract for current production code.

Use these as the active implementation docs first:

- `../operations/19_scene_and_layout_workflow.md`
- `../operations/22_animation_production_runbook.md`
- `powerpoint_layout_rules.md`
- `slide_layout_inventory.md`

---

## How to Read This Document

Each template is a reusable layout configuration. The **layout zones** refer to the 16:9 frame divided as:
- **Top zone**: ~0–20% height — episode/series titles only
- **Main zone**: ~20–80% height — primary visual content
- **Lower zone**: ~80–85% height — supplementary labels, secondary text
- **Subtitle reserve**: ~85–100% height — reserved for burned-in subtitles; NO content enters this zone per project rules

All templates are designed for the "My First Heroes: Inventors" chibi art style: rounded characters, bold flat colors, minimal detail, illustrated (not photographic or abstract).

---

## Template 01: EQUATION_REVEAL

**Frequency:** Appears in 72+ episodes (most common single template)
**Description:** A single equation appears large and clean, centered. Each symbol is labeled with a small annotation. This is the "moment the equation lands" scene — used when introducing a key equation for the first time.
**Elements present:**
- Large equation (center, main zone)
- Annotation labels for each symbol (color-coded arrows or dotted lines to symbol)
- Optional: equation name or "in a box" highlight
**Layout zones used:** Main zone (center)
**Example visual cues that map to this template:**
- `[Visual: equation p = mv displayed large and clean]` — ep04 Newton's Laws
- `[Visual: equation F = dp/dt]` — ep05 Newton's Laws
- `[Visual: T = 2π√(L/g) in a box with the variables labeled]` — ep02 Oscillations
- `[Visual: ω₀ = √(k/m) in a box]` — ep01 Oscillations
- `[Visual: boxed equation — T² = (4π²/GM)a³]` — ep04 Gravity
- `[Visual: V_eff equation boxed prominently]` — ep02 Central Force
- `[Visual: equation highlighted — THE Hamilton-Jacobi equation]` — ep06 Hamiltonian
- `[Visual: Tsiolkovsky Rocket Equation in a box]` — ep05 Newton's Laws
- `[Visual: clean display of the two postulates]` — ep01 Special Relativity
**Variations:**
- **EQUATION_REVEAL_LABELED**: Equation with every symbol annotated (most common)
- **EQUATION_REVEAL_BOXED**: Equation highlighted with a box or border (used for "this is the key result")
- **EQUATION_REVEAL_PLAIN**: Equation alone, no labels, used for well-known equations (F=ma, E=mc²)
- **EQUATION_DUAL**: Two equations side by side for comparison (`[Visual: two equations appearing side by side]`)

---

## Template 02: DERIVATION_STEPWISE

**Frequency:** Appears in 65+ episodes
**Description:** Mathematical derivation shown line by line, with each new step appearing in sequence. The screen fills from top to bottom as algebra progresses. A highlight or box marks the final result.
**Elements present:**
- Sequential algebra lines, appearing one at a time (main zone, left-aligned or centered)
- Optional: substitution labels ("substituting from above", arrows between lines)
- Final result: boxed or colored differently
**Layout zones used:** Main zone (fills vertically as derivation progresses)
**Example visual cues that map to this template:**
- `[Visual: each algebra step appearing line by line]` — ep05 Newton's Laws
- `[Visual: step-by-step algebra]` — ep02 Hamiltonian
- `[Visual: derivation steps shown line by line]` — ep01 Vector Calculus
- `[Visual: derivation displayed step by step]` — ep02 Pauli Exclusion
- `[Visual: the algebra appearing step by step, with each substitution highlighted]` — ep03 Conservation
- `[Visual: substitution steps appearing one at a time]` — ep01 Oscillations
- `[Visual: step-by-step, ṙ = −(L/μ)(du/dθ)]` — ep03 Central Force
- `[Visual: calculation appearing step by step]` — multiple episodes
**Variations:**
- **DERIVATION_FULL**: Complete multi-step derivation, 4–8 lines
- **DERIVATION_KEY_STEP**: Single highlighted algebra step ("the key step"), often with a color highlight
- **DERIVATION_SUBSTITUTION**: Shows a substitution explicitly, old expression on left → new on right with arrow

---

## Template 03: CHARACTER_PORTRAIT

**Frequency:** Appears in 40+ episodes
**Description:** A single historical scientist is depicted in their period setting. The character appears in chibi/illustrated style. A lower-third shows their name, birth-death years, and optional nationality or title. Used to introduce a new character or mark a historical transition.
**Elements present:**
- Character illustration (center or left-center, main zone, ~50% frame width)
- Name + dates lower-third (lower zone, left-aligned)
- Optional: period setting as background (library, laboratory, workshop)
- Optional: a prop associated with them (ramp, pendulum, book, torsion balance)
**Layout zones used:** Main zone (character), lower zone (name/date label)
**Example visual cues that map to this template:**
- `[Visual: Galileo in his Pisa laboratory, wooden inclined ramp, brass balls, water clock]` — ep02 Newton
- `[Visual: portrait of young Einstein, 1905 Bern patent office setting]` — ep09 Newton
- `[Visual: portrait of Emmy Noether, University of Göttingen, 1918]` — ep11 Newton
- `[Visual: d'Alembert — 18th-century Encyclopedist style — sitting at a desk]` — ep01 Lagrangian
- `[Visual: young Lagrange portrait — elegant, composed]` — ep01 Lagrangian
- `[Visual: Maupertuis — grand 18th-century portrait style]` — ep02 Lagrangian
- `[Visual: Euler — spectacles, Swiss academic setting]` — ep02 Lagrangian
- `[Visual: Heisenberg in 1920s clothing, blackboard with equations behind him]` — ep10 Newton
- `[Visual: Kepler at his desk, data tables spread before him, quill in hand]` — ep04 Gravity
- `[Visual: Huygens in his workshop with the clock mechanism]` — ep02 Oscillations
- `[Visual: portrait of Émilie du Châtelet]` — ep03 Conservation
**Variations:**
- **CHARACTER_PORTRAIT_SOLO**: Character alone, clean background, name lower-third
- **CHARACTER_PORTRAIT_SETTING**: Character in their historical environment (lab, office, observatory)
- **CHARACTER_PORTRAIT_PROP**: Character shown with a key object (Cavendish torsion balance, Joule paddle wheel)

---

## Template 04: CHARACTER_MULTI (Timeline / Sequence)

**Frequency:** Appears in 18+ episodes
**Description:** Two or three historical figures appear together, arranged left-to-right in chronological order. Used for "progression of ideas" moments, showing how an idea passed from one thinker to the next. Also used for debate/comparison of two scientists with opposing views.
**Elements present:**
- 2–3 character illustrations in a row (main zone)
- Each with name + dates label below
- Optional: arrow or line between them showing direction of influence
- Optional: thought-bubble or equation above each character showing their key idea
**Layout zones used:** Main zone (full width, split into 2–3 columns), lower zone (labels)
**Example visual cues that map to this template:**
- `[Visual: three portraits in timeline — da Vinci (1452-1519), Amontons (1663-1705), Coulomb (1736-1806)]` — ep08 Newton
- `[Visual: portraits of Wallis, Wren, Huygens in sequence]` — ep02 Conservation
- `[Visual: portraits of Lagrange (1736-1813) and Hamilton (1805-1865)]` — ep11 Newton
- `[Visual: timeline showing Philoponus → Buridan → approaching Galileo]` — ep01 Newton
- `[Visual: side-by-side comparison — Galileo's circular inertia vs Descartes' straight-line inertia]` — ep03 Newton
- `[Visual: 1668 London — Royal Society setting, three scholars at a table]` — ep06 Newton
**Variations:**
- **CHARACTER_MULTI_TIMELINE**: Left-to-right chronological sequence with arrows
- **CHARACTER_MULTI_DEBATE**: Two characters facing each other or side by side, showing contrasting ideas
- **CHARACTER_MULTI_GROUP**: Three+ characters in a shared setting (committee, society meeting)

---

## Template 05: PHYSICS_DIAGRAM

**Frequency:** Appears in 60+ episodes
**Description:** A physics diagram showing a physical setup — objects, forces, geometry. May include force arrows (labeled vectors), measurement labels, and coordinate axes. This is the workhorse diagram template: pendulums, inclined planes, orbits, springs, circuits, and similar setups.
**Elements present:**
- Central object(s) in a physical configuration (main zone)
- Force arrows with labels (color-coded by force type)
- Dimension/angle labels
- Optional: coordinate axes
- Optional: a "zoom" inset for a small sub-element
**Layout zones used:** Main zone (diagram fills ~60–70% of frame width, centered or left-of-center), lower zone may hold equation reference
**Example visual cues that map to this template:**
- `[Visual: free-body diagram with two arrows — W pointing down, N pointing up]` — ep07 Newton
- `[Visual: bead on wire diagram, with gravity arrow pointing down, and question-mark arrow showing normal force]` — ep01 Lagrangian
- `[Visual: pendulum diagram with all quantities labeled — L, m, θ, mg, tension T, arc length Lθ]` — ep02 Oscillations
- `[Visual: free body diagram of pendulum, with all force arrows]` — ep01 Lagrangian
- `[Visual: diagram of two objects A and B, with force arrows — F_AB, F_BA]` — ep06 Newton
- `[Visual: gyroscope diagram — L pointing up along spin axis, r, mg, τ = r × mg]` — ep04 Rigid Body
- `[Visual: diagram of the string in equilibrium, x-axis labeled, tension T shown at both ends]` — ep05 Oscillations
- `[Visual: force vector at angle θ to horizontal displacement d]` — ep04 Conservation
- `[Visual: two vectors r and p in a plane, with angle θ between them]` — ep05 Conservation
- `[Visual: diagram of Cavendish torsion balance — labeled components]` — ep06 Gravity
- `[Visual: gyroscope diagram — L pointing up along spin axis]` — ep04 Rigid Body
**Variations:**
- **DIAGRAM_FORCE_BODY**: Classic free-body diagram (isolated object, named force arrows)
- **DIAGRAM_GEOMETRY**: Geometric setup (angles, distances, coordinate axes) without forces
- **DIAGRAM_SYSTEM**: Multi-body setup (Atwood machine, two-body orbit, double pendulum)
- **DIAGRAM_FIELD**: Field lines or field arrows (gravitational field, electric field, magnetic field)

---

## Template 06: MOTION_ANIMATION

**Frequency:** Appears in 35+ episodes
**Description:** A physical process is shown in motion — a ball rolling, an orbit, a wave propagating, a collision. This is a sequential scene showing CHANGE over time, not a static snapshot. Often accompanied by a velocity/position label that updates, or a visible trail.
**Elements present:**
- Moving object(s) with visible trajectory (arrow trail or dotted path)
- Optional: velocity vectors updating as object moves
- Optional: time labels at key positions
- Optional: "before / after" snapshots shown simultaneously
**Layout zones used:** Main zone (full width for motion paths)
**Example visual cues that map to this template:**
- `[Visual: Manim animation of inclined plane experiment — ball rolling down, timing marks]` — ep02 Newton
- `[Visual: animated double-ramp setup — ball rolls down, crosses flat section, rolls up]` — ep02 Newton
- `[Visual: animation of a pulse moving rightward without changing shape]` — ep05 Oscillations
- `[Visual: animation of mass on spring oscillating; force arrow and velocity arrow shown at each phase]` — ep01 Oscillations
- `[Visual: sequence of cannonball trajectories — each faster than the previous, curving increasingly]` — ep07 Gravity
- `[Visual: animation of two bodies orbiting their CM in CM frame]` — ep01 Central Force
- `[Visual: ice skater with arms extended, then pulling arms in — transition between states]` — ep05 Conservation
- `[Visual: animation — particle spiraling inward, spinning faster and faster]` — ep02 Central Force
- `[Visual: two balls on screen, moving toward each other on a line]` — ep01 Conservation
- `[Visual: animation showing multiple paths from A to B, with travel times labeled]` — ep02 Lagrangian
- `[Visual: time-lapse animation of Mars tracing its retrograde loop against background stars]` — ep01 Gravity
**Variations:**
- **MOTION_SINGLE**: One object moving with labeled vectors
- **MOTION_COLLISION**: Two objects approaching, colliding, separating (before/after)
- **MOTION_ORBIT**: Object following a curved path (circular, elliptical, parabolic)
- **MOTION_WAVE**: Wave propagating (string wave, EM wave, wavefront)
- **MOTION_THOUGHT_EXPERIMENT**: Idealized scenario showing a logical progression (Galileo's ramp)

---

## Template 07: COMPARISON_SPLIT

**Frequency:** Appears in 45+ episodes
**Description:** The screen is divided into two (or three) vertical panels, each showing a different scenario, equation, or concept for direct comparison. Used for "old vs new", "this law vs that law", "fast vs slow", "elastic vs inelastic", etc.
**Elements present:**
- 2 (occasionally 3) side-by-side panels, equal width
- Each panel: label at top (e.g., "Newton" / "Einstein"), scenario or equation below
- Optional: connecting arrow or dividing line between panels
- Optional: check mark / X mark indicating which is correct
**Layout zones used:** Main zone (full width, split vertically into equal columns), top zone for panel labels
**Example visual cues that map to this template:**
- `[Visual: split screen — ball at rest vs ball moving at constant velocity, both labeled "No net force"]` — ep01 Newton
- `[Visual: side-by-side comparison — Galileo's circular inertia vs Descartes' straight-line inertia]` — ep03 Newton
- `[Visual: two systems side by side — tennis ball, electron]` — ep10 Newton
- `[Visual: boundary condition with two regimes labeled — "Classical (Newton)" and "Quantum (Schrödinger)"]` — ep10 Newton
- `[Visual: contrasting arrows — Aristotle's "cause needed for motion" vs Newton's "cause needed for change in motion"]` — ep03 Newton
- `[Visual: side-by-side: F=dp/dt and τ=dL/dt]` — ep05 Conservation
- `[Visual: side-by-side — spatial rotation vs. Lorentz boost]` — ep01 Special Relativity
- `[Visual: side by side — particle (dot) vs. field (wave covering all space)]` — ep01 QFT
- `[Visual: contrast between Galilean spacetime (flat, time separate) and Minkowski spacetime (tilted, mixed)]` — ep02 QFT
- `[Visual: comparison diagram — Earth pendulum swinging fast, Moon pendulum swinging slow, same length]` — ep02 Oscillations
- `[Visual: graph of γ vs v/c — flat near v=0, curving up sharply near v=c]` — ep09 Newton
**Variations:**
- **COMPARISON_TWO_CONCEPTS**: Two physics concepts (old theory vs new, two laws)
- **COMPARISON_TWO_OBJECTS**: Same law applied to two different objects (fast/slow, heavy/light)
- **COMPARISON_THREE_CASES**: Three scenarios side by side (underdamped, critically damped, overdamped)
- **COMPARISON_BEFORE_AFTER**: Single scenario shown before and after an event

---

## Template 08: GRAPH_PLOT

**Frequency:** Appears in 25+ episodes
**Description:** A mathematical graph — x-y axes with one or more curves. Used for visualizing relationships: velocity-time graphs, energy diagrams, resonance curves, phase portraits, potential energy wells. Annotations label key features.
**Elements present:**
- Axis pair with labeled variable names and units
- One or more curves (each labeled or color-coded)
- Key feature annotations (e.g., "slope = acceleration", "area = displacement", "peak = resonant frequency")
- Optional: shaded region under/between curves
**Layout zones used:** Main zone (graph occupies ~60–70% width, centered)
**Example visual cues that map to this template:**
- `[Visual: velocity-time graph appearing — horizontal axis labeled "time (t)", vertical axis labeled "velocity (v)", a straight line rising from origin]` — ep02 Newton
- `[Visual: shaded triangle under the velocity-time graph]` — ep02 Newton
- `[Visual: graph of γ vs v/c — extremely flat near v=0, curving up sharply near v=c]` — ep09 Newton
- `[Visual: velocity vs. time graph — straight line extending upward indefinitely]` — ep09 Newton
- `[Visual: graph of A(ω) vs ω, with different Q values shown]` — ep04 Oscillations
- `[Visual: the full resonance curve labeled with three regimes]` — ep04 Oscillations
- `[Visual: underdamped oscillation plot — amplitude decaying as exponential envelope]` — ep03 Oscillations
- `[Visual: x vs t graph plotting this solution, with time points labeled]` — ep01 Oscillations
- `[Visual: U(x) curve plotted, with horizontal line for total energy E]` — ep06 Conservation
- `[Visual: complete U and KE vs height graph]` — ep06 Conservation
- `[Visual: V_eff(r) curve for gravity, with horizontal lines at different energies]` — ep02 Central Force
- `[Visual: graph showing p vs. v, Newtonian (straight line) vs. relativistic (diverging curve)]` — ep03 Special Relativity
- `[Visual: snapshot and time trace plots side by side]` — ep05 Oscillations
**Variations:**
- **GRAPH_SINGLE_CURVE**: One curve, axes labeled, key features annotated
- **GRAPH_MULTI_CURVE**: Two or more curves on same axes (e.g., different Q values, Newtonian vs relativistic)
- **GRAPH_ENERGY_DIAGRAM**: Potential energy well U(x) with total energy line E and turning points marked
- **GRAPH_PHASE_PORTRAIT**: Phase space diagram (position vs momentum, or q vs p) with orbit curves

---

## Template 09: DATA_TABLE

**Frequency:** Appears in 20+ episodes
**Description:** A structured table displayed on screen, building row by row or column by column as narration proceeds. Used for data, symbol glossaries, comparison tables, and numerical results.
**Elements present:**
- Table with header row and 2–5 columns
- Rows appear sequentially with narration
- Each cell: concise text or number
- Optional: one row or column highlighted (the "key" row)
**Layout zones used:** Main zone (table fills ~70–80% width, centered)
**Example visual cues that map to this template:**
- `[Visual: table appearing on screen]` — ep02 Newton (Galileo's data)
- `[Visual: table of γ values at different speeds]` — ep09 Newton
- `[Visual: table comparing all three objects — momentum column highlights the mass-speed tradeoff]` — ep04 Newton
- `[Visual: table comparing inertial vs non-inertial frame observations]` — ep03 Newton
- `[Visual: table appearing row by row, last column converging to 1.000]` — ep04 Gravity (Kepler's T²/a³)
- `[Visual: two-column table: "Always conserved" vs "Conserved only elastically"]` — ep01 Conservation
- `[Visual: table forming with columns: height, U, KE, v]` — ep06 Conservation
- `[Visual: symmetry-conservation table]` — ep07 Conservation (Noether)
- `[Visual: table — velocity, γ, γ³, ratio of relativistic to classical force needed]` — ep03 Special Relativity
- `[Visual: table of all four quantum numbers with their ranges]` — ep02 Pauli Exclusion
**Variations:**
- **TABLE_DATA**: Experimental or numerical data (rows build as narration proceeds)
- **TABLE_COMPARISON**: Side-by-side comparison (two theories, two objects, two regimes)
- **TABLE_SYMBOL_GLOSSARY**: Symbol | Name | Units | Physical meaning (standard symbol introduction table)
- **TABLE_RESULT_SUMMARY**: End-of-section summary table of key results

---

## Template 10: HISTORICAL_DOCUMENT

**Frequency:** Appears in 15+ episodes
**Description:** A historical document is shown — a book page, a notebook sketch, a title page, an original text in Latin or another language — optionally with a translation appearing below or alongside. Used to add authenticity and anchor abstract ideas to concrete historical moments.
**Elements present:**
- Illustrated representation of a document/book page (center or slightly left, main zone)
- Optional: Latin or original-language text with English translation appearing line by line
- Optional: character portrait in lower corner as "context" (who wrote this)
**Layout zones used:** Main zone (document fills ~50–60% of width)
**Example visual cues that map to this template:**
- `[Visual: Newton's Principia open to Lex II — Latin text visible]` — ep05 Newton
- `[Visual: Newton's Principia open to Lex Prima — the Latin text of the First Law]` — ep03 Newton
- `[Visual: Newton's Principia, Lex III, Latin text with translation]` — ep06 Newton
- `[Visual: Latin text appearing, then English translation beneath]` — ep03 Newton
- `[Visual: Latin text appearing with English translation line by line]` — ep05 Newton
- `[Visual: the Mécanique Analytique title page — elegant 18th-century typography]` — ep01 Lagrangian
- `[Visual: Principia open to Definition II]` — ep04 Newton
- `[Visual: da Vinci's notebook sketches of friction experiments]` — ep08 Newton
**Variations:**
- **DOCUMENT_BOOK**: Open book showing a specific passage
- **DOCUMENT_TRANSLATION**: Source language text with translation appearing below
- **DOCUMENT_NOTEBOOK**: Handwritten notes/sketches (da Vinci style, personal notebook feel)
- **DOCUMENT_TITLE_PAGE**: Book cover or title page (formal, prestigious)

---

## Template 11: CONCEPT_CONNECTION

**Frequency:** Appears in 25+ episodes
**Description:** An abstract conceptual diagram showing how two or more ideas, laws, or domains connect. Includes tree diagrams, flow charts, "leads to" arrows, symmetry-conservation links, and the "where this breaks down" limit diagrams. Used at episode beginnings (orientation) and endings (synthesis).
**Elements present:**
- Concept boxes or nodes (labeled with equations or concept names)
- Arrows showing direction of implication or historical derivation
- Optional: color-coding by era, domain, or theory level
- Optional: one node highlighted as the current episode's focus
**Layout zones used:** Main zone (fills ~70–80% width, centered or full-width for trees)
**Example visual cues that map to this template:**
- `[Visual: wide-angle view of a tree diagram — Newton at the base, branches extending upward to relativity, quantum mechanics, field theory]` — ep12 Newton
- `[Visual: hierarchical tree diagram with each level labeled and dated]` — ep12 Newton
- `[Visual: two boxes — "Symmetry" and "Principle of Stationary Action"]` — ep12 Newton
- `[Visual: flow chart — Newton's machinery → requires exact x and p → Heisenberg says impossible → Newton fails]` — ep10 Newton
- `[Visual: three-panel diagram — each symmetry leads to a conservation law]` — ep11 Newton
- `[Visual: boxed result: "Space translation symmetry → Momentum conservation"]` — ep07 Conservation
- `[Visual: symmetry-conservation table]` — ep07 Conservation
- `[Visual: boundary condition with two regimes labeled — "Classical" and "Quantum"]` — ep10 Newton
- `[Visual: transformation diagram — two orbiting bodies → single orbit around fixed centre]` — ep01 Central Force
- `[Visual: coordinate space diagram — (q, q̇) space on left, (q, p) space on right, arrow between them]` — ep01 Hamiltonian
- `[Visual: the substitution rules displayed as a "translation dictionary" between classical and quantum quantities]` — ep02 QFT
**Variations:**
- **CONNECTION_TREE**: Hierarchical branching diagram (shows how a field develops)
- **CONNECTION_FLOW**: Linear flow chart with conditions/implications
- **CONNECTION_MAPPING**: Two-column mapping (this concept corresponds to that concept in the new theory)
- **CONNECTION_BREAKDOWN**: Equation in center with "valid here" and "fails here" zones marked

---

## Template 12: WORKED_EXAMPLE

**Frequency:** Appears in 40+ episodes
**Description:** A structured calculation shown on screen, walking through a physics problem numerically. The problem setup is shown briefly (diagram), then numbers are substituted, then intermediate results appear, then the final answer is highlighted. This is distinct from DERIVATION_STEPWISE (which is symbolic algebra) — this template uses concrete numbers.
**Elements present:**
- Problem setup: diagram or brief text statement (top of main zone)
- Calculation lines appearing sequentially
- Each substitution labeled (e.g., "m = 3 kg", "v = 10 m/s")
- Final numerical answer highlighted or boxed
- Optional: physical interpretation sentence after the answer
**Layout zones used:** Main zone (calculation fills ~70% width, left-aligned or centered)
**Example visual cues that map to this template:**
- `[Visual: Atwood machine animated with the numbers: m₁ = 3 kg rising at 2.45 m/s², m₂ = 5 kg falling at 2.45 m/s²]` — ep07 Newton
- `[Visual: calculation shown on screen with numerical check]` — ep05 Gravity
- `[Visual: calculation displayed step by step]` — ep06 Gravity (Cavendish → Earth mass)
- `[Visual: calculation cascading with each line]` — ep04 Gravity
- `[Visual: table forming with columns: height, U, KE, v]` — ep06 Conservation
- `[Visual: I₁ = 4.48, ω₁ = 2π appearing]` / `[Visual: ω₂ ≈ 7 rev/s appearing]` — ep05 Conservation
- `[Visual: numerical calculation displayed]` — ep04 Rigid Body
- `[Visual: 31.3 m/s highlighted]` / `[Visual: 24.2 m/s highlighted]` — ep04 Conservation
- `[Visual: unit calculation appearing]` — ep03 Conservation
- `[Visual: numbers substituted]` — ep03 Central Force
**Variations:**
- **WORKED_EXAMPLE_BASIC**: Numbers plugged in, answer out (1–3 steps)
- **WORKED_EXAMPLE_FULL**: Multi-step calculation with labeled intermediate results
- **WORKED_EXAMPLE_ANIMATED**: Object shown moving while numbers appear alongside
- **WORKED_EXAMPLE_TABLE**: Results organized in a table (multiple cases or columns)

---

## Template Coverage Matrix

| Template | Classical Mech | EM | Thermo | Quantum | Relativity | Math Methods |
|---|---|---|---|---|---|---|
| 01 EQUATION_REVEAL | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| 02 DERIVATION_STEPWISE | ✓✓✓ | ✓✓ | ✓✓ | ✓✓✓ | ✓✓ | ✓✓✓ |
| 03 CHARACTER_PORTRAIT | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓ | ✓✓ | ✓ |
| 04 CHARACTER_MULTI | ✓✓ | ✓✓ | ✓✓ | ✓ | ✓ | — |
| 05 PHYSICS_DIAGRAM | ✓✓✓ | ✓✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓✓ |
| 06 MOTION_ANIMATION | ✓✓✓ | ✓✓ | ✓ | ✓✓ | ✓ | — |
| 07 COMPARISON_SPLIT | ✓✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓✓ | ✓ |
| 08 GRAPH_PLOT | ✓✓ | ✓✓ | ✓✓✓ | ✓✓ | ✓ | — |
| 09 DATA_TABLE | ✓✓ | ✓ | ✓✓ | ✓ | ✓ | — |
| 10 HISTORICAL_DOCUMENT | ✓✓✓ | ✓✓ | ✓✓ | ✓ | — | — |
| 11 CONCEPT_CONNECTION | ✓✓✓ | ✓✓ | ✓✓ | ✓✓✓ | ✓✓ | ✓ |
| 12 WORKED_EXAMPLE | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓ | ✓ | ✓ |

Legend: ✓✓✓ = very frequent, ✓✓ = common, ✓ = occasional, — = rare/absent

---

## Scene Sequence Patterns

These templates appear in predictable sequences within episodes. The layout engine should expect these chains:

**Episode Opening (0:00–0:30)**
```
CHARACTER_PORTRAIT_SETTING → (optional) HISTORICAL_DOCUMENT → CONCEPT_CONNECTION (tree/overview)
```

**Introducing a New Concept**
```
PHYSICS_DIAGRAM → EQUATION_REVEAL_LABELED → DERIVATION_STEPWISE → EQUATION_REVEAL_BOXED (final result)
```

**Worked Example Section**
```
PHYSICS_DIAGRAM (setup) → WORKED_EXAMPLE_FULL (numbers) → GRAPH_PLOT or DATA_TABLE (results)
```

**Historical Narrative Section**
```
CHARACTER_PORTRAIT_SETTING → HISTORICAL_DOCUMENT → CHARACTER_MULTI_TIMELINE (next figure) → EQUATION_REVEAL (their contribution)
```

**Comparison / Limits Section**
```
COMPARISON_SPLIT (old vs new) → EQUATION_REVEAL (new version) → CONCEPT_CONNECTION_BREAKDOWN (where old fails)
```

**Episode Closing**
```
CONCEPT_CONNECTION_TREE (synthesis) → COMPARISON_SPLIT (this episode ↔ next episode preview)
```

---

## Element Reuse Inventory (High-Priority Assets)

These character or setting assets appear across the most episodes and should be produced once and reused:

| Asset | Appears In | Template Type |
|---|---|---|
| Isaac Newton (standing/formal) | 6+ episodes | CHARACTER_PORTRAIT |
| Galileo Galilei (with ramp) | 5+ episodes | CHARACTER_PORTRAIT_SETTING |
| Emmy Noether (portrait) | 2 episodes, fundamental | CHARACTER_PORTRAIT |
| Albert Einstein (young, patent office) | 3+ episodes | CHARACTER_PORTRAIT_SETTING |
| Johannes Kepler (at desk) | 2 episodes | CHARACTER_PORTRAIT_SETTING |
| Aristotle (ancient Greece setting) | 3+ episodes | CHARACTER_PORTRAIT_SETTING |
| Mass-spring system (horizontal) | 8+ episodes | PHYSICS_DIAGRAM |
| Simple pendulum (angle θ) | 6+ episodes | PHYSICS_DIAGRAM |
| Free-body diagram block on flat surface | 5+ episodes | PHYSICS_DIAGRAM_FORCE_BODY |
| Inclined plane (generic angle) | 4+ episodes | PHYSICS_DIAGRAM_GEOMETRY |
| Orbit diagram (ellipse + focus) | 6+ episodes | MOTION_ORBIT |
| Ball-wall collision | 3+ episodes | MOTION_COLLISION |
| Rocket in space (exhaust trailing) | 3+ episodes | MOTION_SINGLE |
| Velocity-time graph (linear) | 4+ episodes | GRAPH_SINGLE_CURVE |
| Energy diagram (U(x) curve + E line) | 5+ episodes | GRAPH_ENERGY_DIAGRAM |
| Equation box (generic highlight frame) | Every episode | EQUATION_REVEAL_BOXED |

---

## Notes for Layout Engine Implementation

1. **Subtitle reserve is inviolable.** Bottom 15–20% of frame is reserved for subtitles. No template element enters this zone. The "lower zone" for name labels sits above this reserve (roughly 75–85% height band).

2. **Safe margins.** All content starts at least 5% from left/right frame edges and 5% from top. Critical equation text starts at 10% from any edge.

3. **Character illustrations never overlap equations.** If a CHARACTER_PORTRAIT appears alongside an EQUATION_REVEAL, the character occupies the left 40% and the equation occupies the right 50% with clear separation.

4. **Comparison templates are always symmetric.** Both panels in COMPARISON_SPLIT must be equal width. Do not make one panel larger than the other even if the content is more complex — this creates misleading visual hierarchy.

5. **Tables are never partially off-screen.** DATA_TABLE must fit entirely within the safe zone in one frame. If a table is too long, split it across two sequential frames.

6. **Derivation scenes progress top-to-bottom.** New lines always appear BELOW previous lines, never replacing them (until the final result is isolated). Maximum 6 lines before a new "clean" frame starts.

7. **Graph axes always have units.** GRAPH_PLOT scenes must label both axes with variable name and units. Unlabeled axes are not permitted.

8. **Boxed results use consistent styling.** The EQUATION_REVEAL_BOXED variant should use the same box style across all episodes — a colored border (primary series color) with slight background fill.
