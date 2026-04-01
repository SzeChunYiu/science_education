"""Full pipeline assembler for science education episodes.

Top-level entry point that orchestrates: script parsing, illustration,
animation, narration, music, and final video assembly.

CRITICAL: Models are loaded/unloaded sequentially to stay within 16GB
Apple Silicon unified memory.
"""
import logging
import subprocess
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class EpisodeAssembler:
    """Assemble a complete episode from script to final MP4.

    Pipeline stages (sequential model loading for 16GB memory):
        1. Parse script
        2. Generate production plan
        3. Generate narration (F5-TTS) -> word timestamps
        4. Generate illustrations (SDXL + quality orchestrator)
        5. Animate scenes (parallax + reveals synced to narration)
        6. Generate background music (MusicGen)
        7. Concatenate scene clips with transitions
        8. Mix audio: narration + music
        9. Mux video + audio -> final MP4
        10. Generate quality report

    Args:
        models_dir: Root directory for all model checkpoints.
        device: Torch device string (default "mps" for Apple Silicon).
    """

    def __init__(
        self,
        models_dir: Path = Path("models"),
        device: str = "mps",
    ):
        self.models_dir = Path(models_dir)
        self.device = device

    def assemble_episode(
        self,
        script_path: Path,
        output_dir: Path,
    ) -> Path:
        """Assemble a complete episode from a script file.

        Args:
            script_path: Path to episode markdown script.
            output_dir: Directory for all episode outputs.

        Returns:
            Path to final MP4 file.
        """
        script_path = Path(script_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        episode_id = script_path.stem
        logger.info(f"=== Assembling episode: {episode_id} ===")
        start_time = time.time()

        # --- Stage 1: Parse script ---
        logger.info("[1/10] Parsing script...")
        from src.pipeline.script_parser import parse_script
        parsed = parse_script(str(script_path))
        logger.info(
            f"  Parsed {len(parsed.segments)} segments, "
            f"~{parsed.total_duration:.0f}s total"
        )

        # --- Stage 2: Generate production plan ---
        logger.info("[2/10] Generating production plan...")
        from src.pipeline.scene_mapper import map_scenes
        scenes = map_scenes(parsed)
        logger.info(f"  Mapped {len(scenes)} scenes")

        # --- Stage 3: Generate narration (F5-TTS) ---
        logger.info("[3/10] Generating narration...")
        narration_dir = output_dir / "narration"
        narration_path, timestamps = self._generate_narration(
            script_path, narration_dir
        )
        logger.info(
            f"  Narration: {narration_path}, "
            f"{len(timestamps)} word timestamps"
        )

        # --- Stage 4: Generate illustrations (SDXL) ---
        logger.info("[4/10] Generating illustrations...")
        illustrations_dir = output_dir / "illustrations"
        illustration_paths = self._generate_illustrations(
            parsed, scenes, illustrations_dir
        )
        logger.info(f"  Generated {len(illustration_paths)} illustrations")

        # --- Stage 5: Animate scenes (parallax + reveals) ---
        logger.info("[5/10] Animating scenes...")
        clips_dir = output_dir / "clips"
        clip_paths = self._animate_scenes(
            scenes, illustration_paths, timestamps, clips_dir
        )
        logger.info(f"  Animated {len(clip_paths)} scene clips")

        # --- Stage 6: Generate background music (MusicGen) ---
        logger.info("[6/10] Generating background music...")
        music_path = self._generate_music(parsed, output_dir / "music")
        logger.info(f"  Music: {music_path}")

        # --- Stage 7: Concatenate scene clips ---
        logger.info("[7/10] Concatenating scene clips...")
        raw_video = output_dir / "raw_video.mp4"
        self._concatenate_clips(clip_paths, raw_video)

        # --- Stage 8: Mix audio ---
        logger.info("[8/10] Mixing audio...")
        mixed_audio = output_dir / "mixed_audio.m4a"
        self._mix_audio(narration_path, music_path, mixed_audio)

        # --- Stage 9: Mux video + audio ---
        logger.info("[9/10] Muxing final video...")
        final_path = output_dir / f"{episode_id}.mp4"
        self._mux_video_audio(raw_video, mixed_audio, final_path)

        # --- Stage 10: Quality report ---
        logger.info("[10/10] Generating quality report...")
        self._generate_quality_report(final_path, output_dir)

        elapsed = time.time() - start_time
        logger.info(
            f"=== Episode complete: {final_path} "
            f"({elapsed:.1f}s) ==="
        )
        return final_path

    def _generate_narration(
        self, script_path: Path, output_dir: Path
    ) -> tuple[Path, list[dict]]:
        """Load F5-TTS, generate narration, unload."""
        from src.audio.narration.f5_narrator import F5Narrator

        narrator = F5Narrator(
            model_dir=self.models_dir / "style_learner" / "voice",
            device=self.device,
        )
        narrator.load()
        try:
            narration_path, timestamps = narrator.render_episode(
                script_path, output_dir
            )
        finally:
            narrator.unload()

        return narration_path, timestamps

    def _generate_illustrations(
        self, parsed, scenes: list[dict], output_dir: Path
    ) -> list[Path]:
        """Load SDXL, generate all scene illustrations, unload."""
        output_dir.mkdir(parents=True, exist_ok=True)
        illustration_paths = []

        try:
            from src.style_learner.illustration.scene_illustrator import (
                SceneIllustrator,
            )

            illustrator = SceneIllustrator(
                style_lora_path=self.models_dir / "style_learner" / "lora",
                device=self.device,
            )
            illustrator.load()

            try:
                for i, scene in enumerate(scenes):
                    img_path = output_dir / f"scene_{i:03d}.png"
                    if hasattr(illustrator, "illustrate_scene"):
                        illustrator.illustrate_scene(scene, img_path)
                    illustration_paths.append(img_path)
            finally:
                if hasattr(illustrator, "unload"):
                    illustrator.unload()

        except (ImportError, Exception) as e:
            logger.warning(f"Illustration generation unavailable: {e}")
            # Create placeholder images
            self._create_placeholder_illustrations(
                len(scenes), output_dir, illustration_paths
            )

        return illustration_paths

    def _create_placeholder_illustrations(
        self, n_scenes: int, output_dir: Path, paths: list[Path]
    ):
        """Create solid-color placeholder images when SDXL is unavailable."""
        try:
            from PIL import Image

            for i in range(n_scenes):
                img_path = output_dir / f"scene_{i:03d}.png"
                img = Image.new("RGB", (1920, 1080), color=(30, 30, 50))
                img.save(img_path)
                paths.append(img_path)
        except ImportError:
            logger.error("PIL not available for placeholder generation")

    def _animate_scenes(
        self,
        scenes: list[dict],
        illustration_paths: list[Path],
        timestamps: list[dict],
        output_dir: Path,
    ) -> list[Path]:
        """Animate illustrations with parallax and reveals. CPU/PIL, no GPU."""
        output_dir.mkdir(parents=True, exist_ok=True)
        clip_paths = []

        try:
            from src.style_learner.animation_layer.parallax import (
                render_parallax_clip,
            )

            for i, (scene, img_path) in enumerate(
                zip(scenes, illustration_paths)
            ):
                clip_path = output_dir / f"clip_{i:03d}.mp4"
                duration = scene.get("duration", 5.0)

                if img_path.exists():
                    try:
                        render_parallax_clip(
                            image_path=img_path,
                            output_path=clip_path,
                            duration=duration,
                        )
                    except Exception as e:
                        logger.warning(
                            f"Parallax failed for scene {i}: {e}, "
                            f"using static frame"
                        )
                        self._static_clip(img_path, clip_path, duration)
                else:
                    self._static_clip(img_path, clip_path, duration)

                clip_paths.append(clip_path)

        except ImportError:
            logger.warning("Parallax module unavailable, using static clips")
            for i, img_path in enumerate(illustration_paths):
                clip_path = output_dir / f"clip_{i:03d}.mp4"
                duration = scenes[i].get("duration", 5.0) if i < len(scenes) else 5.0
                self._static_clip(img_path, clip_path, duration)
                clip_paths.append(clip_path)

        return clip_paths

    def _static_clip(self, image_path: Path, output_path: Path, duration: float):
        """Create a static video clip from a single image using ffmpeg."""
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,"
                   "pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            "-r", "30",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=False, timeout=60)

    def _generate_music(self, parsed, output_dir: Path) -> Path:
        """Load MusicGen, generate background music, unload."""
        output_dir.mkdir(parents=True, exist_ok=True)
        music_path = output_dir / "background.wav"

        from src.audio.music.musicgen_generator import MusicGenerator

        generator = MusicGenerator(device=self.device)
        generator.load()
        try:
            # Determine mood from script content
            mood = self._infer_mood(parsed)
            duration = max(int(parsed.total_duration), 60)
            generator.generate(
                mood=mood,
                duration=duration,
                output_path=music_path,
            )
        finally:
            generator.unload()

        return music_path

    def _infer_mood(self, parsed) -> str:
        """Infer music mood from script content."""
        all_text = " ".join(
            " ".join(seg.narrator_lines) for seg in parsed.segments
        ).lower()

        if any(w in all_text for w in ["exciting", "revolution", "breakthrough"]):
            return "inspiring and uplifting"
        if any(w in all_text for w in ["mysterious", "unknown", "puzzle"]):
            return "curious and mysterious"
        if any(w in all_text for w in ["tragic", "struggle", "difficult"]):
            return "contemplative and emotional"
        return "curious and wonder"

    def _concatenate_clips(self, clip_paths: list[Path], output: Path):
        """Concatenate scene clips into a single video."""
        valid_clips = [p for p in clip_paths if p.exists()]
        if not valid_clips:
            logger.error("No valid clips to concatenate")
            return

        list_file = output.parent / "_concat_clips.txt"
        with open(list_file, "w") as f:
            for p in valid_clips:
                f.write(f"file '{p.resolve()}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(output),
        ]
        subprocess.run(cmd, capture_output=True, check=False, timeout=300)
        list_file.unlink(missing_ok=True)
        logger.info(f"Concatenated {len(valid_clips)} clips: {output}")

    def _mix_audio(
        self, narration: Path, music: Path, output: Path
    ):
        """Mix narration and music tracks."""
        from src.audio.narration.audio_mixer import mix_audio, normalize_loudness

        if not narration.exists():
            logger.warning("No narration file, skipping audio mix")
            return

        # Mix narration + music
        raw_mix = output.with_name("_raw_mix.m4a")
        if music.exists():
            mix_audio(narration, music, raw_mix, music_db=-18.0)
        else:
            raw_mix = narration

        # Normalize to YouTube standard
        normalize_loudness(raw_mix, output, target_lufs=-16.0)

        # Clean up temp
        if raw_mix != narration and raw_mix.exists():
            raw_mix.unlink(missing_ok=True)

    def _mux_video_audio(
        self, video: Path, audio: Path, output: Path
    ):
        """Mux video and audio into final MP4."""
        if not video.exists():
            logger.error(f"Video file missing: {video}")
            return

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video),
        ]

        if audio.exists():
            cmd.extend(["-i", str(audio)])
            cmd.extend([
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
            ])
        else:
            cmd.extend(["-c:v", "copy"])

        cmd.append(str(output))

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"Mux failed: {result.stderr[-500:]}")
        else:
            logger.info(f"Final video: {output}")

    def _generate_quality_report(self, video_path: Path, output_dir: Path):
        """Generate a quality report for the assembled episode."""
        report_path = output_dir / "quality_report.json"

        import json

        report = {
            "episode": video_path.stem,
            "video_path": str(video_path),
            "video_exists": video_path.exists(),
        }

        # Get video info if it exists
        if video_path.exists():
            try:
                result = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-print_format", "json",
                     "-show_format", "-show_streams", str(video_path)],
                    capture_output=True, text=True, timeout=10,
                )
                info = json.loads(result.stdout)
                report["duration"] = float(
                    info.get("format", {}).get("duration", 0)
                )
                report["size_mb"] = round(
                    int(info.get("format", {}).get("size", 0)) / 1_048_576, 2
                )
                for stream in info.get("streams", []):
                    if stream.get("codec_type") == "video":
                        report["resolution"] = (
                            f"{stream.get('width')}x{stream.get('height')}"
                        )
                    elif stream.get("codec_type") == "audio":
                        report["audio_codec"] = stream.get("codec_name")
            except Exception as e:
                report["probe_error"] = str(e)

        report_path.write_text(json.dumps(report, indent=2))
        logger.info(f"Quality report: {report_path}")

    def assemble_batch(
        self,
        script_paths: list[Path],
        output_base: Path,
    ) -> list[Path]:
        """Process multiple episodes sequentially.

        Args:
            script_paths: List of script file paths.
            output_base: Base directory for all episode outputs.

        Returns:
            List of paths to final MP4 files.
        """
        output_base = Path(output_base)
        results = []

        for i, script_path in enumerate(script_paths):
            script_path = Path(script_path)
            episode_id = script_path.stem
            episode_dir = output_base / episode_id

            logger.info(
                f"\n{'='*60}\n"
                f"Episode {i+1}/{len(script_paths)}: {episode_id}\n"
                f"{'='*60}"
            )

            try:
                final_path = self.assemble_episode(script_path, episode_dir)
                results.append(final_path)
                logger.info(f"Completed: {final_path}")
            except Exception as e:
                logger.error(f"Failed to assemble {episode_id}: {e}")
                results.append(None)

        successful = sum(1 for r in results if r is not None)
        logger.info(
            f"\nBatch complete: {successful}/{len(script_paths)} episodes"
        )
        return results
