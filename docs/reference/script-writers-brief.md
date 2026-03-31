# Script Writer's Brief
## The Story Behind the Equation — Physics Series

**Version:** 1.0
**Applies to:** All script writer agents across all 41 physics topics
**Authority:** Postgraduate Physics Curriculum Auditor

---

## 1. The Channel's Promise

> "Tell the idea like a story. Teach the subject like a postgraduate course."

Every episode must honour both halves of that promise simultaneously. The story half means: historical development, real people, real problems, human drama. The postgraduate half means: correct equations, honest derivations, worked examples, and a clear account of where the theory breaks down.

Neither half is optional. An episode that is historically vivid but mathematically evasive fails. An episode that is technically correct but narratively dry also fails.

---

## 2. Depth Standard

**Postgraduate depth** on this channel means:

- Equations are introduced in the form a graduate student would see them in a serious textbook (Kleppner & Kolenkow, Griffiths, Sakurai, Jackson, Goldstein, Carroll, Peskin & Schroeder — choose the appropriate reference for the topic).
- Every symbol is defined the first time it appears in an episode. Not just named — explained physically. "m is mass in kilograms" is insufficient. "m is the resistance an object offers to a change in its velocity — heavier means harder to accelerate" is what is required.
- Derivations are shown step-by-step, in plain language between each line. Do not skip algebra and say "it can be shown." Show it, and say what each step means.
- Approximations and limits are named and justified. If you use the non-relativistic limit, say so. If you use the weak-field limit, say so.
- The episode must address at least one place where the equation or theory fails or reaches its boundary.

**This is not a popularisation channel.** It is an education channel that uses storytelling technique. The distinction matters: a popularisation may use a loose analogy in place of an equation. This channel uses the analogy to motivate the equation, then gives the equation.

---

## 3. The 4-Block Episode Structure

Every episode plan follows four blocks. Individual episodes fall within one or more blocks. A complete topic series must contain all four blocks.

### Block A — The Story (historical drama)
Build intuition before equations. Introduce the human problem. Show what earlier thinkers believed and why they were reasonable given their evidence. Create dramatic tension around the gap between the old idea and the new one.

- No derivations required in Block A episodes.
- Analogies should be vivid and physically honest — they will be used again when the equations arrive.
- Block A episodes must end with a forward hook that names the equation or concept coming next.

### Block B — The Equations (derivation and application)
Introduce, derive, and apply the key equations. Each Block B episode should introduce exactly one equation or derivation thread.

Required content for every Block B episode:
1. The equation stated clearly in LaTeX-style inline notation.
2. Every symbol defined, with units and physical meaning.
3. The derivation walked through step-by-step (or the key steps if the full derivation is too long — but never skipped entirely).
4. At least one worked numerical example with real numbers, units, and a physical interpretation of the answer.
5. The historical origin of the equation — who wrote it first, in what form, and how it differs from the modern version.

### Block C — The Limits
Show where the equations stop working. What is the domain of validity? What experiment or phenomenon first revealed the failure? What replaced the theory in that regime, and how does the old theory emerge as a limiting case?

- This block prevents false confidence. Students who can apply F=ma without knowing it fails at v ~ c are not educated — they are trained.
- Every limits episode should contain the quantitative boundary: not just "Newton fails at high speeds" but "Newton's momentum error exceeds 1% at v > 0.14c."

### Block D — The Deeper Truth
Connect the topic to the broader structure of physics. Show how the equations of this topic emerge from, or feed into, a more fundamental framework. Common threads: symmetry and Noether's theorem, the least action principle, the correspondence principle, renormalization group flow, gauge invariance.

- This block should excite the viewer about what comes next in the curriculum.
- It should name the next topic explicitly in the forward hook.

---

## 4. What Every Episode MUST Contain

Regardless of which block an episode belongs to, every episode must include at least one of the following four depth elements. Block B episodes must include all four.

| Depth element | What it means |
|---|---|
| Equation introduced | The central equation of the episode, written in full with all symbols |
| Derivation walked through | At least the key logical steps, with one sentence of physical meaning after each step |
| Worked example | A real numerical problem solved to a numerical answer with units |
| Physical meaning statement | A plain-language sentence that says what the equation is actually asserting about nature |

A "physical meaning statement" is NOT the same as restating the equation in words. "F = ma means force equals mass times acceleration" is not a physical meaning statement. "F = ma means that if you want to accelerate a larger mass by the same amount, you need a proportionally larger force — and the relationship is exactly linear, not approximate" IS a physical meaning statement.

---

## 5. The Content Funnel

Each episode generates four outputs. They are NOT equal in importance. The YouTube Long video is the real product. Everything else is a funnel into it.

