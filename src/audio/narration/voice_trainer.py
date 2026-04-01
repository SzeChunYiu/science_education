"""F5-TTS voice trainer and inference manager."""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MODELS_DIR = Path("models/style_learner")
VOICE_DIR = MODELS_DIR / "voice"
REFERENCE_DIR = Path("data/voice_reference")


class VoiceTrainer:
    """Prepares data and manages F5-TTS fine-tuning."""

    def __init__(self, reference_dir: Path = REFERENCE_DIR):
        self.reference_dir = reference_dir
        self.reference_dir.mkdir(parents=True, exist_ok=True)

    def prepare_training_data(
        self,
        audio_files: list[Path],
        output_dir: Path = None,
        min_duration: float = 3.0,
        max_duration: float = 15.0,
    ) -> Path:
        """Prepare audio segments for F5-TTS fine-tuning.

        Splits long audio into segments, normalizes volume,
        generates metadata CSV in F5-TTS expected format.
        Returns path to prepared dataset directory.
        """
        import subprocess

        if output_dir is None:
            output_dir = self.reference_dir / "prepared"
        output_dir.mkdir(parents=True, exist_ok=True)

        metadata = []
        seg_idx = 0

        for audio_path in audio_files:
            # Get duration
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", str(audio_path)],
                capture_output=True, text=True,
            )
            try:
                info = json.loads(result.stdout)
                duration = float(info["format"]["duration"])
            except (json.JSONDecodeError, KeyError):
                logger.warning(f"Could not get duration for {audio_path}")
                continue

            # Split into segments
            n_segments = max(1, int(duration / max_duration))
            seg_duration = duration / n_segments

            for i in range(n_segments):
                start = i * seg_duration
                seg_path = output_dir / f"segment_{seg_idx:05d}.wav"

                cmd = [
                    "ffmpeg", "-y", "-i", str(audio_path),
                    "-ss", str(start), "-t", str(seg_duration),
                    "-ar", "24000", "-ac", "1",  # F5-TTS expects 24kHz mono
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    str(seg_path),
                ]
                subprocess.run(cmd, capture_output=True, check=False)

                if seg_path.exists():
                    metadata.append({
                        "audio_file": seg_path.name,
                        "text": "",  # Will be filled by Whisper transcription
                        "speaker": "narrator",
                    })
                    seg_idx += 1

        # Transcribe segments with Whisper for text alignment
        try:
            self._transcribe_segments(output_dir, metadata)
        except ImportError:
            logger.warning("Whisper not available, skipping transcription")

        # Save metadata
        meta_path = output_dir / "metadata.csv"
        with open(meta_path, "w") as f:
            f.write("audio_file|text|speaker\n")
            for m in metadata:
                if m["text"]:  # Only include transcribed segments
                    f.write(f"{m['audio_file']}|{m['text']}|{m['speaker']}\n")

        logger.info(f"Prepared {len(metadata)} segments in {output_dir}")
        return output_dir

    def _transcribe_segments(self, audio_dir: Path, metadata: list[dict]):
        """Transcribe audio segments using Whisper."""
        import whisper
        model = whisper.load_model("base")

        for m in metadata:
            audio_path = audio_dir / m["audio_file"]
            if audio_path.exists():
                result = model.transcribe(str(audio_path))
                m["text"] = result["text"].strip()

    @staticmethod
    def get_finetune_command(
        dataset_dir: Path,
        output_dir: Path = VOICE_DIR,
        epochs: int = 100,
        batch_size: int = 4,
        learning_rate: float = 1e-5,
    ) -> str:
        """Return the F5-TTS fine-tuning command for SLURM scripts."""
        return (
            f"f5-tts_finetune "
            f"--dataset_dir {dataset_dir} "
            f"--output_dir {output_dir} "
            f"--epochs {epochs} "
            f"--batch_size {batch_size} "
            f"--learning_rate {learning_rate} "
            f"--save_every 20"
        )


class VoiceReference:
    """Manages reference voice clips for zero-shot TTS."""

    def __init__(self, reference_dir: Path = REFERENCE_DIR):
        self.reference_dir = reference_dir

    def get_reference_clip(self, style: str = "default") -> Path | None:
        """Get a reference audio clip for voice cloning."""
        clip_path = self.reference_dir / f"reference_{style}.wav"
        if clip_path.exists():
            return clip_path
        # Fallback to any available reference
        wavs = list(self.reference_dir.glob("reference_*.wav"))
        return wavs[0] if wavs else None

    def create_reference_from_episode(
        self,
        narration_path: Path,
        output_style: str = "default",
        duration: float = 10.0,
    ) -> Path:
        """Extract a reference clip from an existing narration."""
        import subprocess

        output_path = self.reference_dir / f"reference_{output_style}.wav"
        cmd = [
            "ffmpeg", "-y", "-i", str(narration_path),
            "-t", str(duration),
            "-ar", "24000", "-ac", "1",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path
