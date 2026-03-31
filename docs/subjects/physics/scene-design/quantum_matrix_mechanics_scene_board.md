# Quantum Matrix Mechanics Scene Board

Pilot episode:

- Chosen script: `/Users/billy/Desktop/projects/science_education/output/physics/04_quantum_mechanics/03_matrix_mechanics/ep5_uncertainty_principle/scripts/ep5_youtube_long.md`
- Working title: `The Uncertainty Principle`
- Style system: `21_storybook_visual_style_guide.md`

This board translates the script into reusable scene beats for the storybook-style production pipeline.

Design intent:

- keep the visuals warm and editorial, not sterile
- use cute historical/science motifs for intuition
- switch to precise diagrams and equation overlays whenever the math becomes the point
- reserve the lower third for captions in every shot

---

## Scene Board

| # | Narration Beat | Scene Type | Layout Notes | Assets | Motion | Accuracy Notes |
|---|---|---|---|---|---|---|
| 1 | Open on the claim that squeezing position makes momentum spread out, and that this is not a microscope story but a theorem about states and noncommuting operators. | `hook_card` | Full-frame warm cream or butter-yellow title card with one central wavepacket illustration and a bold headline. Keep the lower third open for subtitles. Use a small side medallion for `\u0394x` and `\u0394p`. | `bg_warm_cream`, wavepacket icon, small operator symbols, optional Heisenberg silhouette badge. | Slow pop-in of the headline, then a gentle wave ripple across the packet. | Do not imply measurement error. The opening claim must frame uncertainty as a property of states, not instruments. |
| 2 | Introduce the general uncertainty relation and define the symbols carefully. | `equation_focus` | Neutral paper-tan or cream background. Large centered inequality with each term boxed or pointed to by friendly labels. Put definitions in a compact right-side note column. | `obj_equation_card`, label stickers for `\u0394A`, `\u0394B`, expectation value, commutator symbol. | Equation builds in two or three steps, then labels land one by one. | Make the relation look like a theorem, not a slogan. Keep notation exact. |
| 3 | Specialize to position and momentum, giving `\u0394x \u0394p \u2265 \u0127/2`, and name it the famous Heisenberg principle. | `comparison_split` | Left panel: narrow position wavepacket squeezed in space. Right panel: broad momentum distribution shown as repeated arrows or bars. Center ribbon holds the inequality. | Position packet graphic, momentum spread graphic, ribbon label, optional Heisenberg portrait medallion. | Panels slide apart slightly to reveal the tradeoff; momentum bars fan outward. | Show that the same state cannot be arbitrarily sharp in both variables. Avoid suggesting one panel is a separate experiment. |
| 4 | Explain the derivation route using shifted operators and the geometric meaning of spread in Hilbert space. | `diagram_explain` | Use a clean chalkboard-style inset inside the storybook palette. Place `\tilde A` and `\tilde B` near the top, with a small vector-space sketch below. Keep math large and uncluttered. | Vector-space diagram, operator cards, expectation-value marker, simple Hilbert-space grid. | Brace labels and arrows appear sequentially; vectors are drawn from the state point. | Keep the derivation faithful to the Cauchy-Schwarz route. Do not collapse the proof into hand-wavy “observer effect” language. |
| 5 | Work through the harmonic-oscillator Gaussian ground state and show it saturates the bound. | `worked_example` | Split the frame: left side shows the Gaussian wavefunction on a soft graph; right side shows the product `\u0394x \u0394p = \u0127/2` in a highlighted box. Use the middle as a bridge from shape to inequality. | Gaussian curve, oscillator icon, axis graph, boxed result card. | Curve draws in from the center, then the bound box lands with a gentle stamp motion. | State clearly that this is a minimum-uncertainty state, not a generic statement about all states. |
| 6 | Use the Bohr-radius estimate to show why localization has real atomic-scale energy consequences. | `graph_plot` | Graph/estimate scene with a horizontal scale bar for `a_0`. Put the energy estimate in a small side box and a tiny hydrogen atom illustration in the corner. | `a_0` ruler graphic, hydrogen atom icon, energy estimate box, momentum arrow. | The ruler zooms from atom scale to a smaller localization interval; the estimate writes itself in. | Keep the estimate approximate and labeled as such. The point is scale, not exact derivation. |
| 7 | Cut off misconceptions: uncertainty is not just ignorance, not a license for anything-goes, and energy-time is subtler than position-momentum. | `comparison_split` | Three-column myth-vs-fact board-book layout. Left column: misconception icon; middle: corrected statement; right: minimal supporting visual. Keep text large and brief. | Warning icons, microscope icon crossed out, clock icon with note, operator/state icon. | Each misconception flips into the corrected version with a soft card turn. | The energy-time panel must say that `\u0394t` is a timescale in the ordinary statement, not a position-like operator uncertainty. |
| 8 | Explain the Fourier picture: a narrow packet in space requires many wavelengths, so momentum spreads out. | `motion_animation` | Wide horizontal scene with a packet compressing and expanding. Put a wavelength ribbon above and a momentum-bar fan below. This should feel tactile and paper-cut, not technical. | Wavepacket animation, wavelength stripes, momentum bars, small caption tag for Fourier relation. | Packet narrows, then the wavelength pattern multiplies; momentum bars fan wider. | Keep the visual correspondence exact: localized in one representation means delocalized in the conjugate one. No mystical language. |
| 9 | Summarize the historical microscope story as a helpful bridge, then state its limit compared with the modern operator derivation. | `historical_setting` | Storybook laboratory vignette with a retro gamma-ray microscope on a desk, Heisenberg as a small character silhouette, and a split note showing “helpful picture” versus “deeper reason.” | Microscope prop, tiny electron dot, classical lab accessories, note cards. | A photon beam flashes toward the electron, then the scene pauses and a note card slides over it. | Make clear that the microscope is pedagogical. The modern reason is noncommuting operators plus Hilbert-space geometry. |
| 10 | Close by connecting uncertainty to the classical limit and teeing up measurement problem. | `outro_bridge` | End card with a soft timeline from `\u0127`-scale to classical scale. Use a small bridge graphic leading into the next episode’s question about measurement. | Timeline strip, classical arrow, next-episode teaser card, subtle commutator badge. | The quantum symbols fade while the classical line grows stronger; teaser card gently slides in. | Preserve the limit statement: commutators shrink, uncertainty bounds shrink, and classical mechanics reappears as `\u0127 \u2192 0`. |

---

## Reusable Scene Kit For This Episode

This pilot should generate a small reusable kit for later quantum episodes:

- `hook_card`
- `equation_focus`
- `comparison_split`
- `diagram_explain`
- `worked_example`
- `motion_animation`
- `historical_setting`
- `outro_bridge`

These templates should be kept in the board-book palette from `21_storybook_visual_style_guide.md`, with precise scientific overlays layered on top when needed.

---

## Production Notes

The episode should not be produced as a flat sequence of static slides. The visual rhythm should alternate between:

- narrative cards
- equation reveals
- visual analogies
- precise derivation scenes
- myth-busting comparison panels
- one or two stronger motion beats

That keeps the content readable while still feeling like a designed video, not a lecture deck.

The most important discipline in this episode is to avoid collapsing uncertainty into “measurement noise.” The board should always show the cause as mathematical structure, not clumsy instrumentation.
