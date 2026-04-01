"""Lightweight Kokoro TTS for instant local previews via mlx-audio.

Designed for quick iteration during script writing -- sub-0.3s generation
on Apple Silicon with ~2GB memory footprint.
"""
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Available Kokoro voice presets
AVAILABLE_VOICES = ["af_heart", "af_bella", "am_adam", "am_michael"]


class KokoroPreview:
    """Generate quick narration previews using Kokoro TTS.

    Tries mlx-audio/kokoro first (fastest on Apple Silicon),
    falls back to edge-tts if unavailable.

    Args:
        voice: Kokoro voice preset. One of af_heart, af_bella,
               am_adam, am_michael.
    """

    def __init__(self, voice: str = "af_heart"):
        if voice not in AVAILABLE_VOICES:
            logger.warning(
                f"Voice '{voice}' not in {AVAILABLE_VOICES}, "
                f"defaulting to 'af_heart'"
            )
            voice = "af_heart"
        self.voice = voice
        self._tts = None

    def _load_kokoro(self):
        """Attempt to load Kokoro via mlx-audio."""
        try:
            from mlx_audio.tts import KokoroTTS
            self._tts = KokoroTTS()
            logger.info(f"Loaded Kokoro TTS (voice={self.voice})")
            return True
        except ImportError:
            logger.info("mlx-audio not installed, will use edge-tts fallback")
            return False
        except Exception as e:
            logger.warning(f"Kokoro load failed: {e}, will use edge-tts fallback")
            return False

    def generate(self, text: str, output_path: Path) -> Path:
        """Generate a quick preview audio clip.

        Args:
            text: Text to speak.
            output_path: Where to save the audio file (.wav or .mp3).

        Returns:
            Path to generated audio file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Try Kokoro first
        if self._tts is not None or self._load_kokoro():
            try:
                audio = self._tts.generate(
                    text=text,
                    voice=self.voice,
                )
                # Save via soundfile
                import soundfile as sf
                sf.write(str(output_path), audio, 24000)
                logger.info(f"Preview generated (Kokoro): {output_path}")
                return output_path
            except Exception as e:
                logger.warning(f"Kokoro generation failed: {e}")

        # Fallback to edge-tts
        return self._generate_edge_tts(text, output_path)

    def _generate_edge_tts(self, text: str, output_path: Path) -> Path:
        """Fallback preview using edge-tts (free Microsoft TTS)."""
        mp3_path = output_path.with_suffix(".mp3")
        cmd = [
            "edge-tts",
            "--voice", "en-US-GuyNeural",
            "--rate", "+5%",
            "--text", text,
            "--write-media", str(mp3_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=30)
            # Convert to wav if requested
            if output_path.suffix == ".wav":
                subprocess.run([
                    "ffmpeg", "-y", "-i", str(mp3_path),
                    "-ar", "24000", "-ac", "1", str(output_path),
                ], capture_output=True, check=True)
                mp3_path.unlink(missing_ok=True)
            else:
                output_path = mp3_path
            logger.info(f"Preview generated (edge-tts fallback): {output_path}")
        except FileNotFoundError:
            logger.error("edge-tts not found. Install with: pip install edge-tts")
        except Exception as e:
            logger.error(f"edge-tts preview failed: {e}")
        return output_path
