"""
Animation subsystem for physics education video production.

Submodules
----------
primitives
    Easing functions and per-element animation classes (FadeIn, SlideIn, etc.).
timeline
    ElementTimeline and SceneTimeline — the core scene/frame rendering engine.
scene_types
    Pre-built scene factories (equation_reveal_scene, character_introduction_scene, …).
ffmpeg_export
    Utilities for stitching PNG frames into MP4 via FFmpeg.

Typical usage
-------------
>>> from src.animation.scene_types import equation_reveal_scene
>>> from src.animation.ffmpeg_export import frames_to_video
>>>
>>> scene = equation_reveal_scene("F = ma", "Newton's Second Law", duration=5.0)
>>> scene.render_all("/tmp/frames/scene_01")
>>> frames_to_video("/tmp/frames/scene_01", "/tmp/out.mp4", fps=30)
"""

from src.animation.primitives import (
    # Easing functions
    linear,
    ease_in,
    ease_out,
    ease_in_out,
    bounce_out,
    spring,
    # Animation classes
    Animation,
    FadeIn,
    FadeOut,
    SlideIn,
    SlideOut,
    ScaleIn,
    ScaleOut,
    Pop,
    Shake,
    PulseOnce,
    TypeWriter,
    CompositeAnimation,
    # Factory
    animation_from_name,
)

from src.animation.timeline import (
    ElementTimeline,
    SceneTimeline,
)

from src.animation.scene_types import (
    equation_reveal_scene,
    character_introduction_scene,
    derivation_step_scene,
    two_character_debate_scene,
    diagram_explanation_scene,
    historical_moment_scene,
    limits_breakdown_scene,
    worked_example_scene,
    storybook_hook_title_card_scene,
    storybook_object_demo_scene,
    storybook_comparison_split_scene,
    storybook_timeline_sequence_scene,
    storybook_outro_bridge_scene,
)

from src.animation.physics_diagrams import PhysicsDiagramRenderer
from src.animation.circuit_diagrams import CircuitDiagramRenderer

from src.animation.ffmpeg_export import (
    frames_to_video,
    check_ffmpeg,
    get_video_info,
)

__all__ = [
    # Easing
    "linear",
    "ease_in",
    "ease_out",
    "ease_in_out",
    "bounce_out",
    "spring",
    # Animation base & classes
    "Animation",
    "FadeIn",
    "FadeOut",
    "SlideIn",
    "SlideOut",
    "ScaleIn",
    "ScaleOut",
    "Pop",
    "Shake",
    "PulseOnce",
    "TypeWriter",
    "CompositeAnimation",
    "animation_from_name",
    # Timeline
    "ElementTimeline",
    "SceneTimeline",
    # Scene type factories
    "equation_reveal_scene",
    "character_introduction_scene",
    "derivation_step_scene",
    "two_character_debate_scene",
    "diagram_explanation_scene",
    "historical_moment_scene",
    "limits_breakdown_scene",
    "worked_example_scene",
    "storybook_hook_title_card_scene",
    "storybook_object_demo_scene",
    "storybook_comparison_split_scene",
    "storybook_timeline_sequence_scene",
    "storybook_outro_bridge_scene",
    "PhysicsDiagramRenderer",
    "CircuitDiagramRenderer",
    # Export
    "frames_to_video",
    "check_ffmpeg",
    "get_video_info",
]
