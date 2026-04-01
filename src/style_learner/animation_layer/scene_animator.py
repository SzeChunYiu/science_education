"""High-level orchestrator producing animated scene clips from illustrations.

Combines depth splitting, parallax motion, narration-synced text reveals,
and frame export into a single pipeline that takes a static illustration
and returns a finished scene clip.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


class SceneAnimator:
    """Orchestrates the full animation pipeline for scene clips.

    Pipeline per scene:
        1. Depth-split illustration into layers (DepthSplitter)
        2. Render parallax frames from camera motion
        3. Overlay text reveals synced to narration
        4. Export frames to MP4

    Args:
        device: Torch device for depth model ("mps", "cpu", "cuda").
    """

    def __init__(self, device: str = "mps"):
        self.device = device
        self._depth_splitter = None

    @property
    def depth_splitter(self):
        """Lazy-load DepthSplitter to avoid import cost when not needed."""
        if self._depth_splitter is None:
            try:
                from src.style_learner.animation_layer.depth_splitter import DepthSplitter
                self._depth_splitter = DepthSplitter(device=self.device)
                logger.info("DepthSplitter initialized on %s", self.device)
            except Exception as e:
                logger.error("Failed to initialize DepthSplitter: %s", e)
                raise
        return self._depth_splitter

    def animate_scene(
        self,
        illustration: Image.Image,
        scene_plan: dict,
        transcript: list[dict],
        scene_start_time: float,
        output_dir: Path,
        fps: int = 30,
    ) -> Path:
        """Produce an animated MP4 clip for a single scene.

        Args:
            illustration: Source illustration as PIL Image.
            scene_plan: Dict with camera_motion, duration, text_elements, etc.
            transcript: Full episode transcript [{word, start, end}].
            scene_start_time: When this scene starts in the episode (seconds).
            output_dir: Directory to write frames and output clip.
            fps: Frames per second for the animation.

        Returns:
            Path to the rendered scene clip MP4.
        """
        from src.style_learner.animation_layer.parallax import render_parallax_frames
        from src.style_learner.animation_layer.narration_sync import (
            plan_visual_reveals,
            apply_reveals_to_frames,
        )

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        scene_duration = scene_plan.get("duration", 5.0)
        camera_motion = scene_plan.get("camera_motion", "static")
        canvas_size = (
            illustration.width if illustration.width > 0 else 1920,
            illustration.height if illustration.height > 0 else 1080,
        )

        # --- Step 1: Depth-split ---
        logger.info("Step 1: Depth splitting illustration (%dx%d)",
                     illustration.width, illustration.height)
        try:
            layers = self.depth_splitter.split(illustration)
        except Exception as e:
            logger.warning("Depth split failed (%s), using single-layer fallback", e)
            layers = {
                "foreground": illustration.convert("RGBA"),
                "midground": Image.new("RGBA", illustration.size, (0, 0, 0, 0)),
                "background": illustration.convert("RGBA"),
            }

        # --- Step 2: Parallax frames ---
        logger.info("Step 2: Rendering parallax frames (motion=%s, %.1fs at %dfps)",
                     camera_motion, scene_duration, fps)
        total_frames = int(scene_duration * fps)

        try:
            parallax_frames = render_parallax_frames(
                layers=layers,
                motion_type=camera_motion,
                num_frames=total_frames,
                canvas_size=canvas_size,
            )
        except Exception as e:
            logger.warning("Parallax rendering failed (%s), using static frames", e)
            base_frame = illustration.convert("RGB")
            parallax_frames = [base_frame.copy() for _ in range(total_frames)]

        # --- Step 3: Text reveals ---
        logger.info("Step 3: Planning and applying text reveals")
        reveals = plan_visual_reveals(
            scene=scene_plan,
            transcript=transcript,
            scene_start_time=scene_start_time,
            scene_duration=scene_duration,
        )

        if reveals:
            logger.info("  %d text reveals planned", len(reveals))
            parallax_frames = apply_reveals_to_frames(
                frames=parallax_frames,
                reveals=reveals,
                fps=fps,
                canvas_size=canvas_size,
            )

        # --- Step 4: Export to MP4 ---
        logger.info("Step 4: Exporting %d frames to MP4", len(parallax_frames))
        frames_dir = output_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        for idx, frame in enumerate(parallax_frames):
            frame_path = frames_dir / f"frame_{idx:05d}.png"
            frame.save(frame_path)

        scene_id = scene_plan.get("scene_id", "scene")
        clip_path = output_dir / f"{scene_id}.mp4"

        try:
            from src.animation.ffmpeg_export import frames_to_video
            frames_to_video(
                frames_dir=str(frames_dir),
                output_path=str(clip_path),
                fps=fps,
            )
        except ImportError:
            logger.error("ffmpeg_export module not available, cannot create video")
            raise
        except Exception as e:
            logger.error("Video export failed: %s", e)
            raise

        # Clean up frames
        shutil.rmtree(frames_dir, ignore_errors=True)

        logger.info("Scene clip saved: %s", clip_path)
        return clip_path

    def animate_episode(
        self,
        illustrations: list[Image.Image],
        production_plan: dict,
        transcript: list[dict],
        output_dir: Path,
    ) -> list[Path]:
        """Animate all scenes in an episode.

        Args:
            illustrations: One illustration per scene.
            production_plan: Full production plan dict with scenes list.
            transcript: Full episode transcript [{word, start, end}].
            output_dir: Base output directory for all clips.

        Returns:
            List of paths to scene clip MP4s, in order.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        scenes = production_plan.get("scenes", [])
        fps = production_plan.get("fps", 30)

        if len(illustrations) != len(scenes):
            logger.warning(
                "Illustration count (%d) != scene count (%d). "
                "Will process min(%d, %d) scenes.",
                len(illustrations), len(scenes),
                len(illustrations), len(scenes),
            )

        clip_paths = []
        scene_start_time = 0.0

        for idx in range(min(len(illustrations), len(scenes))):
            scene_plan = scenes[idx]
            scene_plan.setdefault("scene_id", f"scene_{idx:03d}")
            scene_duration = scene_plan.get("duration", 5.0)

            logger.info(
                "Animating scene %d/%d (start=%.1fs, dur=%.1fs)",
                idx + 1, len(scenes), scene_start_time, scene_duration,
            )

            scene_output = output_dir / scene_plan["scene_id"]
            clip_path = self.animate_scene(
                illustration=illustrations[idx],
                scene_plan=scene_plan,
                transcript=transcript,
                scene_start_time=scene_start_time,
                output_dir=scene_output,
                fps=fps,
            )

            clip_paths.append(clip_path)
            scene_start_time += scene_duration

        logger.info("Episode animation complete: %d clips", len(clip_paths))
        return clip_paths
