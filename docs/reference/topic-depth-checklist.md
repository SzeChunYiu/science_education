# Topic Depth Checklist
## The Story Behind the Equation — Physics Series

**Version:** 1.0
**Purpose:** For each of the 41 curriculum topics, this document confirms or expands the episode count, specifies mandatory equations, key historical figures and their specific contributions, and maps connections to adjacent topics.

Topics flagged with [EXPAND] need more episodes than currently planned. Topics marked [OK] are adequately covered. Topics marked [CRITICAL] are foundational for QFT and must not be under-developed.

---

## Module 1: Classical Mechanics

---

### Topic 01: Newton's Laws of Motion [OK — expanded to 12 ep]

**Current plan:** 12 episodes (expanded from 7)
**Assessment:** Adequate. The ep01–ep12 plan in `episode_plan_v2.md` is the template for the series.

**Mandatory equations:**
- `p = mv` (momentum definition)
- `F = dp/dt` (Newton's original second law)
- `F = ma` (Euler's simplification, valid only for constant mass)
- `F_AB = -F_BA` (third law)
- `ΣF = 0 ⟹ v = constant` (first law / inertial frames)
- `p = γmv` (relativistic momentum — limit episode)
- `Δx · Δp ≥ ℏ/2` (quantum boundary — limit episode)
- `d/dt(∂L/∂q̇) - ∂L/∂q = 0` (Euler-Lagrange preview in Block D)

**Mandatory historical figures and specific contributions:**
- Aristotle (~350 BC): natural vs forced motion; impetus theory
- Philoponus (6th c. AD): first critique of Aristotle's dynamics
- Buridan (14th c.): impetus theory — momentum-like precursor
- Galileo (1589–1632): uniform acceleration, d ∝ t², inertia principle, inclined plane
- Descartes (1644): first clear statement of inertia as rectilinear
- Newton (1687): *Principia* — three laws in terms of momentum; F = dp/dt
- Euler (1736): reformulated second law as F = ma for point masses
- Emmy Noether (1918): conservation laws from symmetries

**Connections:**
- Feeds into: Topic 02 (Conservation Laws), Topic 05 (Lagrangian Mechanics)
- Returns from: Topic 28 (Cosmology — GR reduces to Newtonian gravity in weak field)
- Quantum limit: Topic 20 (Wave Mechanics), Topic 21 (Matrix Mechanics)

---

### Topic 02: Conservation Laws [OK]

**Current plan:** ~6 episodes
**Assessment:** Adequate, but ensure the Noether connection is quantitative, not just verbal.

**Mandatory equations:**
- `p_total = constant` (when ΣF_ext = 0)
- `E_k = ½mv²` (kinetic energy)
- `W = ∫F·ds` (work-energy theorem integral form)
- `E_k + V = E_total = constant` (conservation of mechanical energy)
- `L = r × p` (angular momentum definition)
- `dL/dt = τ` (torque as rate of change of angular momentum)
- `δS = 0` (principle of least action — preview of Noether's content)
- Noether's theorem statement: for each continuous symmetry of the action, there is a conserved current `j^μ` with `∂_μ j^μ = 0`

**Mandatory historical figures:**
- Leibniz (1686): vis viva = mv² — precursor to kinetic energy, dispute with Cartesians over conservation of momentum vs vis viva
- d'Alembert (1743): principle reconciling Leibniz and Newton
- Lagrange (1788): generalized coordinates and conservation via symmetry
- Noether (1918): theorem connecting symmetry to conservation — this is the conceptual climax of the topic

**Connections:**
- Feeds into: Topic 05 (Lagrangian Mechanics — action principle), Topic 34 (Classical Field Theory — Noether for fields)
- Prerequisite for: Topic 22 (Angular Momentum and Spin)

---

### Topic 03: Gravity and Orbits [OK]

**Current plan:** ~7 episodes
**Assessment:** Adequate. Must include the full Newtonian derivation of Kepler's third law from F = GMm/r².

**Mandatory equations:**
- `F = GMm/r²` (Newton's law of gravitation)
- Kepler's three laws: (1) elliptical orbits, (2) equal areas equal times (`dA/dt = L/2m = constant`), (3) `T² ∝ a³` (derive from circular orbit as pedagogical simplification, then generalise)
- `g = GM/R²` (surface gravity)
- `v_escape = √(2GM/R)` (escape velocity)
- `E = -GMm/2a` (total energy of elliptical orbit)
- Schwarzschild radius `r_s = 2GM/c²` (as a preview of GR limits)

**Mandatory historical figures:**
- Ptolemy (2nd c.): geocentric epicycles — show why they worked numerically
- Copernicus (1543): heliocentric model — but still circular orbits
- Brahe (1580s): precision naked-eye data that forced Kepler's hand
- Kepler (1609, 1619): three laws from Brahe's data — 10 years of computation
- Newton (1687): derived Kepler's laws from inverse-square gravity
- Cavendish (1798): measured G — make clear Newton never had a numerical value for G

**Connections:**
- Feeds into: Topic 08 (Central Force Problems), Topic 13 (Special Relativity — perihelion of Mercury), Topic 27 (General Relativity)

---

### Topic 04: Oscillations and Waves [OK]

**Current plan:** ~6 episodes
**Assessment:** Adequate, but the wave equation derivation must be explicit — do not just state it.

**Mandatory equations:**
- `F = -kx` (Hooke's law)
- `d²x/dt² + ω²x = 0` (SHM equation — derive from F = ma)
- `x(t) = A cos(ωt + φ)`, `ω = √(k/m)`
- `T = 2π√(m/k)`, `T = 2π√(L/g)` (pendulum — show the small-angle approximation)
- `d²x/dt² + 2βdx/dt + ω²x = 0` (damped oscillator)
- `ω_res = √(ω² - β²)` (resonance frequency)
- `∂²y/∂t² = v²∂²y/∂x²` (wave equation — derive from Newton applied to a string)
- `y(x,t) = A sin(kx - ωt)`, with `v = ω/k`

**Mandatory historical figures:**
- Hooke (1676): Ut tensio, sic vis — but the law is about springs, not stated in modern form
- Huygens (1673): pendulum clock, centripetal acceleration, wave theory of light
- Euler: string vibration and wave equation
- Fourier (1822): arbitrary periodic functions as superpositions of harmonics

**Connections:**
- Prerequisite for: Topic 12 (Electromagnetic Waves), Topic 20 (Wave Mechanics — de Broglie waves)
- Connects to: Topic 30 (Differential Equations — wave equation as PDE)

---

### Topic 05: Lagrangian Mechanics [CRITICAL]

**Current plan:** ~7 episodes
**Assessment:** Adequate if Noether's theorem is treated with full mathematical weight. This is the gateway to all of QFT.

**Mandatory equations:**
- `L = T - V` (Lagrangian — explain why T minus V, not T plus V)
- `S = ∫L dt` (action functional)
- `δS = 0` (Hamilton's principle — principle of least action)
- `d/dt(∂L/∂q̇_i) - ∂L/∂q_i = 0` (Euler-Lagrange equations — derive via calculus of variations)
- Recovery of F = ma from the Euler-Lagrange equation for a particle
- Conserved quantity from cyclic coordinate: if `∂L/∂q_i = 0` then `p_i = ∂L/∂q̇_i = constant`
- Noether's theorem (mathematical statement): if `L` is invariant under `q_i → q_i + ε·K_i(q,q̇,t)`, then `J = Σ_i (∂L/∂q̇_i)K_i` is conserved

**The derivation of Noether's theorem must be shown explicitly**, not just stated as a principle. The calculus of variations derivation of Euler-Lagrange from δS = 0 must be shown step by step (integration by parts).

**Mandatory historical figures:**
- Fermat (1662): principle of least time for light
- Maupertuis (1744): principle of least action (imprecise but first)
- Euler (1744): made least action mathematically precise
- Lagrange (1788): *Mécanique Analytique* — generalized coordinates, Lagrangian formulation
- Hamilton (1834): Hamilton's principle — δ∫L dt = 0
- Noether (1918): theorem connecting symmetries to conservation laws

**Connections:**
- Feeds into: Topic 06 (Hamiltonian Mechanics), Topic 29 (Vector Calculus), Topic 34 (Classical Field Theory)
- This topic is the structural foundation of QFT — make this explicit in Block D

---

### Topic 06: Hamiltonian Mechanics [CRITICAL]

**Current plan:** ~5 episodes
**Assessment:** Adequate, but the Poisson bracket episode is the most important for QM connection and must not be rushed.

**Mandatory equations:**
- `H = Σ_i p_i q̇_i - L` (Legendre transform — derive this, explain why)
- Hamilton's equations: `dq_i/dt = ∂H/∂p_i`, `dp_i/dt = -∂H/∂q_i`
- `{f, g} = Σ_i (∂f/∂q_i · ∂g/∂p_i - ∂f/∂p_i · ∂g/∂q_i)` (Poisson bracket — full definition)
- `{q_i, p_j} = δ_ij` (fundamental Poisson brackets)
- `df/dt = {f, H} + ∂f/∂t` (time evolution via Poisson brackets)
- Liouville's theorem: `dρ/dt = 0` in phase space (phase space volume is conserved)
- The canonical quantization bridge: `{q, p}_Poisson → [q̂, p̂]/iℏ`

**Mandatory historical figures:**
- Hamilton (1834): canonical equations, unified optics and mechanics
- Jacobi: Hamilton-Jacobi equation (preview, not full treatment)
- Poisson: brackets — important to note Poisson did not see the QM connection
- Liouville (1838): theorem on phase space volume preservation
- Dirac (1925): identified Poisson brackets as the classical analog of commutators

**Connections:**
- Feeds into: Topic 21 (Matrix Mechanics — canonical quantization), Topic 37 (Path Integrals)
- The Poisson bracket → commutator substitution is the single most important structural idea connecting classical to quantum mechanics. This must be the climax of Block D.

---

### Topic 07: Rigid Body Dynamics [OK]

**Current plan:** ~5 episodes
**Assessment:** Adequate.

**Mandatory equations:**
- `I = Σ m_i r_i²` (moment of inertia, discrete)
- `I = ∫r²dm` (continuous)
- `L = Iω` (angular momentum for rotation about fixed axis)
- `τ = Iα = dL/dt`
- Parallel axis theorem: `I = I_cm + Md²`
- Euler's equations for rotation: `I₁ω̇₁ + (I₃-I₂)ω₂ω₃ = τ₁` (and cyclic)
- Precession rate: `Ω = τ/L = Mgr/(Iω)` (gyroscope)

**Mandatory historical figures:**
- Euler (1765): rigid body equations, moment of inertia
- Poinsot (1834): geometric interpretation of free rotation (Poinsot's ellipsoid)
- Foucault (1851): pendulum as demonstration of Earth's rotation

**Connections:**
- Feeds into: Topic 22 (Angular Momentum and Spin — moment of inertia tensor connects to spin matrices)
- Connects to: Topic 05 (Lagrangian treatment of rigid body)

---

### Topic 08: Central Force Problems [OK]

**Current plan:** ~4 episodes
**Assessment:** Adequate.

**Mandatory equations:**
- `U_eff(r) = L²/2mr² + V(r)` (effective potential — this is the key concept)
- Binet equation (optional, for advanced treatment)
- Orbit equation: `r(θ) = p/(1 + e cosθ)` (conic sections from 1/r² force)
- Rutherford scattering: `dσ/dΩ = (Z₁Z₂e²/4E)² · 1/sin⁴(θ/2)`

**Mandatory historical figures:**
- Newton: two-body problem reduction to one-body problem
- Kepler: empirical orbit shapes
- Rutherford (1911): alpha scattering — show that this IS a central force problem

**Connections:**
- Prerequisite for: Topic 20 (Hydrogen atom as central force problem in QM)
- Rutherford scattering is the historical bridge to Topic 33 (Why QFT)

---

## Module 2: Electromagnetism

---

### Topic 09: Electrostatics [OK]

**Current plan:** ~6 episodes
**Assessment:** Adequate.

**Mandatory equations:**
- `F = kq₁q₂/r²` (Coulomb's law — note k = 1/4πε₀)
- `E = F/q₀` (electric field definition)
- `∮E·dA = Q_enc/ε₀` (Gauss's law integral form)
- `∇·E = ρ/ε₀` (Gauss's law differential form — derive from integral form)
- `V = -∫E·dl` (electric potential)
- `E = -∇V` (field from potential)
- `∇²V = -ρ/ε₀` (Poisson equation)

**Mandatory historical figures:**
- Thales of Miletus: amber and static electricity (earliest record)
- Franklin (1750s): one-fluid theory, charge conservation, lightning rod
- Coulomb (1785): torsion balance measurement of inverse-square law
- Gauss: divergence theorem and its application to electrostatics
- Faraday: field concept — make clear this was Faraday's innovation, not Maxwell's

**Connections:**
- Feeds into: Topic 11 (Maxwell's Equations — Gauss's law is Maxwell's first equation)
- Connects to: Topic 29 (Vector Calculus — divergence theorem)

---

### Topic 10: Magnetostatics [OK]

**Current plan:** ~5 episodes
**Assessment:** Adequate.

**Mandatory equations:**
- `F = qv × B` (Lorentz force — magnetic part)
- `dB = (μ₀/4π)(Idl × r̂)/r²` (Biot-Savart law)
- `∮B·dl = μ₀I_enc` (Ampère's law integral form)
- `∇×B = μ₀J` (Ampère's law differential form)
- `∇·B = 0` (no magnetic monopoles — this is Maxwell's second equation)
- `A` (vector potential: `B = ∇×A`)

**Mandatory historical figures:**
- Gilbert (1600): *De Magnete* — Earth as a magnet
- Oersted (1820): current deflects compass — accidental discovery, reported publicly
- Biot and Savart (1820): quantified magnetic field from current (same year as Oersted)
- Ampère (1820–1827): mathematical theory of magnetism, force between currents

**Connections:**
- Feeds into: Topic 11 (Maxwell added displacement current to Ampère's law)

---

### Topic 11: Electrodynamics and Maxwell's Equations [CRITICAL — EXPAND]

**Current plan:** ~8 episodes
**Assessment: EXPAND to 12 episodes.** This is the most important topic in Module 2. Each of Maxwell's four equations warrants its own dedicated episode with full derivation from first principles. The current 8-episode plan does not allow for this.

**Recommended episode structure:**
1. Faraday's induction — the experiment and the law (historical Block A)
2. Faraday's law: `∇×E = -∂B/∂t` — full derivation and worked example
3. The problem with Ampère's law — inconsistency with charge conservation
4. Maxwell's displacement current — the fix and its physical meaning
5. Ampère-Maxwell law: `∇×B = μ₀J + μ₀ε₀∂E/∂t` — derivation and meaning
6. Gauss's law for E: `∇·E = ρ/ε₀` — derivation and worked example
7. Gauss's law for B: `∇·B = 0` — what this says about magnetic monopoles
8. Maxwell's equations unified — the four equations together in integral and differential form
9. Electromagnetic wave derivation — show how `∇²E = μ₀ε₀∂²E/∂t²` emerges from the four equations
10. The speed of light from Maxwell: `c = 1/√(μ₀ε₀)` — the calculation and its meaning
11. Hertz's experiment (1887) — experimental confirmation of EM waves
12. Maxwell to modern physics: gauge invariance preview, connection to QED

**The four Maxwell equations must each have a dedicated derivation episode. This is non-negotiable.**

**Mandatory equations (all four Maxwell equations in both integral and differential form):**

Gauss's law for E:
- `∮E·dA = Q_enc/ε₀`
- `∇·E = ρ/ε₀`

Gauss's law for B (no monopoles):
- `∮B·dA = 0`
- `∇·B = 0`

Faraday's law:
- `∮E·dl = -dΦ_B/dt`
- `∇×E = -∂B/∂t`

Ampère-Maxwell law:
- `∮B·dl = μ₀I_enc + μ₀ε₀dΦ_E/dt`
- `∇×B = μ₀J + μ₀ε₀∂E/∂t`

Wave equation derivation from Maxwell (must be shown step by step):
- `∇²E = μ₀ε₀ ∂²E/∂t²`
- `c = 1/√(μ₀ε₀) = 3×10⁸ m/s`

In covariant form (Block D):
- `∂_μ F^μν = μ₀ J^ν`
- `∂_μ F̃^μν = 0`

**Mandatory historical figures:**
- Faraday (1831): electromagnetic induction — key: Faraday thought in terms of field lines, not equations
- Maxwell (1861–1865): displacement current (1861), *Treatise* (1873) — 20 equations in original form
- Heaviside (1884–1885): reduced Maxwell's 20 equations to the modern 4 using vector calculus
- Hertz (1887): experimental confirmation of EM waves; measured their speed
- Lorentz: EM in moving media, transformation equations (precursor to SR)

**Connections:**
- Feeds into: Topic 12 (EM Waves), Topic 13 (Special Relativity — Maxwell's equations are Lorentz-invariant), Topic 36 (QED — quantization of the EM field)

---

### Topic 12: Electromagnetic Waves and Optics [OK]

**Current plan:** ~5 episodes
**Assessment:** Adequate.

**Mandatory equations:**
- `∇²E - μ₀ε₀∂²E/∂t² = 0` (EM wave equation)
- `E = E₀ cos(kx - ωt)`, `B = B₀ cos(kx - ωt)` with `E₀ = cB₀`
- Poynting vector: `S = (1/μ₀) E × B` (energy flux)
- Snell's law derived from EM boundary conditions (not just stated)
- Fresnel equations (reflection/transmission coefficients)
- Malus's law for polarization

**Connections:**
- Feeds into: Topic 13 (SR — light speed is frame-independent), Topic 19 (Blackbody radiation — EM modes in a cavity)

---

### Topic 13: Special Relativity (from EM) [OK]

**Current plan:** ~7 episodes
**Assessment:** Adequate. The derivation of Lorentz transformations from Maxwell's equations (not just from the two postulates) should appear in at least one episode.

**Mandatory equations:**
- `x' = γ(x - vt)`, `t' = γ(t - vx/c²)` (Lorentz transformations)
- `γ = 1/√(1 - v²/c²)` (Lorentz factor)
- `Δt = γΔτ` (time dilation)
- `L = L₀/γ` (length contraction)
- `E² = (pc)² + (mc²)²` (energy-momentum relation — derive, not just state)
- `E = γmc²`, `p = γmv`
- `E = mc²` as special case when p = 0
- Minkowski metric: `ds² = -c²dt² + dx² + dy² + dz²`

**Mandatory historical figures:**
- Michelson and Morley (1887): null result — explain the interferometer in detail
- FitzGerald (1889) and Lorentz (1892): ad hoc length contraction to explain MM result
- Poincaré (1905): near-simultaneous development
- Einstein (1905): two postulates approach, *Annalen der Physik*
- Minkowski (1908): spacetime geometry — Einstein initially disliked it

**Connections:**
- Feeds into: Topic 26 (Special Relativity deep), Topic 27 (General Relativity), Topic 33 (Dirac equation)

---

## Module 3: Thermodynamics and Statistical Mechanics

---

### Topic 14: Classical Thermodynamics [OK]

**Current plan:** ~7 episodes
**Assessment:** Adequate.

**Mandatory equations:**
- Zeroth law: transitivity of thermal equilibrium (statement)
- First law: `ΔU = Q - W` (note sign convention — state which one is used)
- Carnot efficiency: `η = 1 - T_cold/T_hot` — derive from Carnot cycle analysis
- Second law: `dS ≥ δQ/T` (Clausius inequality)
- `S = -dF/dT` where `F = U - TS` (Helmholtz free energy)
- Third law: `S → 0` as `T → 0` (Nernst heat theorem)

**Mandatory historical figures:**
- Carnot (1824): ideal heat engine efficiency — derived from caloric theory (wrong model, right result!)
- Clausius (1850, 1865): first and second laws in modern form; coined "entropy"
- Kelvin (1851): second law — no process extracts work from single reservoir
- Joule (1843): mechanical equivalent of heat
- Nernst (1906): third law

**Connections:**
- Feeds into: Topic 15 (Kinetic Theory — microscopic basis of temperature), Topic 16 (Statistical Mechanics)

---

### Topic 15: Kinetic Theory [OK]

**Current plan:** ~5 episodes
**Assessment:** Adequate.

**Mandatory equations:**
- `PV = NkT` (ideal gas law — derive from collisions, not just state)
- `P = ½nm⟨v²⟩` (pressure from momentum transfer — the derivation)
- `½m⟨v²⟩ = 3/2 kT` (equipartition for translation)
- `f(v) = 4π(m/2πkT)^(3/2) v² exp(-mv²/2kT)` (Maxwell-Boltzmann distribution)
- Mean free path: `λ = 1/(√2 nπd²)`

**Mandatory historical figures:**
- Bernoulli (1738): kinetic model of gas pressure
- Clausius (1857): mean free path
- Maxwell (1860): velocity distribution — the first statistical law in physics
- Boltzmann (1872): H-theorem, approach to equilibrium

**Connections:**
- Feeds into: Topic 16 (Statistical Mechanics — Maxwell-Boltzmann as a canonical ensemble result)

---

### Topic 16: Statistical Mechanics — Classical [CRITICAL]

**Current plan:** ~7 episodes
**Assessment:** Adequate if the partition function derivation is done carefully.

**Mandatory equations:**
- `S = k ln W` (Boltzmann entropy — define W as number of microstates)
- Canonical ensemble: `P_i = e^(-βE_i)/Z` where `β = 1/kT`
- Partition function: `Z = Σ_i e^(-βE_i)`
- `F = -kT ln Z` (free energy from partition function)
- `⟨E⟩ = -∂ ln Z/∂β`
- `S = k(ln Z + β⟨E⟩)`
- Grand canonical: `Ω = -kT ln Z_grand`

**The derivation of the Boltzmann factor from maximizing entropy subject to constraints (Lagrange multipliers) must be shown.** This is the core of statistical mechanics and is often skimmed.

**Mandatory historical figures:**
- Boltzmann (1872–1884): H-theorem, entropy as log of microstates, kinetic equation — the controversy with Loschmidt and Zermelo
- Gibbs (1902): *Elementary Principles in Statistical Mechanics* — canonical ensemble, partition function, ensembles
- Einstein (1905): Brownian motion as experimental proof of atoms

**Connections:**
- Feeds into: Topic 17 (Quantum Stat Mech), Topic 38 (Renormalization Group — Wilson's approach uses stat mech ideas)

---

### Topic 17: Statistical Mechanics — Quantum [CRITICAL]

**Current plan:** ~6 episodes
**Assessment:** Adequate. Blackbody radiation must be derived properly — the Planck distribution from the quantum harmonic oscillator partition function.

**Mandatory equations:**
- `⟨n⟩_BE = 1/(e^(β(ε-μ)) - 1)` (Bose-Einstein distribution)
- `⟨n⟩_FD = 1/(e^(β(ε-μ)) + 1)` (Fermi-Dirac distribution)
- Planck distribution: `u(ω) = (ℏω³/π²c³) · 1/(e^(ℏω/kT) - 1)` (derive from harmonic oscillator partition function)
- `E_F = (ℏ²/2m)(3π²n)^(2/3)` (Fermi energy)
- BEC transition temperature: `T_c = (2πℏ²/mk)(n/ζ(3/2))^(2/3)`

**Mandatory historical figures:**
- Planck (1900): blackbody radiation — honest account that Planck did not believe his own quantization at first
- Bose (1924): new statistics for photons — sent to Einstein, who immediately saw its significance
- Einstein (1924): extended Bose statistics to atoms, predicted condensation
- Fermi (1926) and Dirac (1926): independently derived Fermi-Dirac statistics

**Connections:**
- Feeds into: Topic 23 (Identical Particles and Atoms), Topic 19 (Origins of Quantum Theory — historical root of Planck's insight)

---

### Topic 18: Phase Transitions [OK]

**Current plan:** ~5 episodes
**Assessment:** Adequate. The renormalization group preview in the final episode must be substantive, not hand-wavy.

**Mandatory equations:**
- Ising model Hamiltonian: `H = -J Σ_{⟨ij⟩} s_i s_j - h Σ_i s_i`
- Mean field result: `m = tanh(β(zJm + h))`
- Critical exponents: define β, γ, ν, η — show that mean field gives β = 1/2, exact 2D Ising gives β = 1/8
- Scaling hypothesis: `F(t, h) = |t|^(2-α) f(h/|t|^Δ)` (introduce, do not derive)

**Mandatory historical figures:**
- van der Waals (1873): equation of state with phase transition
- Ising (1925): 1D model, solved exactly — no phase transition in 1D
- Onsager (1944): exact 2D Ising solution — the tour de force
- Kadanoff (1966): block spin renormalization — conceptual picture
- Wilson (1971): RG as a calculational tool; Nobel 1982

**Connections:**
- Feeds into: Topic 38 (Renormalization Group — Wilson's approach is the QFT version of this)

---

## Module 4: Quantum Mechanics

---

### Topic 19: Origins of Quantum Theory [OK]

**Current plan:** ~7 episodes
**Assessment:** Adequate.

**Mandatory equations:**
- `u(ν) = 8πhν³/c³ · 1/(e^(hν/kT) - 1)` (Planck's blackbody law)
- `E = hν` (Planck-Einstein relation)
- `E_k = hν - φ` (photoelectric effect — Einstein 1905)
- `r_n = n²a₀` (Bohr radii)
- `E_n = -13.6 eV/n²` (Bohr energy levels)
- `1/λ = R_H(1/n₁² - 1/n₂²)` (Rydberg formula — derive from Bohr)
- `λ = h/p` (de Broglie wavelength)
- Compton scattering: `λ' - λ = (h/m_ec)(1 - cosθ)` — derive from energy-momentum conservation

**Mandatory historical figures:**
- Planck (1900): blackbody fix — quantization as mathematical trick
- Einstein (1905): photoelectric effect — took the quantum seriously as physical reality
- Bohr (1913): planetary atom with quantized orbits — why n²? (angular momentum quantization)
- de Broglie (1924): matter waves — derive λ = h/p from SR + Planck-Einstein
- Compton (1923): photon has momentum — corpuscular light confirmed

**Connections:**
- Feeds into: Topic 20 (Schrödinger derived de Broglie + energy-momentum relation)

---

### Topic 20: Wave Mechanics [CRITICAL — EXPAND]

**Current plan:** ~6 episodes
**Assessment: EXPAND to 8 episodes.** The derivation of Schrödinger's equation needs its own episode. The current plan is adequate for applications but undersells the derivation.

**The Schrödinger equation must be derived, not just stated. The standard pedagogy:**
1. Start with de Broglie: `λ = h/p`, so `p = ℏk`
2. A plane wave: `ψ = Ae^(i(kx-ωt))`
3. Note `∂ψ/∂x = ikψ`, so `p̂ψ = -iℏ∂ψ/∂x = ℏkψ = pψ` — this motivates `p̂ = -iℏ∂/∂x`
4. Energy: `E = p²/2m + V`, so `Ê = ℏω`
5. Note `∂ψ/∂t = -iωψ`, so `iℏ∂ψ/∂t = ℏωψ = Eψ`
6. Combine: `iℏ∂ψ/∂t = -ℏ²/2m · ∂²ψ/∂x² + Vψ`

This derivation must be in a dedicated episode. Label it explicitly as a plausibility argument / heuristic derivation, not a rigorous derivation from first principles.

**Mandatory equations:**
- `iℏ ∂ψ/∂t = -ℏ²/2m ∇²ψ + Vψ` (time-dependent Schrödinger equation)
- `-ℏ²/2m ∇²ψ + Vψ = Eψ` (time-independent Schrödinger equation)
- `|ψ|² = ψ*ψ` (Born rule — probability density)
- `∫|ψ|²dV = 1` (normalization)
- Particle in a box: `ψ_n = √(2/L) sin(nπx/L)`, `E_n = n²π²ℏ²/2mL²`
- Harmonic oscillator: `E_n = (n + ½)ℏω` (derive via ladder operators)
- Hydrogen atom: `E_n = -13.6 eV/n²` (confirm Bohr result from wave mechanics)
- Tunneling: transmission coefficient `T ∼ e^(-2κa)` where `κ = √(2m(V₀-E))/ℏ`

**Mandatory historical figures:**
- Schrödinger (1926): wave mechanics — motivated by de Broglie, influenced by Debye's suggestion
- Born (1926): probability interpretation of |ψ|² — Schrödinger himself hated this
- The Schrödinger-Born controversy: must be addressed, not glossed over

**Connections:**
- Feeds into: Topic 21 (Matrix Mechanics — shown to be equivalent to wave mechanics), Topic 24 (Perturbation theory — approximate solutions to Schrödinger equation)

---

### Topic 21: Matrix Mechanics and Formalism [CRITICAL]

**Current plan:** ~6 episodes
**Assessment:** Adequate. The uncertainty principle derivation from commutators must be shown.

**Mandatory equations:**
- `[x̂, p̂] = iℏ` (canonical commutation relation — derive: `[x, -iℏ∂/∂x]ψ`)
- `[Â, B̂] = ÂB̂ - B̂Â` (commutator definition)
- `ΔA · ΔB ≥ ½|⟨[Â,B̂]⟩|` (general uncertainty principle — derive from Cauchy-Schwarz)
- `Δx · Δp ≥ ℏ/2` (Heisenberg — as a special case)
- Dirac notation: `⟨φ|ψ⟩`, `|ψ⟩ = Σ c_n|n⟩`, `⟨A⟩ = ⟨ψ|Â|ψ⟩`
- Schrödinger vs Heisenberg picture: `d⟨A⟩/dt = i/ℏ ⟨[H,A]⟩ + ⟨∂A/∂t⟩`

**The derivation of the uncertainty principle from the Cauchy-Schwarz inequality must be shown.** It is one of the most important derivations in quantum mechanics and is routinely hand-waved.

**Mandatory historical figures:**
- Heisenberg (1925): matrix mechanics — before Schrödinger, no wave equation
- Born and Jordan (1925): recognized Heisenberg's arrays as matrices
- Dirac (1926): unified notation, q-numbers, connection to Poisson brackets
- von Neumann (1932): mathematical foundations — Hilbert space formulation

**Connections:**
- Feeds into: Topic 25 (Entanglement — commutators and measurement), Topic 35 (Canonical Quantization)

---

### Topic 22: Angular Momentum and Spin [OK]

**Current plan:** ~6 episodes
**Assessment:** Adequate. The derivation of spin from the algebra must be shown — spin is not a classical concept and should not be introduced as one.

**Mandatory equations:**
- `[L_x, L_y] = iℏL_z` (and cyclic) (angular momentum algebra)
- `L² |l,m⟩ = ℏ²l(l+1)|l,m⟩`, `L_z|l,m⟩ = ℏm|l,m⟩`
- Ladder operators: `L± = L_x ± iL_y`
- Pauli matrices: `σ_x, σ_y, σ_z` (write them out explicitly)
- `S = ℏ/2 · σ` (spin-1/2 operators)
- `[S_x, S_y] = iℏS_z` (spin obeys same algebra as L)
- Clebsch-Gordan: `|j₁,m₁⟩⊗|j₂,m₂⟩ = Σ ⟨j₁m₁j₂m₂|jm⟩|j,m⟩`

**Key point for writers:** Half-integer spin (s = 1/2) is allowed by the algebra but forbidden for orbital angular momentum by the requirement of single-valuedness of the wavefunction. Spin is intrinsically quantum. Do not explain it as a spinning ball.

**Mandatory historical figures:**
- Stern and Gerlach (1922): discrete deflection — two spots, not a smear
- Pauli (1924): proposed "non-classical two-valuedness" before spin was named
- Uhlenbeck and Goudsmit (1925): named it spin, proposed spinning electron
- Dirac (1928): spin emerges naturally from relativistic QM (preview of Topic 33)

**Connections:**
- Feeds into: Topic 23 (Pauli exclusion), Topic 22 (Clebsch-Gordan needed for multi-electron atoms), Topic 33 (Dirac equation gives spin from first principles)

---

### Topic 23: Identical Particles and Atoms [OK]

**Current plan:** ~5 episodes
**Assessment:** Adequate.

**Mandatory equations:**
- Symmetrization postulate: `ψ_bosons = symmetric`, `ψ_fermions = antisymmetric`
- `ψ_antisym = (1/√2)(|a⟩|b⟩ - |b⟩|a⟩)` for two fermions
- Slater determinant (write out for 3 electrons, not just name it)
- Pauli exclusion principle as a consequence of antisymmetry
- Hartree-Fock equations (conceptual statement)

**Connections:**
- Feeds into: Topic 17 (Fermi-Dirac statistics), Topic 35 (Fock space in QFT)

---

### Topic 24: Perturbation Theory and Approximations [OK]

**Current plan:** ~5 episodes
**Assessment:** Adequate.

**Mandatory equations:**
- `E_n^(1) = ⟨n^(0)|H'|n^(0)⟩` (first-order energy correction)
- `|n^(1)⟩ = Σ_{m≠n} ⟨m^(0)|H'|n^(0)⟩/(E_n^(0) - E_m^(0)) |m^(0)⟩`
- `E_n^(2) = Σ_{m≠n} |⟨m^(0)|H'|n^(0)⟩|² / (E_n^(0) - E_m^(0))`
- Variational principle: `⟨ψ|H|ψ⟩ ≥ E_ground` for any normalized `|ψ⟩`
- WKB approximation: `ψ ∼ exp(±i/ℏ ∫p(x)dx)`

**Connections:**
- Feeds into: Topic 36 (QED — perturbative expansion in α), Topic 40 (Standard Model — perturbative SM calculations)

---

### Topic 25: Quantum Entanglement and Foundations [OK]

**Current plan:** ~6 episodes
**Assessment:** Adequate. Bell's theorem must be derived, not just described.

**Mandatory equations:**
- Bell state: `|Φ+⟩ = (1/√2)(|↑↑⟩ + |↓↓⟩)` (write all four Bell states)
- CHSH inequality: `|E(a,b) - E(a,b') + E(a',b) + E(a',b')| ≤ 2` (classical), `≤ 2√2` (QM)
- The derivation of the CHSH bound 2 from local hidden variables must be shown step by step
- The QM prediction `2√2 ≈ 2.83` must be derived from the singlet state

**Mandatory historical figures:**
- Einstein, Podolsky, Rosen (1935): EPR paper — locality + completeness argument
- Bell (1964): inequalities from local realism — showed EPR is testable
- Aspect, Grangier, Roger (1982): first definitive Bell test
- Zeilinger (2022): Nobel Prize experiments closing major loopholes

**Connections:**
- Feeds into: quantum computing (not in current curriculum), Topic 27 (quantum gravity foundations discussion)

---

## Module 5: Relativity

---

### Topic 26: Special Relativity (deep) [OK]

**Current plan:** ~6 episodes
**Assessment:** Adequate. Complement Topic 13's historical approach with deeper geometric content here.

**Mandatory equations:**
- `ds² = -c²dτ² = η_μν dx^μ dx^ν` (Minkowski metric, signature -+++)
- `x'^μ = Λ^μ_ν x^ν` (Lorentz transformation in tensor form)
- `p^μ = (E/c, p)` (four-momentum)
- `p^μ p_μ = -m²c²` (mass-shell condition)
- `F^μν = ∂^μ A^ν - ∂^ν A^μ` (electromagnetic field tensor)
- `∂_μ F^μν = μ₀ J^ν` (Maxwell's equations in covariant form)

**Connections:**
- Prerequisite for: Topic 27 (GR generalises Minkowski to curved spacetime)

---

### Topic 27: General Relativity [CRITICAL]

**Current plan:** ~8 episodes
**Assessment:** Adequate, but the Einstein field equations must be derived from the action principle, not just stated.

**Mandatory equations:**
- Equivalence principle (statement + gedanken experiment)
- Geodesic equation: `d²x^μ/dτ² + Γ^μ_νρ (dx^ν/dτ)(dx^ρ/dτ) = 0`
- Riemann tensor: `R^ρ_σμν = ∂_μΓ^ρ_νσ - ∂_νΓ^ρ_μσ + ...`
- Ricci tensor: `R_μν = R^ρ_μρν`
- Ricci scalar: `R = g^μν R_μν`
- Einstein tensor: `G_μν = R_μν - ½g_μν R`
- Einstein field equations: `G_μν + Λg_μν = 8πG/c⁴ T_μν`
- Hilbert action: `S = 1/(16πG) ∫(R - 2Λ)√(-g) d⁴x + S_matter` (derive EFE by varying)
- Schwarzschild metric: `ds² = -(1-r_s/r)c²dt² + (1-r_s/r)^(-1)dr² + r²dΩ²`

**Mandatory historical figures:**
- Einstein (1907–1915): equivalence principle to field equations — 8-year struggle
- Hilbert (1915): derived field equations from action principle (approximately simultaneously with Einstein)
- Schwarzschild (1916): exact solution — 6 weeks after Einstein's equations, while at the Russian front
- Wheeler (1960s): coined "black hole," popularized GR in the US
- LIGO team (2015): first detection of gravitational waves

**Connections:**
- Feeds into: Topic 28 (Cosmology — Friedmann equations from EFE), Topic 41 (quantum gravity problem)

---

### Topic 28: Cosmology [OK]

**Current plan:** ~6 episodes
**Assessment:** Adequate.

**Mandatory equations:**
- Friedmann equations: `(ȧ/a)² = 8πGρ/3 - kc²/a² + Λc²/3`
- `ä/a = -4πG/3(ρ + 3p/c²) + Λc²/3`
- Hubble's law: `v = H₀ d` (derive from Friedmann as small-a limit)
- `H₀ = ȧ/a` (Hubble parameter)
- CMB temperature: `T ∝ 1/a` (derive from adiabatic expansion)
- Density parameters: `Ω_m + Ω_r + Ω_Λ + Ω_k = 1`

**Mandatory historical figures:**
- Friedmann (1922): expanding universe solutions from EFE
- Lemaître (1927): independently derived, proposed the "cosmic egg"
- Hubble (1929): observational evidence for expansion
- Penzias and Wilson (1965): CMB discovery (accidental)
- Riess, Perlmutter, Schmidt (1998): accelerating expansion, dark energy, Nobel 2011

**Connections:**
- This topic closes Module 5. Block D episode should preview the quantum gravity problem (Topic 41).

---

## Module 6: Mathematical Methods

---

### Topic 29: Vector Calculus for Physics [OK]

**Current plan:** ~4 episodes
**Assessment:** Adequate. These episodes serve as tools; depth should be commensurate with their role.

**Mandatory content:**
- Gradient, divergence, curl in Cartesian, spherical, and cylindrical coordinates
- Stokes' theorem: `∮_C F·dl = ∬_S (∇×F)·dA`
- Divergence theorem: `∯_S F·dA = ∭_V (∇·F)dV`
- Show explicitly how Gauss's law in differential form follows from integral form via divergence theorem

---

### Topic 30: Differential Equations in Physics [OK]

**Current plan:** ~4 episodes
**Assessment:** Adequate.

**Mandatory content:**
- Second-order linear ODEs with constant coefficients (SHM, RLC circuits)
- Wave equation, heat equation, Laplace equation as canonical PDEs
- Separation of variables applied to each
- Green's functions: `LG(x,x') = δ(x-x')` — physical meaning as response to a point source

---

### Topic 31: Complex Analysis for Physics [OK]

**Current plan:** ~4 episodes
**Assessment:** Adequate.

**Mandatory content:**
- Cauchy-Riemann equations
- Cauchy's integral theorem and formula
- Residue theorem with applications to real integrals
- Application to scattering amplitudes: poles in the complex plane correspond to resonances

---

### Topic 32: Group Theory for Physics [CRITICAL]

**Current plan:** ~5 episodes
**Assessment:** Adequate but SU(2) must be done carefully — it is prerequisite for understanding spin and gauge theory.

**Mandatory equations:**
- Group axioms (closure, associativity, identity, inverse)
- `[T_a, T_b] = if_{abc} T_c` (Lie algebra structure constants)
- SU(2) algebra: `[J_x, J_y] = iJ_z` — show this IS the angular momentum algebra
- SU(2) fundamental representation: 2×2 matrices
- `SU(2) ≅ SO(3)` locally but globally different (double cover — important for spin-1/2)
- SU(3): 8 generators (Gell-Mann matrices) — this is color in QCD

**Connections:**
- Feeds into: Topic 36 (QED — U(1) gauge invariance), Topic 39 (Non-Abelian gauge theory — SU(2)×SU(3))

---

## Module 7: Quantum Field Theory

---

### Topic 33: Why QFT? [CRITICAL]

**Current plan:** ~5 episodes
**Assessment:** Adequate. The Dirac equation derivation must be its own episode.

**The Dirac equation needs dedicated treatment. The derivation must show:**
1. Klein-Gordon equation `(-∂_μ∂^μ + m²)φ = 0` as the naive relativistic Schrödinger equation
2. Problem: negative probability densities (because it is second-order in time)
3. Dirac's strategy: find a first-order equation whose square gives Klein-Gordon
4. Require: `(iγ^μ∂_μ - m)(iγ^μ∂_μ + m) = -∂_μ∂^μ + m²`
5. This forces the gamma matrices to satisfy `{γ^μ, γ^ν} = 2η^μν` (Clifford algebra)
6. The minimal representation requires 4×4 matrices — this is where spin-1/2 emerges
7. The four components: particle spin-up, particle spin-down, antiparticle spin-up, antiparticle spin-down

**Writers must not say "spin just falls out" without showing WHY the Clifford algebra forces a 4-component spinor.**

**Mandatory equations:**
- Klein-Gordon: `(□ + m²)φ = 0` where `□ = ∂_μ∂^μ = -∂²/∂t² + ∇²`
- Dirac equation: `(iγ^μ∂_μ - m)ψ = 0`
- Clifford algebra: `{γ^μ, γ^ν} = 2η^μν`
- Dirac representation of gamma matrices (write them out)
- Dirac adjoint: `ψ̄ = ψ†γ^0`
- Conserved current: `j^μ = ψ̄γ^μψ` (positive definite — Dirac's fix)

**Mandatory historical figures:**
- Klein and Gordon (1926): relativistic wave equation — independently
- Dirac (1928): first-order relativistic equation — predicted spin and antiparticles
- Anderson (1932): discovered positron — confirmed Dirac's prediction

**Connections:**
- Feeds into: Topic 35 (Canonical Quantization), Topic 36 (QED — quantizing the Dirac field)

---

### Topic 34: Classical Field Theory [OK]

**Current plan:** ~4 episodes
**Assessment:** Adequate.

**Mandatory equations:**
- `L = ∫L(φ, ∂_μφ) d³x` (Lagrangian from Lagrangian density)
- Euler-Lagrange for fields: `∂_μ(∂L/∂(∂_μφ)) - ∂L/∂φ = 0`
- Noether's theorem for fields: conserved current `j^μ = (∂L/∂(∂_μφ))δφ - K^μ` where `∂_μ j^μ = 0`
- Energy-momentum tensor: `T^μν = (∂L/∂(∂_μφ))∂^νφ - η^μν L`
- Show that `∂_μ T^μν = 0` gives energy and momentum conservation for fields

---

### Topic 35: Canonical Quantization [CRITICAL]

**Current plan:** ~6 episodes
**Assessment:** Adequate. The Fock space construction and the vacuum energy episode are essential.

**Mandatory equations:**
- `[φ(x), π(y)] = iℏδ³(x-y)` (equal-time commutation relation for fields)
- `φ(x) = ∫d³k/(2π)³ 1/√(2ω_k) [a_k e^(ikx) + a†_k e^(-ikx)]`
- `[a_k, a†_k'] = δ³(k-k')` (creation/annihilation algebra)
- `H = ∫d³k ω_k a†_k a_k + ½δ³(0)` (Hamiltonian — the divergent zero-point energy)
- Normal ordering: `:H: = ∫d³k ω_k a†_k a_k`
- `|0⟩` (vacuum state), `a†_k|0⟩` (one-particle state)
- `N = ∫d³k a†_k a_k` (number operator)

**The vacuum energy divergence must be discussed honestly** — not as a defect to be swept away, but as the first sign that QFT has a UV problem. This sets up the renormalization discussion.

**Mandatory historical figures:**
- Dirac (1927): quantization of the electromagnetic field — first QFT
- Jordan and Klein (1927): quantization of matter fields
- Fock (1932): Fock space formalism

---

### Topic 36: Quantum Electrodynamics (QED) [CRITICAL — EXPAND]

**Current plan:** ~7 episodes
**Assessment:** Adequate if the renormalization episode is done properly. See Topic 38 for renormalization depth requirements.

**Mandatory equations:**
- QED Lagrangian: `L_QED = ψ̄(iγ^μD_μ - m)ψ - ¼F_μν F^μν`
- Covariant derivative: `D_μ = ∂_μ + ieA_μ`
- Gauge invariance: `ψ → e^(ieα)ψ`, `A_μ → A_μ - ∂_μα`
- Feynman rules: electron propagator `i(γ^μp_μ + m)/(p² - m² + iε)`, photon propagator `-ig_μν/(k² + iε)`, vertex `-ieγ^μ`
- Tree-level Compton scattering: `|M|²` (set up, indicate the algebra)
- One-loop electron self-energy (introduce, discuss divergence structure)
- Anomalous magnetic moment: `g-2 = α/π + ...` (state result, explain what α/π means)

**Feynman diagrams must be introduced as a visual notation for terms in the perturbative expansion of the S-matrix, not as literal pictures of particle paths.** The connection to the path integral must be stated.

**Mandatory historical figures:**
- Schwinger (1947): calculated g-2 analytically
- Feynman (1948): path integral approach and diagrams
- Tomonaga (1946): covariant perturbation theory (independently)
- Dyson (1949): proved the three approaches are equivalent; systematized renormalization

---

### Topic 37: Path Integrals [CRITICAL]

**Current plan:** ~5 episodes
**Assessment:** Adequate.

**The path integral must be motivated from the double-slit experiment, not just defined abstractly.**

**Mandatory equations:**
- `⟨x_f,t_f|x_i,t_i⟩ = ∫Dx(t) e^(iS[x]/ℏ)` (path integral definition)
- `S[x] = ∫L(x,ẋ) dt` (classical action)
- Stationary phase approximation: when `ℏ → 0`, integral dominated by classical path (recover classical mechanics)
- Generating functional: `Z[J] = ∫Dφ e^(i(S[φ] + ∫Jφ d⁴x))`
- Propagator: `G(x,y) = -i δ²ln Z/δJ(x)δJ(y)|_{J=0}`
- Connection to statistical mechanics: `Z_stat = ∫Dφ e^(-S_E[φ]/ℏ)` where `S_E` is the Euclidean action (Wick rotation `t → -iτ`)

**Mandatory historical figures:**
- Dirac (1933): noted the connection between quantum amplitudes and `exp(iS/ℏ)`
- Feynman (1948): developed the full formalism in his thesis

**Connections:**
- Feeds into: Topic 38 (Renormalization Group — Wilson's approach uses Euclidean path integral)

---

### Topic 38: Renormalization Group [CRITICAL — EXPAND]

**Current plan:** ~6 episodes
**Assessment: EXPAND to 8 episodes.** This topic is routinely under-taught as "infinities cancel." Wilson's picture is the correct modern understanding and must be given full treatment.

**Wilson's picture (mandatory framework for writers):**

Renormalization is NOT primarily about removing infinities. It is about the fact that physics at long distances (low energy) does not depend on the details of physics at short distances (high energy) — only on a small number of parameters. The renormalization group describes how these parameters change as you change the scale at which you describe the system.

The steps:
1. Start with a field theory valid up to some UV cutoff Λ (e.g., the Planck scale)
2. Integrate out (average over) fluctuations at the highest scales Λ' < k < Λ
3. The result is a new effective theory valid up to Λ' with renormalized couplings
4. The RG equation describes how couplings flow as Λ' is varied
5. Fixed points of the RG flow are scale-invariant theories (conformal field theories)
6. Renormalizability means: only a finite number of couplings are relevant at long distances

**Mandatory equations:**
- Callan-Symanzik equation: `[μ ∂/∂μ + β(g)∂/∂g + nγ]G^(n) = 0`
- Beta function definition: `β(g) = μ dg/dμ`
- One-loop beta function for QED: `β(e) = e³/12π²` (coupling grows at high energy)
- One-loop beta function for QCD: `β(g) = -g³/16π² (11 - 2N_f/3)` (negative for N_f < 17 — asymptotic freedom)
- Wilson's effective action: `e^(-S_eff[φ_<]) = ∫Dφ_> e^(-S[φ_< + φ_>])`
- RG fixed point: `β(g*) = 0`

**Mandatory historical figures:**
- Bethe (1947): Lamb shift calculation — first successful renormalization
- Schwinger, Feynman, Tomonaga (1947–1949): systematic renormalization of QED
- Gell-Mann and Low (1954): running coupling concept
- Kadanoff (1966): block spin — conceptual foundation for Wilson's work
- Wilson (1971–1972): effective field theory, exact RG, condensed matter applications, Nobel 1982
- Gross, Wilczek, Politzer (1973): asymptotic freedom in QCD from negative beta function, Nobel 2004

**Connections:**
- This topic connects: Topic 18 (Phase Transitions — universality), Topic 39 (Non-Abelian gauge theory — asymptotic freedom is a beta function result), Topic 40 (Standard Model — running couplings and gauge coupling unification)

---

### Topic 39: Non-Abelian Gauge Theory [CRITICAL]

**Current plan:** ~6 episodes
**Assessment:** Adequate.

**The progression from QED (U(1)) to Yang-Mills (SU(N)) must be made explicit.** Writers must show WHY local SU(2) invariance requires gauge bosons that interact with each other (unlike photons in QED).

**Mandatory equations:**
- U(1) gauge invariance review: `ψ → e^(iα(x))ψ` requires `A_μ → A_μ - ∂_μα`
- SU(2) local invariance: `ψ → e^(igα^a(x)T_a)ψ` requires non-Abelian gauge field
- Yang-Mills field strength: `F^a_μν = ∂_μA^a_ν - ∂_νA^a_μ - gf^{abc}A^b_μA^c_ν`
- Note: the non-Abelian term `f^{abc}A^b_μA^c_ν` has no QED analog — this gives self-interactions
- Yang-Mills Lagrangian: `L_YM = -¼F^a_μν F^{aμν}`
- QCD Lagrangian: `L_QCD = Σ_f ψ̄_f(iγ^μD_μ - m_f)ψ_f - ¼G^a_μν G^{aμν}`
- Asymptotic freedom: `α_s(Q²) = 2π/((11 - 2N_f/3)ln(Q/Λ_QCD))`

**Mandatory historical figures:**
- Yang and Mills (1954): non-Abelian gauge theory — proposed for isospin
- Gell-Mann (1964): quarks and SU(3) flavor symmetry
- Fritzsch, Gell-Mann, Leutwyler (1973): QCD with color SU(3)
- Gross and Wilczek (1973), Politzer (1973): asymptotic freedom

---

### Topic 40: The Standard Model [CRITICAL]

**Current plan:** ~7 episodes
**Assessment:** Adequate. The Higgs mechanism derivation must be shown, not just described.

**The Mexican hat potential and spontaneous symmetry breaking must be derived:**
1. Start with `V(φ) = -μ²|φ|² + λ|φ|⁴` — the "wrong sign" mass term
2. Minimum at `|φ|² = μ²/2λ = v²/2` (the vacuum expectation value)
3. Expand around the minimum: `φ = (v + h)/√2`
4. The h field has mass `m_h = √(2μ²) = √(2λ)v` — the Higgs boson
5. Gauge bosons that couple to φ gain mass through `|D_μφ|²` — W and Z masses
6. Goldstone bosons (the "eaten" degrees of freedom) become the longitudinal polarizations of W and Z

**Mandatory equations:**
- Full SM gauge group: `SU(3)_c × SU(2)_L × U(1)_Y`
- SM Lagrangian: `L_SM = L_gauge + L_fermion + L_Higgs + L_Yukawa` (describe each term, show the full Lagrangian at least once)
- Higgs potential: `V(φ) = -μ²φ†φ + λ(φ†φ)²`
- W and Z masses: `m_W = gv/2`, `m_Z = √(g²+g'²)v/2`
- Weinberg angle: `sin²θ_W = g'²/(g²+g'²) ≈ 0.231`
- CKM matrix: `U_CKM` (name, explain, write schematically)

**Mandatory historical figures:**
- Glashow (1961): electroweak group structure SU(2)×U(1) without Higgs
- Weinberg (1967) and Salam (1968): electroweak unification with Higgs mechanism
- Higgs, Brout, Englert, Kibble, Guralnik, Hagen (1964): SSB mechanism — note the credit distribution
- 't Hooft and Veltman (1971): proved electroweak theory is renormalizable, Nobel 1999
- Rubbia and van der Meer (1983): W and Z boson discovery at CERN

---

### Topic 41: Beyond the Standard Model (preview) [OK]

**Current plan:** ~4 episodes
**Assessment:** Adequate as a preview. This is the final topic — it should close the series with open questions, not false resolutions.

**Mandatory content:**
- Neutrino oscillations: `P(ν_α → ν_β) = sin²(2θ)sin²(Δm²L/4E)` — evidence for nonzero mass
- The hierarchy problem: the Higgs mass is quadratically sensitive to UV physics — why is it 125 GeV, not Planck scale?
- Supersymmetry as a proposed solution: every boson has a fermionic partner (and vice versa) — this cancels the quadratic divergences
- Grand unification: running couplings of SU(3), SU(2), U(1) nearly meet at `Q ∼ 10¹⁵` GeV (in SUSY)
- The quantum gravity problem: GR and QFT are incompatible at the Planck scale `E_Pl = √(ℏc⁵/G) ≈ 10¹⁹` GeV

**Mandatory historical figures:**
- Pontecorvo (1957): neutrino oscillations — proposed before experimental confirmation
- Wess and Zumino (1974): first SUSY field theory in 4D
- Georgi and Glashow (1974): SU(5) grand unification — predicted proton decay (not observed)

**The final episode of this topic (and the series) should be a reflection on Noether's theorem as the unifying thread:** every fundamental equation in the series is a statement about symmetry. The series began with Newton asking "why do things move?" and ends with the answer: because of the symmetries of spacetime and the gauge symmetries of the Standard Model.

---

## Summary: Episodes by Expansion Status

| Topic | Current Plan | Recommended | Status |
|---|---|---|---|
| 01 Newton's Laws | 12 | 12 | OK |
| 02 Conservation Laws | 6 | 6 | OK |
| 03 Gravity and Orbits | 7 | 7 | OK |
| 04 Oscillations and Waves | 6 | 6 | OK |
| 05 Lagrangian Mechanics | 7 | 7 | CRITICAL |
| 06 Hamiltonian Mechanics | 5 | 5 | CRITICAL |
| 07 Rigid Body Dynamics | 5 | 5 | OK |
| 08 Central Force Problems | 4 | 4 | OK |
| 09 Electrostatics | 6 | 6 | OK |
| 10 Magnetostatics | 5 | 5 | OK |
| 11 Electrodynamics / Maxwell | 8 | **12** | EXPAND |
| 12 EM Waves and Optics | 5 | 5 | OK |
| 13 Special Relativity (from EM) | 7 | 7 | OK |
| 14 Classical Thermodynamics | 7 | 7 | OK |
| 15 Kinetic Theory | 5 | 5 | OK |
| 16 Statistical Mechanics Classical | 7 | 7 | CRITICAL |
| 17 Statistical Mechanics Quantum | 6 | 6 | CRITICAL |
| 18 Phase Transitions | 5 | 5 | OK |
| 19 Origins of Quantum Theory | 7 | 7 | OK |
| 20 Wave Mechanics | 6 | **8** | EXPAND |
| 21 Matrix Mechanics / Formalism | 6 | 6 | CRITICAL |
| 22 Angular Momentum and Spin | 6 | 6 | OK |
| 23 Identical Particles | 5 | 5 | OK |
| 24 Perturbation Theory | 5 | 5 | OK |
| 25 Entanglement / Foundations | 6 | 6 | OK |
| 26 Special Relativity (deep) | 6 | 6 | OK |
| 27 General Relativity | 8 | 8 | CRITICAL |
| 28 Cosmology | 6 | 6 | OK |
| 29 Vector Calculus | 4 | 4 | OK |
| 30 Differential Equations | 4 | 4 | OK |
| 31 Complex Analysis | 4 | 4 | OK |
| 32 Group Theory | 5 | 5 | CRITICAL |
| 33 Why QFT? | 5 | 5 | CRITICAL |
| 34 Classical Field Theory | 4 | 4 | OK |
| 35 Canonical Quantization | 6 | 6 | CRITICAL |
| 36 QED | 7 | 7 | CRITICAL |
| 37 Path Integrals | 5 | 5 | CRITICAL |
| 38 Renormalization Group | 6 | **8** | EXPAND |
| 39 Non-Abelian Gauge Theory | 6 | 6 | CRITICAL |
| 40 The Standard Model | 7 | 7 | CRITICAL |
| 41 Beyond the SM | 4 | 4 | OK |
| **TOTAL** | **~236** | **~243** | |

---

## Critical Equations That Must Appear Somewhere in the Series

The following equations are the irreducible core of a postgraduate physics education. Every one of them must appear, be derived (or have its derivation motivated), and be given physical meaning in at least one episode.

1. `F = dp/dt` (Newton)
2. `d/dt(∂L/∂q̇) - ∂L/∂q = 0` (Euler-Lagrange)
3. `{q,p}_Poisson → [q̂,p̂] = iℏ` (canonical quantization)
4. `∇·E = ρ/ε₀`, `∇·B = 0`, `∇×E = -∂B/∂t`, `∇×B = μ₀J + μ₀ε₀∂E/∂t` (Maxwell)
5. `c = 1/√(μ₀ε₀)` (speed of light from Maxwell)
6. `ds² = η_μν dx^μ dx^ν` (Minkowski spacetime)
7. `G_μν = 8πG/c⁴ T_μν` (Einstein field equations)
8. `S = k ln W` (Boltzmann entropy)
9. `Z = Σ e^(-βE_i)` (partition function)
10. `iℏ ∂ψ/∂t = Ĥψ` (Schrödinger)
11. `[x̂, p̂] = iℏ` (Heisenberg)
12. `Δx·Δp ≥ ℏ/2` (uncertainty principle, derived from commutator)
13. `(iγ^μ∂_μ - m)ψ = 0` (Dirac)
14. `⟨x_f|x_i⟩ = ∫Dx e^(iS/ℏ)` (Feynman path integral)
15. `β(g) = μ dg/dμ` (renormalization group)
16. `L_SM = L_gauge + L_fermion + L_Higgs + L_Yukawa` (Standard Model)
17. For each conservation law: the Noether current `j^μ = ∂L/∂(∂_μφ) δφ`
