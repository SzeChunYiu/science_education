"""
test_layout.py — integration test for the physics education layout engine.

Tests:
  1. Basic scene: character_left + equation_center + caption + subtitle
     on a warm beige background (#f5e6d3), with a placeholder PNG for
     the character (a colored rectangle, no real asset needed).
  2. Overlap resolution: two elements placed in a way that their zones
     overlap; verifies they get pushed apart.
  3. Subtitle zone enforcement: confirms non-subtitle content is rejected.
  4. Contrast utilities: WCAG checks on known color pairs.
  5. Schema validation: valid and invalid scene dicts.

Output: /tmp/test_layout_output.png  (basic scene)
        /tmp/test_layout_overlap.png  (overlap test)
"""

import os
import sys
import tempfile

# Ensure the src directory is on the path when running as a script
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Import layout engine
# ---------------------------------------------------------------------------
from layout import (
    LayoutEngine,
    Compositor,
    LayoutElement,
    LayoutConstraintError,
    ValidationReport,
    validate_scene,
    validate_scene_safe,
    SceneValidationError,
    contrast_ratio,
    auto_fix_text_contrast,
    describe_contrast,
    ZONES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_placeholder_png(
    path: str,
    width: int = 400,
    height: int = 600,
    color: tuple = (255, 180, 120),
    label: str = "CHARACTER",
) -> str:
    """
    Create a simple colored rectangle PNG as a character placeholder.
    Saves to *path* and returns the path.
    """
    img = Image.new("RGBA", (width, height), color + (255,))
    draw = ImageDraw.Draw(img)
    # Draw a simple face outline to make it recognisable
    draw.ellipse([50, 50, 350, 450], outline=(80, 40, 10), width=6)
    draw.ellipse([120, 160, 180, 220], fill=(80, 40, 10))   # left eye
    draw.ellipse([220, 160, 280, 220], fill=(80, 40, 10))   # right eye
    draw.arc([120, 260, 280, 360], start=10, end=170, fill=(80, 40, 10), width=6)
    # Label
    draw.text((10, height - 30), label, fill=(60, 30, 10))
    img.save(path, format="PNG")
    return path


def hr(title: str = "") -> None:
    width = 70
    if title:
        pad = (width - len(title) - 2) // 2
        print("=" * pad + f" {title} " + "=" * (width - pad - len(title) - 2))
    else:
        print("=" * width)


def section(title: str) -> None:
    print()
    hr(title)


def ok(msg: str) -> None:
    print(f"  [PASS] {msg}")


def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def check(condition: bool, pass_msg: str, fail_msg: str) -> bool:
    if condition:
        ok(pass_msg)
    else:
        fail(fail_msg)
    return condition


# ---------------------------------------------------------------------------
# Test 1: Basic scene rendering
# ---------------------------------------------------------------------------

def test_basic_scene() -> bool:
    section("TEST 1: Basic scene rendering (16:9)")

    tmp_dir = "/tmp"
    char_path = os.path.join(tmp_dir, "test_character.png")
    output_path = "/tmp/test_layout_output.png"

    make_placeholder_png(char_path, width=400, height=600, color=(255, 180, 120))
    print(f"  Placeholder character written to: {char_path}")

    engine = LayoutEngine(aspect="16:9")
    compositor = Compositor(engine)

    scene = {
        "background": "#f5e6d3",
        "elements": [
            {
                "role": "character_left",
                "asset": char_path,
                "scale": 0.85,
            },
            {
                "role": "equation_center",
                "text": "p = mv",
                "font_size": 72,
                "color": "#1a1a1a",
            },
            {
                "role": "caption",
                "text": "momentum  =  mass  \u00d7  velocity",
                "font_size": 36,
                "color": "#2c2c2c",
            },
            {
                "role": "subtitle",
                "text": "The quantity Newton started with",
                "font_size": 32,
                "color": "#ffffff",
            },
        ],
    }

    # Validate schema first
    valid, err = validate_scene_safe(scene)
    check(valid, "Scene passes schema validation", f"Schema error: {err}")

    # Render
    try:
        final_image = compositor.render_frame(scene, output_path)
        rendered_ok = os.path.isfile(output_path)
        check(rendered_ok, f"Frame rendered to {output_path}", "Render failed — file not created")
    except Exception as exc:
        fail(f"render_frame raised: {exc}")
        import traceback; traceback.print_exc()
        return False

    # Run the engine independently to inspect resolved positions
    elements = [
        LayoutElement(role="character_left", asset_path=char_path, scale=0.85),
        LayoutElement(role="equation_center", text="p = mv", font_size=72, color=(26, 26, 26)),
        LayoutElement(role="caption", text="momentum = mass × velocity", font_size=36, color=(44, 44, 44)),
        LayoutElement(role="subtitle", text="The quantity Newton started with", font_size=32, color=(255, 255, 255)),
    ]
    resolved = engine.place(elements)

    print()
    print("  Resolved element positions:")
    print(f"  {'Role':<20} {'BBox':>30}  {'Z':>4}  {'W':>6}  {'H':>6}")
    print("  " + "-" * 72)
    for el in resolved:
        print(f"  {el.role:<20} {str(el.bbox):>30}  {el.z:>4}  {el.w:>6}  {el.h:>6}")

    # Contrast check report
    print()
    print("  Contrast checks:")
    bg_color = (245, 230, 211)  # #f5e6d3

    text_elements = [
        ("equation_center", (26, 26, 26), 72),
        ("caption",         (44, 44, 44), 36),
        ("subtitle",        (255, 255, 255), 32),
    ]
    all_contrast_ok = True
    for role, color, fs in text_elements:
        desc = describe_contrast(color, bg_color, font_size=fs)
        passed = "PASS" in desc
        all_contrast_ok = all_contrast_ok and passed
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {role:<20} text={color} on bg={bg_color}: {desc}")

    # Run full validation
    report = engine.validate(resolved)
    print()
    print("  Validation report:")
    for c in report.checks:
        status = "[PASS]" if c.passed else "[FAIL]"
        detail = f" ({c.detail})" if c.detail else ""
        print(f"    {status} {c.name}{detail}")

    all_passed = report.passed
    check(all_passed, "Full validation passed", "One or more validation checks FAILED")
    return all_passed


# ---------------------------------------------------------------------------
# Test 2: Overlap resolution
# ---------------------------------------------------------------------------

def test_overlap_resolution() -> bool:
    section("TEST 2: Overlap resolution")

    engine = LayoutEngine(aspect="16:9")
    output_path = "/tmp/test_layout_overlap.png"

    # equation_center and body_text share overlapping zones — a good natural test.
    # We also set scale=1.0 on both to maximise their footprint.
    elements = [
        LayoutElement(
            role="equation_center",
            text="F = ma",
            font_size=80,
            color=(30, 30, 30),
            scale=1.0,
        ),
        LayoutElement(
            role="body_text",
            text="Force equals mass times acceleration",
            font_size=40,
            color=(30, 30, 30),
            scale=1.0,
        ),
    ]

    # Check bboxes before and after placement
    print("  Running engine.place() on equation_center + body_text (both scale=1.0) ...")

    resolved = engine.place(elements)
    report = engine.validate(resolved)

    print()
    print("  Resolved positions after overlap resolution:")
    print(f"  {'Role':<20} {'BBox':>40}")
    print("  " + "-" * 65)
    for el in resolved:
        print(f"  {el.role:<20} {str(el.bbox):>40}")

    overlapping_pairs = engine._find_overlapping_pairs(resolved)
    no_overlap = len(overlapping_pairs) == 0
    check(
        no_overlap,
        "No overlapping elements after resolution",
        f"Still overlapping: {[(resolved[i].role, resolved[j].role) for i, j in overlapping_pairs]}",
    )

    # Also render to PNG for visual inspection
    compositor = Compositor(engine)
    scene = {
        "background": "#e8f4f8",
        "elements": [
            {"role": "equation_center", "text": "F = ma",
             "font_size": 80, "color": "#1a1a1a", "scale": 1.0},
            {"role": "body_text",
             "text": "Force equals mass times acceleration",
             "font_size": 40, "color": "#1a1a1a", "scale": 1.0},
        ],
    }
    try:
        compositor.render_frame(scene, output_path)
        ok(f"Overlap test rendered to {output_path}")
    except Exception as exc:
        fail(f"render_frame raised: {exc}")

    print()
    print("  Validation report:")
    for c in report.checks:
        status = "[PASS]" if c.passed else "[FAIL]"
        detail = f" ({c.detail})" if c.detail else ""
        print(f"    {status} {c.name}{detail}")

    return no_overlap


# ---------------------------------------------------------------------------
# Test 3: Subtitle zone enforcement
# ---------------------------------------------------------------------------

def test_subtitle_zone_enforcement() -> bool:
    section("TEST 3: Subtitle zone hard constraint")

    engine = LayoutEngine(aspect="16:9")

    # Try placing a caption that is forced into the subtitle zone.
    # We'll manually push it past the subtitle boundary and then call
    # _check_safe_zones to confirm it's caught.
    el = LayoutElement(
        role="caption",
        text="This caption is in the wrong place",
        font_size=36,
        color=(0, 0, 0),
    )
    # Place normally first
    zone_px = engine._zone_to_pixels("caption")
    engine._fit_element_to_zone(el, zone_px)
    el.update_bbox()

    # Artificially push it into the subtitle zone
    subtitle_y = engine._subtitle_y
    el.y = subtitle_y + 10
    el.update_bbox()

    violations = engine._check_safe_zones([el])
    caught = len(violations) > 0
    check(caught, f"Violation correctly detected: {violations[0]}", "Subtitle zone violation was NOT caught")

    # Now verify that a legitimate subtitle element is not flagged
    sub = LayoutElement(
        role="subtitle",
        text="Legitimate subtitle",
        font_size=32,
        color=(255, 255, 255),
    )
    sub_zone = engine._zone_to_pixels("subtitle")
    engine._fit_element_to_zone(sub, sub_zone)
    sub.update_bbox()

    sub_violations = engine._check_safe_zones([sub])
    check(
        len(sub_violations) == 0,
        "Subtitle element correctly not flagged as a violation",
        f"Subtitle element was incorrectly flagged: {sub_violations}",
    )

    return caught


# ---------------------------------------------------------------------------
# Test 4: Contrast utilities
# ---------------------------------------------------------------------------

def test_contrast_utilities() -> bool:
    section("TEST 4: WCAG contrast utilities")

    all_passed = True

    # Black on white: should be 21:1
    ratio = contrast_ratio((0, 0, 0), (255, 255, 255))
    close_to_21 = abs(ratio - 21.0) < 0.01
    all_passed &= check(close_to_21, f"Black/white ratio = {ratio:.2f}:1 (expect ~21)", f"Got {ratio:.2f}:1")

    # White on white: should be 1:1
    ratio_same = contrast_ratio((255, 255, 255), (255, 255, 255))
    is_one = abs(ratio_same - 1.0) < 0.01
    all_passed &= check(is_one, f"White/white ratio = {ratio_same:.2f}:1 (expect 1.0)", f"Got {ratio_same:.2f}:1")

    # Symmetry: ratio(A,B) == ratio(B,A)
    r_ab = contrast_ratio((200, 100, 50), (30, 30, 130))
    r_ba = contrast_ratio((30, 30, 130), (200, 100, 50))
    symmetric = abs(r_ab - r_ba) < 0.001
    all_passed &= check(symmetric, f"Contrast ratio is symmetric ({r_ab:.3f} == {r_ba:.3f})", "Not symmetric")

    # auto_fix_text_contrast: light grey text on white background — should trigger a fix
    fix = auto_fix_text_contrast((200, 200, 200), (255, 255, 255), min_ratio=4.5)
    has_fix = fix is not None
    all_passed &= check(has_fix, f"Auto-fix triggered for low-contrast grey on white: method={fix['method'] if fix else None}", "No fix triggered — unexpected")

    # High contrast text should return None (no fix needed)
    fix_none = auto_fix_text_contrast((26, 26, 26), (245, 230, 211), min_ratio=4.5)
    all_passed &= check(fix_none is None, "No fix needed for near-black on warm beige", f"Unexpected fix: {fix_none}")

    print()
    print("  Sample contrast descriptions:")
    pairs = [
        ((0, 0, 0),       (255, 255, 255), 36, "Black on white"),
        ((26, 26, 26),    (245, 230, 211), 36, "Near-black on beige"),
        ((255, 255, 255), (30, 30, 200),   32, "White on deep blue"),
        ((150, 150, 150), (200, 200, 200), 16, "Mid-grey on light-grey"),
    ]
    for fg, bg, fs, label in pairs:
        desc = describe_contrast(fg, bg, font_size=fs)
        print(f"    {label:<30} {desc}")

    return all_passed


# ---------------------------------------------------------------------------
# Test 5: Schema validation
# ---------------------------------------------------------------------------

def test_schema_validation() -> bool:
    section("TEST 5: Scene schema validation")

    all_passed = True

    # Valid minimal scene
    valid_scene = {
        "background": "#f5e6d3",
        "elements": [
            {"role": "headline", "text": "Hello Physics", "font_size": 60},
        ],
    }
    is_valid, err = validate_scene_safe(valid_scene)
    all_passed &= check(is_valid, "Valid minimal scene accepted", f"Rejected: {err}")

    # Valid full scene
    valid_full = {
        "background": "#ffffff",
        "aspect": "9:16",
        "metadata": {"episode": 1, "title": "Momentum"},
        "elements": [
            {"role": "character_center", "asset": "/tmp/some.png", "scale": 0.9},
            {"role": "equation_center",  "text": "E = mc²", "font_size": 72, "color": "#000000"},
            {"role": "subtitle",         "text": "Energy", "font_size": 32},
        ],
    }
    is_valid2, err2 = validate_scene_safe(valid_full)
    all_passed &= check(is_valid2, "Valid full scene accepted", f"Rejected: {err2}")

    # Invalid: unknown role
    bad_role = {
        "elements": [{"role": "floating_label", "text": "bad"}]
    }
    is_bad_role, _ = validate_scene_safe(bad_role)
    all_passed &= check(not is_bad_role, "Unknown role correctly rejected", "Unknown role was accepted — schema too permissive")

    # Invalid: element with neither asset nor text
    bad_empty = {
        "elements": [{"role": "headline"}]  # no text, no asset
    }
    is_bad_empty, err_empty = validate_scene_safe(bad_empty)
    all_passed &= check(not is_bad_empty, "Element with no content correctly rejected", f"Empty element accepted: {err_empty}")

    # Invalid: scale > 1.0
    bad_scale = {
        "elements": [{"role": "headline", "text": "hi", "scale": 1.5}]
    }
    is_bad_scale, _ = validate_scene_safe(bad_scale)
    all_passed &= check(not is_bad_scale, "scale > 1.0 correctly rejected", "scale > 1.0 was accepted")

    # Invalid: bad color
    bad_color = {
        "elements": [{"role": "caption", "text": "hi", "color": "red"}]  # not a valid hex
    }
    is_bad_color, _ = validate_scene_safe(bad_color)
    all_passed &= check(not is_bad_color, "Invalid color string correctly rejected", "Invalid color accepted")

    return all_passed


# ---------------------------------------------------------------------------
# Test 6: 9:16 (Shorts) aspect ratio
# ---------------------------------------------------------------------------

def test_shorts_aspect() -> bool:
    section("TEST 6: YouTube Shorts (9:16) layout")

    tmp_dir = "/tmp"
    char_path = os.path.join(tmp_dir, "test_character_shorts.png")
    output_path = "/tmp/test_layout_shorts.png"

    make_placeholder_png(char_path, width=300, height=500, color=(120, 200, 255))

    engine = LayoutEngine(aspect="9:16")
    compositor = Compositor(engine)

    print(f"  Canvas size: {engine.canvas_w}×{engine.canvas_h}")
    print(f"  Subtitle boundary: y={engine._subtitle_y}px")
    print(f"  Content area: ({engine._safe_x1},{engine._safe_y1}) → ({engine._safe_x2},{engine._safe_y2})")

    scene = {
        "background": "#1a1a2e",
        "elements": [
            {"role": "character_center", "asset": char_path, "scale": 0.75},
            {"role": "headline",    "text": "Newton's Laws",  "font_size": 56, "color": "#ffffff"},
            {"role": "equation_center", "text": "F = ma",     "font_size": 80, "color": "#ffd700"},
            {"role": "subtitle",    "text": "Law 2: Net force = mass × acceleration", "font_size": 28, "color": "#cccccc"},
        ],
    }

    valid, err = validate_scene_safe(scene)
    check(valid, "Shorts scene passes schema validation", f"Schema error: {err}")

    try:
        compositor.render_frame(scene, output_path)
        ok(f"Shorts frame rendered to {output_path}")
    except Exception as exc:
        fail(f"render_frame raised: {exc}")
        import traceback; traceback.print_exc()
        return False

    # Validate resolved positions
    elements_list = [
        LayoutElement(role="character_center", asset_path=char_path, scale=0.75),
        LayoutElement(role="headline", text="Newton's Laws", font_size=56, color=(255, 255, 255)),
        LayoutElement(role="equation_center", text="F = ma", font_size=80, color=(255, 215, 0)),
        LayoutElement(role="subtitle", text="Law 2", font_size=28, color=(204, 204, 204)),
    ]
    resolved = engine.place(elements_list)
    report = engine.validate(resolved)

    print()
    print("  Resolved element positions (9:16):")
    print(f"  {'Role':<20} {'BBox':>36}  Z")
    print("  " + "-" * 62)
    for el in resolved:
        print(f"  {el.role:<20} {str(el.bbox):>36}  {el.z}")

    print()
    for c in report.checks:
        status = "[PASS]" if c.passed else "[FAIL]"
        detail = f" ({c.detail})" if c.detail else ""
        print(f"    {status} {c.name}{detail}")

    return report.passed


# ---------------------------------------------------------------------------
# Test 7: Determinism
# ---------------------------------------------------------------------------

def test_determinism() -> bool:
    section("TEST 7: Determinism (same input → same output)")

    engine = LayoutEngine(aspect="16:9")
    char_path = "/tmp/test_character.png"

    def make_elements():
        return [
            LayoutElement(role="character_left", asset_path=char_path, scale=0.8),
            LayoutElement(role="equation_center", text="E = mc²", font_size=64, color=(10, 10, 10)),
            LayoutElement(role="body_text", text="Mass-energy equivalence", font_size=32, color=(30, 30, 30)),
            LayoutElement(role="subtitle", text="Einstein, 1905", font_size=30, color=(200, 200, 200)),
        ]

    r1 = engine.place(make_elements())
    r2 = engine.place(make_elements())

    bboxes_match = all(a.bbox == b.bbox for a, b in zip(r1, r2))
    return check(bboxes_match, "Two identical placements produce identical bboxes", "Determinism FAILED — bboxes differ")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    hr()
    print("  PHYSICS EDUCATION LAYOUT ENGINE — Integration Tests")
    print("  canvas support: 1920×1080 (16:9)  |  1080×1920 (9:16)")
    hr()

    results = {}

    results["basic_scene"]             = test_basic_scene()
    results["overlap_resolution"]      = test_overlap_resolution()
    results["subtitle_enforcement"]    = test_subtitle_zone_enforcement()
    results["contrast_utilities"]      = test_contrast_utilities()
    results["schema_validation"]       = test_schema_validation()
    results["shorts_aspect"]           = test_shorts_aspect()
    results["determinism"]             = test_determinism()

    # Summary
    section("SUMMARY")
    all_passed = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        all_passed = all_passed and passed

    print()
    if all_passed:
        print("  ALL TESTS PASSED")
    else:
        print("  SOME TESTS FAILED — see details above")

    hr()
    print()
    print("  Output files written:")
    for path in [
        "/tmp/test_layout_output.png",
        "/tmp/test_layout_overlap.png",
        "/tmp/test_layout_shorts.png",
    ]:
        exists = os.path.isfile(path)
        print(f"    {'[OK]' if exists else '[MISSING]'} {path}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
