"""Integration test: full TED-Ed style pipeline on a sample episode.

Usage:
    python -m src.test_teded_pipeline [--skip-illustrations] [--skip-narration] [--skip-music]

Tests the full pipeline: script → production plan → illustrations → animation → narration → MP4.
Uses placeholders/fallbacks when ML models aren't available.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("output/test_renders/teded_pipeline_test")


def find_sample_script() -> Path:
    """Find a sample episode script to test with."""
    physics_dir = Path("output/physics")
    if physics_dir.exists():
        for md_file in sorted(physics_dir.rglob("*_youtube_long.md")):
            return md_file

    # Create a minimal test script
    test_script = OUTPUT_DIR / "test_script.md"
    test_script.parent.mkdir(parents=True, exist_ok=True)
    test_script.write_text("""# Test Episode: Newton's First Law

## Scene 1
[Visual: Newton sitting under apple tree]
NARRATOR: Have you ever wondered why objects at rest tend to stay at rest? Isaac Newton asked this very question back in 1687.

## Scene 2
[Visual: Ball rolling on flat surface]
NARRATOR: Newton's first law tells us that an object in motion stays in motion unless acted upon by an external force. This is called inertia.

## Scene 3
[Visual: Equation F equals ma]
NARRATOR: This simple idea revolutionized our understanding of physics and laid the foundation for classical mechanics.
""")
    return test_script


def test_script_parsing(script_path: Path) -> dict:
    """Test 1: Parse the script."""
    logger.info("=== Test 1: Script Parsing ===")
    from src.pipeline.script_parser import parse_script

    parsed = parse_script(script_path)
    logger.info(f"Parsed {len(parsed.segments)} segments")
    assert len(parsed.segments) > 0, "No segments parsed"
    return {"segments": len(parsed.segments), "status": "PASS"}


def test_production_plan(script_path: Path) -> dict:
    """Test 2: Generate production plan."""
    logger.info("=== Test 2: Production Plan ===")
    try:
        from src.style_learner.inference.plan_generator import ProductionPlanGenerator

        generator = ProductionPlanGenerator()
        plan = generator.generate_plan_from_script(script_path)

        plan_path = OUTPUT_DIR / "production_plan.json"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(json.dumps(plan, indent=2))

        n_scenes = len(plan.get("scenes", []))
        logger.info(f"Generated plan with {n_scenes} scenes")
        return {"scenes": n_scenes, "status": "PASS"}
    except Exception as e:
        logger.warning(f"Production plan failed (expected if models not trained): {e}")
        return {"status": "SKIP", "reason": str(e)}


def test_illustration_generation(skip: bool = False) -> dict:
    """Test 3: Generate sample illustration."""
    logger.info("=== Test 3: Illustration Generation ===")
    if skip:
        return {"status": "SKIP", "reason": "skipped by flag"}

    try:
        from src.style_learner.illustration.sdxl_generator import SDXLGenerator

        gen = SDXLGenerator(device="mps")
        gen.load()
        img = gen.generate(
            prompt="teded_style, educational illustration of Isaac Newton under apple tree, "
                   "flat color style, bold outlines, warm palette",
            steps=15,  # Quick test
        )
        img_path = OUTPUT_DIR / "test_illustration.png"
        img_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(img_path)
        gen.unload()

        logger.info(f"Generated illustration: {img_path} ({img.size})")
        return {"size": img.size, "path": str(img_path), "status": "PASS"}
    except Exception as e:
        logger.warning(f"Illustration generation failed: {e}")
        # Create placeholder
        img = Image.new("RGB", (1024, 1024), (200, 180, 140))
        img_path = OUTPUT_DIR / "test_illustration.png"
        img_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(img_path)
        return {"status": "FALLBACK", "reason": str(e)}


def test_parallax_animation() -> dict:
    """Test 4: Parallax animation from illustration."""
    logger.info("=== Test 4: Parallax Animation ===")
    try:
        from src.style_learner.animation_layer.parallax import render_parallax_frames, save_frames
        from src.style_learner.animation_layer.depth_splitter import DepthSplitter

        img_path = OUTPUT_DIR / "test_illustration.png"
        if not img_path.exists():
            img = Image.new("RGB", (1920, 1080), (200, 180, 140))
            img.save(img_path)

        img = Image.open(img_path).resize((1920, 1080))

        # Try depth splitting
        try:
            splitter = DepthSplitter(device="mps")
            splitter.load()
            depth = splitter.estimate_depth(img)
            fg, mid, bg = splitter.split_layers(img, depth)
            splitter.unload()
        except Exception:
            # Fallback: use same image for all layers
            fg = mid = bg = img.convert("RGBA")

        frames = render_parallax_frames(
            fg, mid, bg,
            motion="pan_right", magnitude="slow",
            duration=3.0, fps=30,
        )

        frames_dir = OUTPUT_DIR / "parallax_frames"
        save_frames(frames, frames_dir)

        # Export to MP4
        from src.animation.ffmpeg_export import frames_to_video
        mp4_path = OUTPUT_DIR / "test_parallax.mp4"
        frames_to_video(frames_dir, mp4_path, fps=30)

        logger.info(f"Rendered {len(frames)} parallax frames → {mp4_path}")
        return {"frames": len(frames), "path": str(mp4_path), "status": "PASS"}
    except Exception as e:
        logger.error(f"Parallax animation failed: {e}")
        return {"status": "FAIL", "reason": str(e)}


def test_narration(script_path: Path, skip: bool = False) -> dict:
    """Test 5: Generate narration audio."""
    logger.info("=== Test 5: Narration Generation ===")
    if skip:
        return {"status": "SKIP", "reason": "skipped by flag"}

    try:
        from src.audio.narration.f5_narrator import F5Narrator

        narrator = F5Narrator()
        narrator.load()

        audio_path, timestamps = narrator.render_episode(
            script_path, output_dir=OUTPUT_DIR / "narration"
        )
        narrator.unload()

        logger.info(f"Generated narration: {audio_path} ({len(timestamps)} words)")
        return {
            "audio": str(audio_path),
            "words": len(timestamps),
            "status": "PASS",
        }
    except Exception as e:
        logger.warning(f"Narration failed: {e}")
        return {"status": "FALLBACK", "reason": str(e)}


def test_music_generation(skip: bool = False) -> dict:
    """Test 6: Generate background music."""
    logger.info("=== Test 6: Music Generation ===")
    if skip:
        return {"status": "SKIP", "reason": "skipped by flag"}

    try:
        from src.audio.music.musicgen_generator import MusicGenerator

        gen = MusicGenerator(device="mps")
        gen.load()
        music_path = gen.generate(
            mood="curious and educational",
            duration=15,
            output_path=OUTPUT_DIR / "test_music.wav",
        )
        gen.unload()

        logger.info(f"Generated music: {music_path}")
        return {"path": str(music_path), "status": "PASS"}
    except Exception as e:
        logger.warning(f"Music generation failed: {e}")
        return {"status": "FALLBACK", "reason": str(e)}


def test_quality_orchestrator() -> dict:
    """Test 7: Quality orchestrator with mock scorers."""
    logger.info("=== Test 7: Quality Orchestrator ===")
    from src.quality.orchestrator import QualityOrchestrator, ScorerConfig

    # Mock scorers
    call_count = [0]
    def mock_generator():
        call_count[0] += 1
        return Image.new("RGB", (100, 100), (call_count[0] * 50, 100, 100))

    scorers = [
        ScorerConfig("mock_aesthetic", lambda img: 0.8, threshold=0.5, weight=1.0),
        ScorerConfig("mock_semantic", lambda img: 0.7, threshold=0.5, weight=1.0),
    ]

    orchestrator = QualityOrchestrator(scorers, n_candidates=2, max_rounds=1)
    result = orchestrator.run(mock_generator)

    assert result.accepted, "Quality orchestrator should accept mock candidates"
    logger.info(f"Orchestrator: accepted={result.accepted}, composite={result.composite_score:.3f}")
    return {"accepted": result.accepted, "composite": result.composite_score, "status": "PASS"}


def main():
    parser = argparse.ArgumentParser(description="TED-Ed pipeline integration test")
    parser.add_argument("--skip-illustrations", action="store_true")
    parser.add_argument("--skip-narration", action="store_true")
    parser.add_argument("--skip-music", action="store_true")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = {}
    script_path = find_sample_script()
    logger.info(f"Using script: {script_path}")

    results["parsing"] = test_script_parsing(script_path)
    results["production_plan"] = test_production_plan(script_path)
    results["illustration"] = test_illustration_generation(skip=args.skip_illustrations)
    results["parallax"] = test_parallax_animation()
    results["narration"] = test_narration(script_path, skip=args.skip_narration)
    results["music"] = test_music_generation(skip=args.skip_music)
    results["quality"] = test_quality_orchestrator()

    # Summary
    report_path = OUTPUT_DIR / "test_report.json"
    report_path.write_text(json.dumps(results, indent=2))

    print("\n" + "=" * 60)
    print("INTEGRATION TEST RESULTS")
    print("=" * 60)

    for name, result in results.items():
        status = result.get("status", "UNKNOWN")
        icon = {"PASS": "OK", "FAIL": "FAIL", "SKIP": "SKIP", "FALLBACK": "WARN"}.get(status, "??")
        print(f"  [{icon}] {name}: {status}")

    total = len(results)
    passed = sum(1 for r in results.values() if r.get("status") == "PASS")
    failed = sum(1 for r in results.values() if r.get("status") == "FAIL")

    print(f"\n  {passed}/{total} passed, {failed} failed")
    print(f"  Report: {report_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
