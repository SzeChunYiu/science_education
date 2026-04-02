"""
Storyboard schema -- the contract between Claude CLI (director) and the renderer.

A storyboard is a list of scenes. Each scene has:
- A background
- A list of timed visual beats (element enter/exit/transform events)
- Subtitle text synced to narration

This schema is what Claude CLI outputs and the renderer consumes.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Beat:
    """A single visual event -- an element entering, exiting, or changing."""
    time: float                    # seconds from scene start
    action: str                    # "enter", "exit", "move", "highlight", "transform"
    element_id: str                # unique ID within the scene
    role: str                      # "character", "prop", "equation", "label", "diagram", "accent"
    asset: Optional[str] = None    # asset filename (e.g. "char_newton", "obj_ball_red")
    text: Optional[str] = None     # text content (for equations, labels, captions)
    x: float = 0.5                 # x position as fraction of canvas width (0.0-1.0)
    y: float = 0.5                 # y position as fraction of canvas height (0.0-1.0)
    w: float = 0.2                 # width as fraction of canvas
    h: float = 0.2                 # height as fraction of canvas
    animation: str = "fade_in"     # animation type
    duration: float = 0.5          # animation duration in seconds
    font_size: int = 48            # for text elements


@dataclass
class StoryboardScene:
    """One continuous scene with a fixed background."""
    scene_id: str
    background: str                # background asset stem (e.g. "bg_study")
    duration: float                # total scene duration in seconds
    beats: list[Beat] = field(default_factory=list)
    narrator_text: str = ""        # full narrator text for this scene


@dataclass
class Storyboard:
    """Complete episode storyboard -- the output of Claude CLI direction."""
    episode_id: str
    title: str
    scenes: list[StoryboardScene] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        import dataclasses
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Storyboard":
        """Deserialize from JSON dict."""
        scenes = []
        for s in data.get("scenes", []):
            raw_beats = s.pop("beats", [])
            beats = [Beat(**b) for b in raw_beats]
            scenes.append(StoryboardScene(**s, beats=beats))
        return cls(
            episode_id=data["episode_id"],
            title=data.get("title", ""),
            scenes=scenes,
        )
