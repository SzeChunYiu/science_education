"""MusicGen background music generator for educational videos.

Generates gentle ambient instrumental music using Meta's MusicGen model.
Falls back to silence placeholder if audiocraft is not installed.
"""
import logging
import subprocess
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class MusicGenerator:
    """Generate background music using MusicGen.

    Uses facebook/musicgen-small (~300MB) for ambient educational music.
    Generates in 30s chunks and concatenates for longer durations.

    Args:
        device: Torch device string (default "mps" for Apple Silicon).
        model_name: HuggingFace model identifier.
    """

    def __init__(
        self,
        device: str = "mps",
        model_name: str = "facebook/musicgen-small",
    ):
        self.device = device
        self.model_name = model_name
        self._model = None
        self._processor = None

    def load(self):
        """Load MusicGen model and processor."""
        try:
            from audiocraft.models import MusicGen
            self._model = MusicGen.get_pretrained(
                self.model_name, device=self.device
            )
            self._model.set_generation_params(
                use_sampling=True,
                top_k=250,
                duration=30,
            )
            logger.info(f"Loaded MusicGen ({self.model_name}) on {self.device}")
        except ImportError:
            logger.warning(
                "audiocraft not installed. Music generation will produce "
                "silence placeholders. Install with: pip install audiocraft"
            )
            self._model = None
        except Exception as e:
            logger.error(f"Failed to load MusicGen: {e}")
            self._model = None

    def generate(
        self,
        mood: str,
        duration: int = 60,
        output_path: Path = None,
    ) -> Path:
        """Generate ambient educational background music.

        Args:
            mood: Mood descriptor (e.g. "curious", "wonder", "contemplative").
            duration: Target duration in seconds.
            output_path: Where to save the audio. Auto-generated if None.

        Returns:
            Path to generated music file (.wav).
        """
        if output_path is None:
            output_path = Path(f"output/music/{mood}_{duration}s.wav")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self._model is None:
            logger.warning("MusicGen not loaded, generating silence placeholder")
            return self._generate_silence(duration, output_path)

        prompt = (
            f"gentle educational ambient music, {mood}, "
            f"instrumental, no vocals, soft"
        )

        try:
            if duration <= 30:
                return self._generate_chunk(prompt, duration, output_path)
            else:
                return self._generate_long(prompt, duration, output_path)
        except Exception as e:
            logger.error(f"MusicGen generation failed: {e}")
            return self._generate_silence(duration, output_path)

    def _generate_chunk(
        self, prompt: str, duration: int, output_path: Path
    ) -> Path:
        """Generate a single chunk up to 30s."""
        import torch
        import soundfile as sf

        self._model.set_generation_params(duration=duration)
        wav = self._model.generate([prompt])

        # wav shape: (batch, channels, samples)
        audio = wav[0].cpu().numpy()
        if audio.ndim == 2:
            audio = audio[0]  # Take first channel if stereo

        sf.write(str(output_path), audio, 32000)
        logger.info(f"Generated {duration}s music: {output_path}")
        return output_path

    def _generate_long(
        self, prompt: str, duration: int, output_path: Path
    ) -> Path:
        """Generate long music by concatenating 30s chunks with crossfade."""
        import torch
        import soundfile as sf

        chunk_dur = 30
        n_chunks = (duration + chunk_dur - 1) // chunk_dur
        chunk_paths = []

        for i in range(n_chunks):
            remaining = min(chunk_dur, duration - i * chunk_dur)
            if remaining <= 0:
                break

            chunk_path = output_path.parent / f"_chunk_{i:02d}.wav"
            self._generate_chunk(prompt, remaining, chunk_path)
            chunk_paths.append(chunk_path)

        if not chunk_paths:
            return self._generate_silence(duration, output_path)

        # Concatenate chunks with crossfade using ffmpeg
        if len(chunk_paths) == 1:
            chunk_paths[0].rename(output_path)
            return output_path

        self._crossfade_concat(chunk_paths, output_path)

        # Clean up temp chunks
        for p in chunk_paths:
            p.unlink(missing_ok=True)

        logger.info(f"Generated {duration}s music ({n_chunks} chunks): {output_path}")
        return output_path

    def _crossfade_concat(self, paths: list[Path], output: Path):
        """Concatenate audio files with 1s crossfade between chunks."""
        if len(paths) == 1:
            paths[0].rename(output)
            return

        # Build ffmpeg concat filter with crossfade
        list_file = output.parent / "_concat_music.txt"
        with open(list_file, "w") as f:
            for p in paths:
                f.write(f"file '{p.resolve()}'\n")

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file), "-c:a", "pcm_s16le",
            str(output),
        ], capture_output=True, check=False)
        list_file.unlink(missing_ok=True)

    def _generate_silence(self, duration: int, output_path: Path) -> Path:
        """Generate a silent audio file as placeholder."""
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", str(duration),
            "-c:a", "pcm_s16le",
            str(output_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=30)
            logger.info(f"Generated silence placeholder ({duration}s): {output_path}")
        except Exception as e:
            logger.error(f"Failed to generate silence: {e}")
        return output_path

    def unload(self):
        """Free model memory."""
        del self._model
        del self._processor
        self._model = None
        self._processor = None
        try:
            import torch
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                torch.mps.empty_cache()
            elif torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
        logger.info("MusicGen unloaded")