### 5.1 YouTube Long (8–15 minutes) — The Core Teaching

This is where the real physics happens. Full depth. Do not compromise here for the sake of short-form appeal.

Required:
- Complete 4-block structure or a clearly placed position within the topic's arc
- All equations introduced with derivations and symbol-by-symbol explanation
- Worked example with numbers, units, and physical interpretation
- Historical development with named figures and dates
- At least one citation to a primary source or standard textbook
- Clear statement of where the theory breaks down

Tone: warm, precise, story-driven but technically honest.

### 5.2 YouTube Short / TikTok (30–90 seconds) — The Dramatic Hook

ONE idea. ONE surprising fact, paradox, or "you were taught wrong" moment. NO equations on screen. No derivations.

Rules:
- The hook must be extracted from the opening of the long script — it is not invented separately.
- Must create genuine intellectual discomfort or surprise. "Did you know Newton's laws are wrong?" is too vague. "F=ma. Every physicist knows it. Newton never wrote it." is specific enough to create genuine curiosity.
- Must end with a direct verbal call-to-action to the long video: "The full derivation and the real story is in the long video — link in bio."
- Maximum one analogy.
- Do not attempt to resolve the paradox or complete the explanation in the short. The short is a question, not an answer.

### 5.3 X Post — The Single Most Surprising Sentence

1–3 sentences. Extract the single most surprising or counterintuitive fact from the episode. The goal is a post that an educated person who does not follow the channel would repost because it is genuinely interesting, not because it is clickbait.

Rules:
- Must be a real fact, not a teaser question.
- Inline notation is acceptable if essential: "F = dp/dt, not F = ma — that is what Newton actually wrote" is fine.
- No hashtag stuffing. One or two topic-relevant hashtags at most.
- Do not summarise the episode. Extract one gem.

---

## 6. Notation Standards

Use LaTeX-style inline notation throughout all scripts. The rendering pipeline handles formatting. Writers must use consistent symbols.

### Core notation rules:

- Write equations inline as they would appear in a textbook: `F = dp/dt`, `E = γmc²`, `iℏ ∂ψ/∂t = Ĥψ`
- Greek letters spelled out in running text when the symbol is not available: "the Lorentz factor gamma" — but use γ in equation lines
- Partial derivatives: `∂L/∂q`
- Vectors in bold or with arrow: **F** or F⃗ — be consistent within a topic
- Operators with hat: Ĥ, p̂, x̂
- Indices: subscript notation `F_μν`, superscript for contravariant `x^μ`
- Do NOT write equations in words: "F equals dp over dt" is not acceptable in a Block B script. Write `F = dp/dt`.
- When introducing a new symbol, always follow it immediately with: symbol, pronunciation if non-obvious, units, physical meaning.

Example of correct symbol introduction:

> "Newton's second law in its original form: **F = dp/dt**. Here F is the net force in Newtons — the total push or pull on the object. p is momentum, in kg·m/s — the quantity Newton called 'the quantity of motion.' And dp/dt is the time derivative of momentum — how fast the momentum is changing at this instant."

---

## 7. Citation Requirements

### Required for every episode:
- At minimum: one primary or historically close source + one standard textbook reference
- Historical claims (who discovered what, when, in what form) must be cited to a specific source
- Equations presented as historical originals must be verified against the actual original work, not a secondary account

