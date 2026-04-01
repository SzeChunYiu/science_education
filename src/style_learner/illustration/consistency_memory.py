"""Per-episode visual memory for illustration consistency.

Tracks accepted visual elements across scenes and provides consistency
anchors for subsequent scene prompts, ensuring a coherent look within
each episode.
"""
import json
import logging
from collections import Counter
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)


class ConsistencyMemory:
    """Maintains visual consistency state for a single episode.

    Stores dominant colours, scene types, character descriptions, and key
    objects from every accepted scene illustration so that later scenes
    can reference the established look.
    """

    def __init__(self, episode_id: str) -> None:
        self.episode_id = episode_id
        self.scenes: list[dict] = []
        self._colour_counter: Counter = Counter()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(
        self,
        scene_id: int,
        image: Image.Image,
        scene_data: dict,
    ) -> None:
        """Extract and store visual features from an accepted scene.

        Args:
            scene_id: Integer scene index within the episode.
            image: The accepted PIL image.
            scene_data: Scene dict from the production plan.
        """
        colours = self._extract_colours(image)
        record = {
            "scene_id": scene_id,
            "scene_type": scene_data.get("scene_type", ""),
            "dominant_colours": colours,
            "character": scene_data.get("character", {}),
            "key_objects": self._extract_key_objects(scene_data),
        }
        self.scenes.append(record)

        for c in colours:
            self._colour_counter[c] += 1

        logger.debug(
            "ConsistencyMemory updated: episode=%s scene=%d colours=%s",
            self.episode_id,
            scene_id,
            colours,
        )

    def get_anchors(self) -> list[str]:
        """Return prompt anchor strings derived from accumulated scenes.

        Anchors nudge the diffusion model toward visual consistency with
        previously accepted illustrations.
        """
        if not self.scenes:
            return []

        anchors: list[str] = []

        # Palette anchor
        palette = self.get_palette()
        if palette:
            anchors.append(
                f"consistent warm palette using {', '.join(palette[:4])}"
            )

        # Character design anchor
        char_names = {
            s["character"].get("name")
            for s in self.scenes
            if s.get("character") and s["character"].get("name")
        }
        if char_names:
            anchors.append(
                "same character design as established: "
                + ", ".join(sorted(char_names))
            )

        # Scene-type continuity
        types_seen = {s["scene_type"] for s in self.scenes if s["scene_type"]}
        if types_seen:
            anchors.append(
                "matching illustration style from earlier scenes"
            )

        # Key-object continuity
        all_objects: list[str] = []
        for s in self.scenes:
            all_objects.extend(s.get("key_objects", []))
        obj_counter = Counter(all_objects)
        recurring = [obj for obj, count in obj_counter.items() if count >= 2]
        if recurring:
            anchors.append(
                f"recurring visual elements: {', '.join(recurring[:5])}"
            )

        return anchors

    def get_palette(self) -> list[str]:
        """Return the most common hex colours across all accepted scenes."""
        if not self._colour_counter:
            return []
        return [colour for colour, _ in self._colour_counter.most_common(6)]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Path) -> None:
        """Persist memory to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "episode_id": self.episode_id,
            "scenes": self.scenes,
            "colour_counts": dict(self._colour_counter),
        }
        path.write_text(json.dumps(data, indent=2))
        logger.info("ConsistencyMemory saved to %s", path)

    @classmethod
    def load(cls, path: Path) -> "ConsistencyMemory":
        """Reconstruct memory from a previously saved JSON file."""
        path = Path(path)
        data = json.loads(path.read_text())
        mem = cls(episode_id=data["episode_id"])
        mem.scenes = data.get("scenes", [])
        mem._colour_counter = Counter(data.get("colour_counts", {}))
        logger.info(
            "ConsistencyMemory loaded from %s (%d scenes)",
            path,
            len(mem.scenes),
        )
        return mem

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_colours(image: Image.Image, count: int = 5) -> list[str]:
        """Extract dominant hex colours from *image* using colorthief.

        Falls back to a simple histogram approach when colorthief cannot
        process the image (e.g. very small or single-colour images).
        """
        try:
            from colorthief import ColorThief
            from io import BytesIO

            buf = BytesIO()
            # colorthief expects RGB; convert if necessary
            rgb_image = image.convert("RGB")
            rgb_image.save(buf, format="PNG")
            buf.seek(0)

            ct = ColorThief(buf)
            palette = ct.get_palette(color_count=count, quality=5)
            return [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in palette]
        except Exception as exc:
            logger.warning("colorthief extraction failed: %s — using fallback", exc)
            # Fallback: quantise and take most common colours
            rgb_image = image.convert("RGB").resize((64, 64))
            quantised = rgb_image.quantize(colors=count)
            palette_flat = quantised.getpalette()
            if palette_flat is None:
                return []
            colours = []
            for i in range(min(count, len(palette_flat) // 3)):
                r, g, b = palette_flat[i * 3 : i * 3 + 3]
                colours.append(f"#{r:02x}{g:02x}{b:02x}")
            return colours

    @staticmethod
    def _extract_key_objects(scene_data: dict) -> list[str]:
        """Pull notable object names from scene metadata."""
        objects: list[str] = []

        # From visual_metaphor
        vm = scene_data.get("visual_metaphor", "")
        if vm:
            objects.append(vm)

        # From text_elements
        for te in scene_data.get("text_elements", []):
            label = te.get("label", "") or te.get("text", "")
            if label:
                objects.append(label)

        return objects
