"""F5-TTS narrator for generating educational narration audio."""
import logging
import subprocess
import json
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class F5Narrator:
    """Generate narration audio using F5-TTS with voice cloning."""

    def __init__(
        self,
        model_dir: Path = Path("models/style_learner/voice"),
        reference_audio: Path = None,
        device: str = "mps",
    ):
        self.model_dir = model_dir
        self.reference_audio = reference_audio
        self.device = device
        self._model = None

    def load(self):
        """Load F5-TTS model."""
        try:
            from f5_tts.api import F5TTS
            self._model = F5TTS(device=self.device)

            # Load fine-tuned checkpoint if available
            ckpt = self.model_dir / "model_last.pt"
            if ckpt.exists():
                self._model.load_checkpoint(str(ckpt))
                logger.info(f"Loaded fine-tuned voice from {ckpt}")
            else:
                logger.info("Using base F5-TTS model (no fine-tuned checkpoint)")
        except ImportError:
            logger.warning("F5-TTS not installed, will fall back to edge-tts")
            self._model = None

    def generate_segment(
        self,
        text: str,
        output_path: Path,
        reference_audio: Path = None,
    ) -> Path:
        """Generate audio for a single text segment.

        Args:
            text: Text to speak
            output_path: Where to save the audio file
            reference_audio: Voice reference clip for cloning (optional)

        Returns:
            Path to generated audio file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ref = reference_audio or self.reference_audio

        if self._model is not None and ref and ref.exists():
            try:
                wav, sr = self._model.infer(
                    ref_file=str(ref),
                    ref_text="",  # Auto-transcribe reference
                    gen_text=text,
                )
                import soundfile as sf
                sf.write(str(output_path), wav, sr)
                logger.info(f"Generated narration: {output_path}")
                return output_path
            except Exception as e:
                logger.error(f"F5-TTS generation failed: {e}")

        # Fallback to edge-tts
        return self._generate_edge_tts(text, output_path)

    def _generate_edge_tts(self, text: str, output_path: Path) -> Path:
        """Fallback narration using edge-tts."""
        wav_path = output_path.with_suffix(".mp3")
        cmd = [
            "edge-tts",
            "--voice", "en-US-GuyNeural",
            "--rate", "+0%",
            "--text", text,
            "--write-media", str(wav_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=60)
            # Convert to wav if needed
            if output_path.suffix == ".wav":
                subprocess.run([
                    "ffmpeg", "-y", "-i", str(wav_path),
                    "-ar", "24000", "-ac", "1", str(output_path)
                ], capture_output=True, check=True)
                wav_path.unlink(missing_ok=True)
            else:
                output_path = wav_path
            logger.info(f"Generated narration (edge-tts fallback): {output_path}")
        except Exception as e:
            logger.error(f"edge-tts failed: {e}")
        return output_path

    def render_episode(
        self,
        script_path: Path | str,
        output_dir: Path = None,
    ) -> tuple[Path, list[dict]]:
        """Render narration for an entire episode script.

        Returns:
            (full_narration_path, word_timestamps)
        """
        from src.pipeline.script_parser import parse_script

        script_path = Path(script_path)
        if output_dir is None:
            output_dir = script_path.parent / "narration"
        output_dir.mkdir(parents=True, exist_ok=True)

        parsed = parse_script(script_path)
        segment_paths = []
        all_timestamps = []
        current_time = 0.0

        for i, segment in enumerate(parsed.segments):
            text = " ".join(segment.narrator_lines).strip()
            if not text:
                continue

            seg_path = output_dir / f"segment_{i:03d}.wav"
            self.generate_segment(text, seg_path)

            if seg_path.exists():
                # Get duration
                duration = self._get_audio_duration(seg_path)

                # Approximate word timestamps
                words = text.split()
                word_dur = duration / max(len(words), 1)
                for j, word in enumerate(words):
                    all_timestamps.append({
                        "word": word,
                        "start": round(current_time + j * word_dur, 3),
                        "end": round(current_time + (j + 1) * word_dur, 3),
                    })

                current_time += duration
                segment_paths.append(seg_path)

        # Concatenate all segments
        full_path = output_dir / "full_narration.wav"
        if segment_paths:
            self._concatenate_audio(segment_paths, full_path)

        # Save timestamps
        ts_path = output_dir / "timestamps.json"
        ts_path.write_text(json.dumps(all_timestamps, indent=2))

        return full_path, all_timestamps

    def _get_audio_duration(self, path: Path) -> float:
        """Get audio duration in seconds."""
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", str(path)],
            capture_output=True, text=True,
        )
        try:
            info = json.loads(result.stdout)
            return float(info["format"]["duration"])
        except (json.JSONDecodeError, KeyError):
            return 5.0  # Default estimate

    def _concatenate_audio(self, paths: list[Path], output: Path):
        """Concatenate audio files with short pauses between."""
        list_file = output.parent / "concat_list.txt"
        with open(list_file, "w") as f:
            for p in paths:
                f.write(f"file '{p.resolve()}'\n")

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file), "-c", "copy", str(output),
        ], capture_output=True, check=False)
        list_file.unlink(missing_ok=True)

    def unload(self):
        """Free model memory."""
        del self._model
        self._model = None
        try:
            import torch
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except ImportError:
            pass
