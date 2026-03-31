# Asset registry — single source of truth for asset lookup
# Replaces hardcoded dicts in episode_renderer.py

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class AssetRegistry:
    """
    Lightweight registry that scans the data/assets/physics/ directory tree
    and provides keyword-based lookup for character, background, and object assets.

    Usage
    -----
    registry = AssetRegistry()
    registry.find("newton")                          # best match any type
    registry.find("newton", asset_type="character")  # character only
    registry.find("grass_field", asset_type="background")
    registry.find("pendulum", asset_type="object")
    """

    # Sub-directory → asset_type label
    _SUBDIR_TYPE: dict[str, str] = {
        "characters": "character",
        "backgrounds": "background",
        "objects": "object",
        "elements": "element",
    }

    def __init__(self, assets_root: Optional[str] = None) -> None:
        if assets_root is None:
            # Resolve relative to this file: src/asset_registry.py → project root → data/assets/physics
            assets_root = str(Path(__file__).resolve().parents[1] / "data" / "assets" / "physics")
        self._root = Path(assets_root)
        # Map: (stem_keywords, asset_type) → absolute path
        self._index: list[tuple[str, str, Path]] = []
        self._scan()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _scan(self) -> None:
        """Walk the assets root and index every PNG file."""
        if not self._root.is_dir():
            return
        for png in self._root.rglob("*.png"):
            # Determine asset type from parent directory chain
            rel_parts = png.relative_to(self._root).parts
            asset_type = "unknown"
            for part in rel_parts[:-1]:  # exclude the filename itself
                if part in self._SUBDIR_TYPE:
                    asset_type = self._SUBDIR_TYPE[part]
                    break
            # Build a searchable key from the filename stem
            stem = png.stem.lower()
            # Strip common prefixes used in this project
            for prefix in ("char_", "bg_", "obj_", "element_"):
                if stem.startswith(prefix):
                    stem = stem[len(prefix):]
                    break
            self._index.append((stem, asset_type, png))

    def _keywords_for(self, stem: str) -> list[str]:
        """Split a stem like 'ancient_greek_courtyard' into searchable tokens."""
        return [part for part in stem.replace("-", "_").split("_") if part]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find(self, query: str, asset_type: Optional[str] = None) -> Optional[str]:
        """
        Return the absolute path of the best matching asset, or None.

        Parameters
        ----------
        query : str
            Keyword(s) to search for (e.g. "newton", "grass field", "pendulum").
        asset_type : str, optional
            Restrict results to "character", "background", "object", or "element".
        """
        if not query:
            return None
        query_lower = query.lower().replace(" ", "_").replace("-", "_")
        query_tokens = [t for t in query_lower.replace("_", " ").split() if t]

        best_path: Optional[Path] = None
        best_score = 0

        for stem, atype, path in self._index:
            if asset_type and atype != asset_type:
                continue
            # Exact stem match wins immediately
            if query_lower == stem or query_lower in stem:
                return str(path)
            # Token overlap scoring
            stem_tokens = self._keywords_for(stem)
            score = sum(1 for qt in query_tokens if any(qt in st or st in qt for st in stem_tokens))
            if score > best_score:
                best_score = score
                best_path = path

        if best_score > 0 and best_path is not None:
            return str(best_path)
        return None

    def all_of_type(self, asset_type: str) -> list[str]:
        """Return sorted list of all absolute paths for the given asset_type."""
        return sorted(str(p) for _, atype, p in self._index if atype == asset_type)

    def __repr__(self) -> str:
        return f"AssetRegistry(root={self._root!r}, entries={len(self._index)})"


# Module-level singleton — importers can use this directly
_registry: Optional[AssetRegistry] = None


def get_registry() -> AssetRegistry:
    """Return the module-level singleton registry, creating it on first call."""
    global _registry
    if _registry is None:
        _registry = AssetRegistry()
    return _registry
