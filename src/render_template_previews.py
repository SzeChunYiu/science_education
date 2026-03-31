"""
Render a broad template-preview pack for QA.

The preview pack is rendered through the same
scene-descriptor -> slide-planner -> episode-renderer path used by the
current production renderer, so template QA exercises the actual layout
planning method instead of a separate manual preview route.

Usage:
    python3 -m src.render_template_previews
    python3 -m src.render_template_previews --only equation_reveal animation_scene
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.animation import (
    check_ffmpeg,
    frames_to_video,
    get_video_info,
)
from src.animation.circuit_diagrams import CircuitDiagramRenderer
from src.animation.physics_diagrams import PhysicsDiagramRenderer
from src.pipeline.episode_renderer import build_scene_timeline


def _asset(*parts: str) -> str:
    return str(PROJECT_ROOT.joinpath(*parts))


def _render_scene(name: str, scene_spec, out_dir: Path, fps: int, aspect_ratio: str) -> Path:
    frames_dir = out_dir / f"{name}_frames"
    mp4_path = out_dir / f"preview_{name}.mp4"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)
    scene = build_scene_timeline(scene_spec, aspect_ratio=aspect_ratio, fps=fps) if isinstance(scene_spec, dict) else scene_spec
    scene.render_all(str(frames_dir), verbose=False)
    frames_to_video(str(frames_dir), str(mp4_path), fps=fps)
    shutil.rmtree(frames_dir, ignore_errors=True)
    return mp4_path


def _scene_dict(template: str, duration: float, background: str, elements: list[dict], **extra: object) -> dict[str, object]:
    scene = {
        "scene_id": f"preview_{template}",
        "template": template,
        "duration": duration,
        "background": background,
        "elements": elements,
    }
    scene.update(extra)
    return scene


def _generate_preview_diagram_assets() -> dict[str, str]:
    asset_dir = (PROJECT_ROOT / "output" / "preview_assets").resolve()
    asset_dir.mkdir(parents=True, exist_ok=True)

    physics = PhysicsDiagramRenderer(width=1600, height=900)
    circuit = CircuitDiagramRenderer()

    force_path = asset_dir / "diagram_force_body.png"
    physics.force_diagram(
        forces=[
            ("N", "up", 220, "#3A7BD5"),
            ("W", "down", 220, "#E8503A"),
            ("F", "right", 260, "#27AE60"),
            ("f", "left", 140, "#E67E22"),
        ],
        object_label="m",
        title="Free-Body Diagram",
        subtitle="A pushed block on rough ground",
    ).save(force_path)

    motion_path = asset_dir / "diagram_motion.png"
    physics.motion_diagram(
        n_positions=5,
        accelerating=True,
        title="Motion Diagram",
    ).save(motion_path)

    energy_path = asset_dir / "diagram_energy.png"
    physics.energy_diagram(
        before=(40, 80),
        after=(90, 30),
        title="Energy Transfer",
    ).save(energy_path)

    incline_path = asset_dir / "diagram_inclined_plane.png"
    physics.inclined_plane(
        angle_deg=32.0,
        show_components=True,
        title="Inclined Plane Forces",
    ).save(incline_path)

    spring_diag_path = asset_dir / "diagram_spring.png"
    physics.spring_diagram(
        extension=0.42,
        title="Spring Force Diagram",
        show_force_arrow=True,
        displacement_label="x",
    ).save(spring_diag_path)

    circuit_path = asset_dir / "diagram_circuit_rc.png"
    circuit.simple_series_rc(
        circuit_path,
        source_label="V",
        resistor_label="R",
        capacitor_label="C",
    )

    circuit_lamp_path = asset_dir / "diagram_circuit_battery_lamp.png"
    circuit.simple_battery_lamp(
        circuit_lamp_path,
        source_label="Battery",
        lamp_label="Lamp",
    )

    return {
        "force": str(force_path),
        "motion": str(motion_path),
        "energy": str(energy_path),
        "incline": str(incline_path),
        "spring": str(spring_diag_path),
        "circuit": str(circuit_path),
        "circuit_lamp": str(circuit_lamp_path),
    }


def _build_scenes(aspect_ratio: str, fps: int) -> dict[str, object]:
    char_aristotle = _asset("data", "assets", "physics", "test_v3", "char_aristotle_v3.png")
    char_newton = _asset("data", "assets", "physics", "test_v3", "char_newton_v3.png")
    char_galileo = _asset("data", "assets", "physics", "test_v3", "char_galileo_v3.png")
    bg_greece = _asset("data", "assets", "physics", "test_v3", "bg_ancient_greece.png")
    bg_grass = _asset("data", "assets", "physics", "test_v3", "bg_grass_field.png")
    ball = _asset("data", "assets", "physics", "objects", "obj_ball_red.png")
    airflow = _asset("data", "assets", "physics", "objects", "obj_airflow_streamlines.png")
    pendulum = _asset("data", "assets", "physics", "objects", "obj_pendulum.png")
    spring = _asset("data", "assets", "physics", "objects", "obj_coil_spring.png")
    arrow = _asset("data", "assets", "physics", "objects", "obj_arrow_right.png")
    globe = _asset("data", "assets", "physics", "objects", "obj_earth_globe.png")
    ramp = _asset("data", "assets", "physics", "objects", "obj_ramp_wood.png")
    diagrams = _generate_preview_diagram_assets()

    return {
        "narration_with_caption": _scene_dict(
            "narration_with_caption",
            3.0,
            bg_greece,
            [
                {"role": "headline", "text": "Push a ball. It slows down. Why?"},
                {"role": "body_text", "text": "For centuries, people thought motion always needed a mover."},
                {"role": "diagram", "asset_path": ball, "text": None},
            ],
            badge_text="Hook",
        ),
        "equation_reveal": _scene_dict(
            "equation_reveal",
            5.0,
            "",
            [
                {"role": "equation_center", "text": r"F = ma"},
                {"role": "caption", "text": "Force equals mass times acceleration."},
            ],
        ),
        "equation_reveal_complex": _scene_dict(
            "equation_reveal",
            5.5,
            "",
            [
                {"role": "equation_center", "text": r"\int_{0}^{1} x^2\,dx = \frac{1}{3}"},
                {"role": "caption", "text": "Integral of x squared from zero to one."},
            ],
        ),
        "equation_reveal_indexed": _scene_dict(
            "equation_reveal",
            5.0,
            "",
            [
                {"role": "equation_center", "text": r"\sum_{n=0}^{\infty} a_n = S"},
                {"role": "caption", "text": "Indexed sum with an infinite upper limit."},
            ],
        ),
        "derivation_step": _scene_dict(
            "derivation_step",
            5.5,
            "",
            [
                {"role": "headline", "text": r"p = mv"},
                {"role": "timeline", "text": r"F = \frac{dp}{dt} = m\frac{dv}{dt}"},
                {"role": "caption", "text": "Differentiate momentum with respect to time."},
            ],
        ),
        "diagram_explanation": _scene_dict(
            "diagram_explanation",
            5.0,
            "",
            [
                {"role": "diagram", "asset_path": pendulum, "text": "Pendulum motion"},
                {"role": "caption", "text": "Gravity pulls down. Tension pulls inward."},
            ],
        ),
        "animation_scene": _scene_dict(
            "animation_scene",
            5.0,
            bg_grass,
            [
                {"role": "diagram", "asset_path": ball, "text": "Air rushing around a thrown ball"},
                {"role": "caption", "text": "The ball must stay visible throughout the motion, while air streams around it."},
                {"role": "accent", "asset_path": airflow, "text": None},
            ],
        ),
        "character_scene": _scene_dict(
            "character_scene",
            5.0,
            bg_greece,
            [
                {"role": "character_center", "asset_path": char_aristotle, "text": None},
                {"role": "lower_third", "text": "Motion needs a cause."},
            ],
        ),
        "two_character_debate": _scene_dict(
            "two_character_debate",
            5.5,
            "",
            [
                {"role": "character_left", "asset_path": char_aristotle, "text": None},
                {"role": "character_right", "asset_path": char_newton, "text": None},
                {"role": "lower_third", "text": "Aristotle"},
                {"role": "lower_third", "text": "Newton"},
                {"role": "caption", "text": "Motion needs a mover."},
                {"role": "caption", "text": "Change in motion needs a net force."},
            ],
        ),
        "two_element_comparison": _scene_dict(
            "two_element_comparison",
            5.5,
            "",
            [
                {"role": "character_left", "text": "Ball at rest, no motion.", "asset_path": ball},
                {"role": "character_right", "text": "Ball in flight, visible motion.", "asset_path": arrow},
            ],
            bridge_text="Same ball, different state",
        ),
        "historical_moment": _scene_dict(
            "historical_moment",
            5.5,
            bg_greece,
            [
                {"role": "character_center", "asset_path": char_galileo, "text": None},
                {"role": "lower_third", "text": "1604 · Padua"},
                {"role": "caption", "text": "Galileo studies falling bodies."},
            ],
        ),
        "object_demo": _scene_dict(
            "object_demo",
            5.5,
            "",
            [
                {"role": "headline", "text": "A spring stores elastic force"},
                {"role": "diagram", "asset_path": spring, "text": None},
                {"role": "caption", "text": "Stretch the spring and the restoring force grows."},
                {"role": "lower_third", "text": "Hooke's law preview"},
                {"role": "accent", "asset_path": arrow, "text": None},
            ],
        ),
        "timeline_sequence": _scene_dict(
            "timeline_sequence",
            6.5,
            "",
            [
                {"role": "headline", "text": "Three turning points"},
                {"role": "timeline", "text": "1604 | Falling bodies", "asset_path": char_galileo},
                {"role": "timeline", "text": "1687 | Newton's laws", "asset_path": char_newton},
                {"role": "timeline", "text": "1905 | Relativity", "asset_path": char_aristotle},
            ],
        ),
        "limits_breakdown": _scene_dict(
            "limits_breakdown",
            5.0,
            "",
            [
                {"role": "headline", "text": "Classical intuition fails."},
                {"role": "equation_center", "text": r"\gamma = \frac{1}{\sqrt{1 - v^2/c^2}}"},
                {"role": "caption", "text": r"\gamma \to \infty \;\; \mathrm{as} \;\; v \to c"},
            ],
        ),
        "worked_example": _scene_dict(
            "worked_example",
            7.0,
            "",
            [
                {"role": "headline", "text": "A 2 kg cart accelerates at 3 m/s^2."},
                {"role": "equation_center", "text": r"F = ma"},
                {"role": "caption", "text": r"F = 2 \times 3"},
                {"role": "lower_third", "text": r"F = 6\,\mathrm{N}"},
            ],
        ),
        "outro_bridge": _scene_dict(
            "outro_bridge",
            4.5,
            bg_greece,
            [
                {"role": "headline", "text": "The story behind the equation"},
                {"role": "body_text", "text": "Scenes should make sense at a glance."},
                {"role": "caption", "text": "Next: constant velocity"},
                {"role": "diagram", "asset_path": char_newton, "text": None},
            ],
        ),
        "physics_force_diagram": _scene_dict(
            "diagram_explanation",
            5.0,
            "",
            [
                {"role": "diagram", "asset_path": diagrams["force"], "text": "Free-body diagram"},
                {"role": "caption", "text": "Normal force up, weight down, applied force right, friction left."},
            ],
        ),
        "physics_motion_diagram": _scene_dict(
            "diagram_explanation",
            5.0,
            "",
            [
                {"role": "diagram", "asset_path": diagrams["motion"], "text": "Accelerating motion diagram"},
                {"role": "caption", "text": "The spacing between positions grows as the object speeds up."},
            ],
        ),
        "physics_energy_diagram": _scene_dict(
            "diagram_explanation",
            5.0,
            "",
            [
                {"role": "diagram", "asset_path": diagrams["energy"], "text": "Energy bar diagram"},
                {"role": "caption", "text": "Kinetic energy rises while potential energy falls."},
            ],
        ),
        "physics_inclined_plane": _scene_dict(
            "diagram_explanation",
            5.0,
            "",
            [
                {"role": "diagram", "asset_path": diagrams["incline"], "text": "Inclined plane forces"},
                {"role": "caption", "text": "Weight splits into components parallel and perpendicular to the slope."},
            ],
        ),
        "physics_spring_diagram": _scene_dict(
            "diagram_explanation",
            5.0,
            "",
            [
                {"role": "diagram", "asset_path": diagrams["spring"], "text": "Spring force diagram"},
                {"role": "caption", "text": "The restoring force points back toward the relaxed position."},
            ],
        ),
        "circuit_series_rc": _scene_dict(
            "diagram_explanation",
            5.0,
            "",
            [
                {"role": "diagram", "asset_path": diagrams["circuit"], "text": "Series RC circuit"},
                {"role": "caption", "text": "A source drives current through a resistor and capacitor in one loop."},
            ],
        ),
        "circuit_battery_lamp": _scene_dict(
            "diagram_explanation",
            5.0,
            "",
            [
                {"role": "diagram", "asset_path": diagrams["circuit_lamp"], "text": "Battery and lamp circuit"},
                {"role": "caption", "text": "A simple closed loop lights the lamp when the circuit is complete."},
            ],
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Render comprehensive template previews.")
    parser.add_argument("--outdir", default="output/previews", help="Output directory for preview MP4s.")
    parser.add_argument("--fps", type=int, default=24, help="Output fps.")
    parser.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16"])
    parser.add_argument("--only", nargs="*", default=[], help="Optional subset of scene keys to render.")
    args = parser.parse_args()

    if not check_ffmpeg():
        raise SystemExit("ffmpeg not found on PATH")

    out_dir = (PROJECT_ROOT / args.outdir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    scenes = _build_scenes(args.aspect_ratio, args.fps)
    selected = args.only or list(scenes.keys())

    for key in selected:
        if key not in scenes:
            raise SystemExit(f"Unknown scene key: {key}")

    print(f"Rendering {len(selected)} template previews -> {out_dir}")
    for key in selected:
        path = _render_scene(key, scenes[key], out_dir, args.fps, args.aspect_ratio)
        info = get_video_info(str(path))
        print(f"  {path.name}: {info['duration']:.2f}s {info['width']}x{info['height']} audio={info['audio_codec'] or 'none'}")


if __name__ == "__main__":
    main()