### Citation hierarchy:
1. **Primary source** — the original paper or book (e.g., Newton's *Principia*, 1687; Dirac, *Proc. Royal Soc.*, 1928)
2. **Standard graduate textbook** — for the modern pedagogical form (e.g., Griffiths *Introduction to Electrodynamics* 4th ed.; Peskin & Schroeder *An Introduction to Quantum Field Theory*)
3. **Historical secondary source** — for historical narrative context (e.g., Whittaker *A History of the Theories of Aether and Electricity*; Pais *Subtle is the Lord*)

### What must be cited:
- Any specific date, year, or historical priority claim
- Any claim that the historical form of an equation differs from the modern form
- Any quantitative claim about experimental measurement
- Any claim about what a historical figure believed or wrote

### What does not need a citation:
- Well-established modern physics (F = ma, Maxwell's equations in SI form, Schrödinger's equation)
- Standard mathematical derivations available in multiple textbooks
- Logical consequences of already-cited equations

### Citation format in scripts:
Place citations in square brackets at the end of the sentence: [Newton, *Principia* 1687, Lex II]
Full references go in a separate References section at the end of the script document.

---

## 8. Tone Rules

### The three-word summary: warm, precise, never condescending.

**Warm** means:
- The narrator is genuinely excited about the physics.
- Historical figures are treated as intelligent people solving hard problems, not as heroes or caricatures.
- The viewer's confusion is anticipated and addressed directly: "This is the part that trips most people up. Let's slow down here."

**Precise** means:
- No analogy replaces an equation. Every analogy is a bridge to the equation.
- Approximations are named. "This is exact" and "this is an approximation good to within 1% at everyday speeds" are different statements and must be treated differently.
- "It can be shown" is almost never acceptable. Show it, or say honestly "the full proof requires tools we haven't covered yet — it comes in Episode N."

**Never condescending** means:
- Do not congratulate the viewer for following along.
- Do not use the phrase "simply" or "just" before a non-trivial step.
- Do not explain what multiplication is.
- Treat the viewer as a capable adult who is encountering this material for the first time.

**Additional tone rules:**
- Do not use the word "fascinating" or "amazing" as filler. If something is surprising, explain WHY it is surprising.
- Do not open with a rhetorical question unless it is a genuinely hard question with a specific, non-obvious answer.
- Avoid passive voice in narration. "Newton showed" not "it was shown by Newton."
- Avoid "we" when it creates false inclusivity. Use "you" when addressing the viewer directly and the narrator's voice when explaining.

---

## 9. Reference Episode: Newton's Laws, Episode 5

Use this as the template for a well-constructed Block B episode.

**Episode:** "What Newton Actually Wrote" (Newton's Laws of Motion, ep05)
**File:** `/Users/billy/Desktop/projects/science_education/output/physics/01_classical_mechanics/01_newtons_laws/episodes/episode_plan_v2.md`

Why this episode is a model:

1. **Hook that names a real surprise:** "F=ma. Every student knows it. But Newton never wrote it." — This is specific, verifiable, and genuinely counterintuitive.

2. **Historical claim with named authority:** Attributes F = dp/dt to Newton (1687) and the simplification F = ma to Euler (1736). This is not vague — it names who, what, and when.

3. **Derivation with narrated steps:** Starts from F = Δp/Δt, takes the limit to get F = dp/dt, then shows F = ma as the special case where mass is constant. Each step is a separate numbered line with physical meaning.

4. **The failure case is in the same episode:** Shows that F = ma fails for a rocket (changing mass), while F = dp/dt continues to work. This prevents the viewer from over-generalising.

5. **Two worked examples with real numbers:** (a) Ball bouncing off wall — force of 900 N calculated from momentum change and contact time. (b) Rocket — qualitative explanation of why F = ma fails. Both examples have physical interpretations of the numerical answers.

6. **Forward hook that builds on the episode's content:** "Force changes momentum. But where does force come from?" — This is answerable from the episode's content and sets up Episode 6.

**Template structure extracted from ep05:**

```
HOOK: [specific verifiable surprise]
HISTORY: [named figure, year, what they actually wrote]
EQUATION STATEMENT: [full equation with all symbols defined]
DERIVATION: [numbered steps, one sentence of meaning after each]
WORKED EXAMPLE 1: [numerical, physical interpretation of answer]
WORKED EXAMPLE 2: [shows a limit or failure of the equation, or a contrasting case]
KEY CLAIM: [one sentence that is the main takeaway]
FORWARD HOOK: [one sentence that makes the next episode feel necessary]
REFERENCES: [primary + textbook]
```

---

## 10. The Deeper Purpose

Each topic in this curriculum ends with a Block D episode that connects the topic to the next level of abstraction. As a writer, you must understand the ladder:

```
Newton's Laws (F = dp/dt)
    ↓ generalises to
Lagrangian Mechanics (Euler-Lagrange equations)
    ↓ generalises to
Hamiltonian Mechanics (Hamilton's equations, phase space)
    ↓ connects to
Quantum Mechanics (canonical quantization: {q,p}→[q̂,p̂] = iℏ)
    ↓ generalises to
Quantum Field Theory (fields replace particles, Fock space)
    ↓ structured by
Symmetry (Noether's theorem, gauge invariance)
```

Every Block D episode should show one rung of this ladder explicitly. The viewer should finish Block D knowing what lies above the current topic and how to get there.

---

## 11. Quality Gates

Before submitting a script, verify:

- [ ] Every equation has all symbols defined
- [ ] At least one worked example with numerical answer and units
- [ ] At least one citation to a primary or textbook source
- [ ] The historical form of the equation is distinguished from the modern form
- [ ] At least one sentence states where the theory or equation breaks down
- [ ] The short-form hook is extracted from the long script's opening, not invented separately
- [ ] No use of "simply," "just," "obviously," "it is easy to show"
- [ ] Forward hook at the end of the episode names the next concept explicitly
- [ ] All notation is consistent with the notation standards in Section 6

---

*This brief is a living document. If a topic requires notation or structural adjustments not covered here, flag it before writing — do not improvise silently.*
