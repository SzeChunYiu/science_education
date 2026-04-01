"""Visual metaphor suggestions for abstract physics concepts."""

# Concept keyword → visual metaphor description
METAPHOR_TABLE = {
    "gravity": "invisible threads pulling objects downward, apple falling in slow motion",
    "force": "glowing arrows pushing and pulling on objects",
    "acceleration": "speedometer needle climbing, motion blur trails",
    "velocity": "arrow showing direction and speed alongside moving object",
    "momentum": "bowling ball colliding with pins, transfer of motion",
    "energy": "glowing orb transferring between objects",
    "kinetic energy": "vibrating molecules, bouncing ball with speed lines",
    "potential energy": "ball perched on cliff edge, compressed spring glowing",
    "conservation": "balanced scale with energy symbols on both sides",
    "friction": "rough surface with tiny bumps magnified, heat waves",
    "inertia": "object resisting change, passenger lurching in stopping car",
    "newton": "apple falling near contemplative figure under tree",
    "electrostatics": "hair standing on end, sparks between charged objects",
    "electric field": "invisible lines of force radiating from charges",
    "coulomb": "two charged spheres attracting and repelling with force arrows",
    "magnetism": "iron filings tracing field lines around magnet",
    "electromagnetic": "intertwined electric and magnetic wave patterns",
    "wave": "ripples spreading across water surface from dropped stone",
    "frequency": "tuning fork vibrating with visible sound waves",
    "wavelength": "ruler measuring crest-to-crest distance on wave",
    "light": "prism splitting white beam into rainbow spectrum",
    "reflection": "mirror showing light ray bouncing at equal angle",
    "refraction": "straw appearing bent in glass of water",
    "thermodynamics": "engine diagram with heat flowing from hot to cold",
    "entropy": "neat arrangement of blocks gradually becoming disordered",
    "temperature": "thermometer with molecules vibrating faster as mercury rises",
    "pressure": "particles bouncing off container walls with force arrows",
    "atom": "tiny solar system with electron orbits around nucleus",
    "quantum": "particle existing in multiple positions simultaneously, ghostly overlaps",
    "relativity": "clock running slower on fast-moving rocket",
    "spacetime": "fabric sheet warped by heavy ball sitting on it",
}


def suggest_metaphor(narration: str) -> str:
    """Suggest a visual metaphor based on narration content.

    Searches narration for concept keywords and returns the best
    matching visual metaphor description. Returns empty string
    if no strong match found.
    """
    narration_lower = narration.lower()

    best_match = ""
    best_score = 0

    for concept, metaphor in METAPHOR_TABLE.items():
        # Score by keyword presence and specificity
        words = concept.split()
        matches = sum(1 for w in words if w in narration_lower)
        score = matches / len(words) if words else 0

        # Bonus for exact phrase match
        if concept in narration_lower:
            score += 1.0

        if score > best_score:
            best_score = score
            best_match = metaphor

    return best_match if best_score >= 0.5 else ""
