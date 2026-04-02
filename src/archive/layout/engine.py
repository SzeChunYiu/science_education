"""
Layout engine — positions, validates, and de-collides LayoutElement objects.

The engine is deterministic: given the same list of LayoutElement inputs,
it always produces the same resolved positions.

Usage:
    engine = LayoutEngine(aspect="16:9")
    resolved = engine.place(elements)
    report = engine.validate(resolved)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .constants import (
    ASPECT_TO_CANVAS,
    GRID_COLS,
    GRID_ROWS,
    MAX_OVERLAP_ITERATIONS,
    OVERLAP_PUSH_FACTOR,
    SAFE_BOTTOM,
    SAFE_LEFT,
    SAFE_RIGHT,
    SAFE_TOP,
    SUBTITLE_ROLES,
    Z_ORDER,
    Z_ORDER_DEFAULT,
    ZONES,
)
from .element import LayoutElement


# ---------------------------------------------------------------------------
# Validation report
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    """Result of a single validation check."""
    name: str
    passed: bool
    detail: str = ""

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        suffix = f" — {self.detail}" if self.detail else ""
        return f"[{status}] {self.name}{suffix}"


@dataclass
class ValidationReport:
    """Aggregated validation report for a fully placed frame."""
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append(CheckResult(name, passed, detail))

    def __str__(self) -> str:
        lines = ["ValidationReport:"]
        for c in self.checks:
            lines.append(f"  {c}")
        status = "ALL PASSED" if self.passed else "HAS FAILURES"
        lines.append(f"  => {status}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# LayoutEngine
# ---------------------------------------------------------------------------

class LayoutEngine:
    """
    Computes pixel-accurate positions for all scene elements.

    The engine operates on a 12×8 content grid that sits within the canvas
    safe area.  Each element is assigned to its semantic zone (from the
    ZONES mapping), scaled to fit, and centred.  After initial placement,
    a constraint-satisfaction loop resolves any remaining overlaps without
    ever pushing elements into the subtitle zone.

    Args:
        aspect: "16:9" (default) or "9:16"
    """

    def __init__(self, aspect: str = "16:9") -> None:
        if aspect not in ASPECT_TO_CANVAS:
            raise ValueError(
                f"Unknown aspect ratio {aspect!r}. "
                f"Valid options: {list(ASPECT_TO_CANVAS.keys())}"
            )
        self.aspect = aspect
        self.canvas_w, self.canvas_h = ASPECT_TO_CANVAS[aspect]

        # Pixel boundaries of the full safe area (content + subtitle zone together)
        self._safe_x1 = int(self.canvas_w * SAFE_LEFT)
        self._safe_y1 = int(self.canvas_h * SAFE_TOP)
        self._safe_x2 = int(self.canvas_w * (1.0 - SAFE_RIGHT))
        self._safe_y2 = int(self.canvas_h * (1.0 - SAFE_BOTTOM))

        # Pixel boundary of the subtitle zone top edge
        self._subtitle_y = int(self.canvas_h * (1.0 - SAFE_BOTTOM))

        # Total content area dimensions (used for grid cell sizing)
        self._content_w = self._safe_x2 - self._safe_x1
        self._content_h = self._safe_y2 - self._safe_y1

        # Grid cell size in pixels
        self._cell_w = self._content_w / GRID_COLS
        self._cell_h = self._content_h / GRID_ROWS

        # The subtitle zone itself spans the full canvas width at the bottom
        self._subtitle_zone_rect = (
            0,
            self._subtitle_y,
            self.canvas_w,
            self.canvas_h,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def place(self, elements: List[LayoutElement]) -> List[LayoutElement]:
        """
        Main entry point.  Assign positions to all elements and resolve
        any overlaps.

        Steps:
          1. Assign z-order from Z_ORDER constants
          2. Convert each element's zone to pixel rect
          3. Scale and centre element within its zone
          4. Enforce hard subtitle zone constraint
          5. Resolve remaining overlaps iteratively
          6. Return elements sorted by z-order

        Args:
            elements: list of LayoutElement with role, asset_path/text, scale set

        Returns:
            The same list (mutated in place) with x, y, w, h, bbox resolved,
            sorted ascending by z-order for compositor use.
        """
        for el in elements:
            # Assign Z
            el.z = Z_ORDER.get(el.role, Z_ORDER_DEFAULT)

            if el.role not in ZONES:
                raise ValueError(
                    f"Unknown role {el.role!r} — must be one of: {sorted(ZONES.keys())}"
                )

            zone_px = self._zone_to_pixels(el.role)
            self._fit_element_to_zone(el, zone_px)

        # Hard constraint: no non-subtitle content in subtitle zone
        violations = self._check_safe_zones(elements)
        if violations:
            raise LayoutConstraintError(
                "Subtitle zone violation(s) detected after initial placement:\n"
                + "\n".join(f"  • {v}" for v in violations)
            )

        # Iterative overlap resolution
        elements = self._resolve_overlaps(elements)

        # Sort by z-order so compositor can render in the right order
        elements.sort(key=lambda e: e.z)
        return elements

    def _zone_to_pixels(self, zone_key: str) -> Tuple[int, int, int, int]:
        """
        Convert a named zone (from ZONES) to a pixel rectangle.

        For the "subtitle" role, the zone maps into the subtitle-reserved band
        at the bottom of the canvas.  All other zones map into the content area.

        Returns:
            (x, y, x2, y2) pixel rectangle (x2 and y2 are exclusive)
        """
        col_start, col_end, row_start, row_end = ZONES[zone_key]

        if zone_key in SUBTITLE_ROLES:
            # Subtitle band: full width, bottom SAFE_BOTTOM fraction
            sub_h = self.canvas_h - self._subtitle_y
            sub_cell_h = sub_h / 1  # subtitle band is treated as 1 row
            x  = 0
            x2 = self.canvas_w
            y  = self._subtitle_y
            y2 = self.canvas_h
        else:
            x  = int(self._safe_x1 + col_start * self._cell_w)
            x2 = int(self._safe_x1 + col_end   * self._cell_w)
            y  = int(self._safe_y1 + row_start  * self._cell_h)
            y2 = int(self._safe_y1 + row_end    * self._cell_h)

        return (x, y, x2, y2)

    def _fit_element_to_zone(
        self,
        element: LayoutElement,
        zone_px: Tuple[int, int, int, int],
    ) -> LayoutElement:
        """
        Scale the element to fit within the zone and centre it.

        The element's intrinsic size is determined from:
          - image assets: their natural pixel dimensions
          - text elements: an estimated bbox based on font_size and text length

        After scaling (respecting the element's scale factor and zone padding),
        the element is centred within the zone.

        The element is mutated in place and returned.
        """
        zx, zy, zx2, zy2 = zone_px
        zone_w = zx2 - zx
        zone_h = zy2 - zy
        padded_w = max(1, zone_w - 2 * element.padding)
        padded_h = max(1, zone_h - 2 * element.padding)

        # --- determine intrinsic size ---
        if element.asset_path is not None:
            try:
                from PIL import Image as _Image
                with _Image.open(element.asset_path) as img:
                    intrinsic_w, intrinsic_h = img.size
            except Exception:
                # Fallback: treat as square
                intrinsic_w = intrinsic_h = min(padded_w, padded_h)
        else:
            # Estimate text bounding box
            intrinsic_w, intrinsic_h = _estimate_text_size(
                element.text, element.font_size
            )

        # --- compute scale factor to fit within padded zone ---
        if intrinsic_w == 0 or intrinsic_h == 0:
            scale_fit = 1.0
        else:
            scale_fit = min(padded_w / intrinsic_w, padded_h / intrinsic_h)

        # Apply user-supplied scale (capped at 1.0 relative to zone fit)
        effective_scale = min(element.scale, 1.0) * scale_fit

        element.w = max(1, int(intrinsic_w * effective_scale))
        element.h = max(1, int(intrinsic_h * effective_scale))

        # Centre within zone
        element.x = zx + (zone_w - element.w) // 2
        element.y = zy + (zone_h - element.h) // 2

        element.update_bbox()
        return element

    def _check_safe_zones(
        self, elements: List[LayoutElement]
    ) -> List[str]:
        """
        Check that no non-subtitle element overlaps the subtitle zone.

        Returns:
            List of human-readable violation strings.  Empty = all OK.
        """
        violations = []
        for el in elements:
            if el.role in SUBTITLE_ROLES:
                continue
            if el.bbox is None:
                continue
            _, _, _, y2 = el.bbox
            if y2 > self._subtitle_y:
                overlap_px = y2 - self._subtitle_y
                violations.append(
                    f"role={el.role!r} extends {overlap_px}px into subtitle zone "
                    f"(bbox={el.bbox}, subtitle_y={self._subtitle_y})"
                )
        return violations

    def _resolve_overlaps(
        self,
        elements: List[LayoutElement],
        max_iterations: int = MAX_OVERLAP_ITERATIONS,
    ) -> List[LayoutElement]:
        """
        Iteratively push overlapping elements apart.

        Algorithm (per iteration):
          1. Find all pairs (i, j) where bboxes intersect
          2. Compute intersection centroid
          3. Push each element's centre away from the centroid, proportional
             to the overlap area
          4. Re-clamp both elements to the safe content area (or subtitle zone
             for subtitle elements)
          5. Repeat until no overlaps remain or max_iterations is reached
          6. If overlaps remain: scale down the lower-priority (lower-z) element

        The subtitle zone boundary is treated as a hard floor — elements above
        the subtitle zone cannot be pushed below it.
        """
        for iteration in range(max_iterations):
            pairs = self._find_overlapping_pairs(elements)
            if not pairs:
                break

            for i, j in pairs:
                a = elements[i]
                b = elements[j]

                oa = self._overlap_area(a.bbox, b.bbox)
                if oa <= 0:
                    continue

                # Intersection rectangle
                ix1 = max(a.bbox[0], b.bbox[0])
                iy1 = max(a.bbox[1], b.bbox[1])
                ix2 = min(a.bbox[2], b.bbox[2])
                iy2 = min(a.bbox[3], b.bbox[3])

                cx = (ix1 + ix2) / 2.0
                cy = (iy1 + iy2) / 2.0

                # Vector from centroid to each element's centre
                acx = a.x + a.w / 2.0
                acy = a.y + a.h / 2.0
                bcx = b.x + b.w / 2.0
                bcy = b.y + b.h / 2.0

                # Push magnitude proportional to overlap
                push_w = (ix2 - ix1) * OVERLAP_PUSH_FACTOR
                push_h = (iy2 - iy1) * OVERLAP_PUSH_FACTOR

                def _push(ex: float, ey: float, centroid_x: float, centroid_y: float):
                    dx = ex - centroid_x
                    dy = ey - centroid_y
                    dist = math.hypot(dx, dy)
                    if dist < 1e-6:
                        # Elements are exactly coincident — push in a default direction
                        return push_w, 0.0
                    nx = dx / dist
                    ny = dy / dist
                    return nx * push_w, ny * push_h

                adx, ady = _push(acx, acy, cx, cy)
                bdx, bdy = _push(bcx, bcy, cx, cy)

                # Apply push
                a.x = int(a.x + adx)
                a.y = int(a.y + ady)
                b.x = int(b.x + bdx)
                b.y = int(b.y + bdy)

                # Re-clamp to safe area
                self._clamp_to_safe_area(a)
                self._clamp_to_safe_area(b)

                a.update_bbox()
                b.update_bbox()

        # Final pass: if still overlapping, scale down the lower-z element
        remaining_pairs = self._find_overlapping_pairs(elements)
        for i, j in remaining_pairs:
            a = elements[i]
            b = elements[j]
            # Scale down the lower-priority element
            lower = a if a.z <= b.z else b
            higher = b if a.z <= b.z else a
            if lower.scale > 0.1:
                lower.scale = max(0.1, lower.scale * 0.7)
                zone_px = self._zone_to_pixels(lower.role)
                self._fit_element_to_zone(lower, zone_px)
                self._clamp_to_safe_area(lower)
                lower.update_bbox()

        return elements

    def _find_overlapping_pairs(
        self, elements: List[LayoutElement]
    ) -> List[Tuple[int, int]]:
        """
        Return all (i, j) index pairs where elements[i] and elements[j] overlap.
        Ignores pairs involving background elements.
        """
        pairs = []
        n = len(elements)
        for i in range(n):
            for j in range(i + 1, n):
                a = elements[i]
                b = elements[j]
                if a.role == "background" or b.role == "background":
                    continue
                if a.bbox and b.bbox and self._overlap_area(a.bbox, b.bbox) > 0:
                    pairs.append((i, j))
        return pairs

    def _overlap_area(
        self,
        bbox1: Tuple[int, int, int, int],
        bbox2: Tuple[int, int, int, int],
    ) -> float:
        """
        Compute the pixel area of the intersection of two bounding boxes.

        Args:
            bbox1, bbox2: (x, y, x2, y2) bounding rectangles

        Returns:
            Area in pixels (0 if no intersection)
        """
        ix1 = max(bbox1[0], bbox2[0])
        iy1 = max(bbox1[1], bbox2[1])
        ix2 = min(bbox1[2], bbox2[2])
        iy2 = min(bbox1[3], bbox2[3])
        if ix2 <= ix1 or iy2 <= iy1:
            return 0.0
        return float((ix2 - ix1) * (iy2 - iy1))

    def _clamp_to_safe_area(self, element: LayoutElement) -> None:
        """
        Clamp an element so it stays within its permitted canvas region.

        - Subtitle elements: clamped within the subtitle band
        - All other elements: clamped within the content-safe area (above subtitle zone)
        """
        if element.role in SUBTITLE_ROLES:
            min_x = 0
            max_x = self.canvas_w - element.w
            min_y = self._subtitle_y
            max_y = self.canvas_h - element.h
        else:
            min_x = self._safe_x1
            max_x = self._safe_x2 - element.w
            min_y = self._safe_y1
            max_y = self._subtitle_y - element.h  # hard floor above subtitle zone

        element.x = max(min_x, min(element.x, max(min_x, max_x)))
        element.y = max(min_y, min(element.y, max(min_y, max_y)))

    def validate(self, elements: List[LayoutElement]) -> ValidationReport:
        """
        Run all layout validation checks and return a structured report.

        Checks performed:
          1. All elements have resolved bbox
          2. No non-subtitle elements in subtitle zone
          3. All elements within canvas bounds
          4. No overlapping pairs remain
          5. Correct z-order assignment
        """
        report = ValidationReport()

        # 1. Bbox resolved
        unresolved = [e.role for e in elements if e.bbox is None]
        report.add(
            "all_bboxes_resolved",
            len(unresolved) == 0,
            f"Unresolved: {unresolved}" if unresolved else "",
        )

        # 2. Subtitle zone violations
        violations = self._check_safe_zones(elements)
        report.add(
            "subtitle_zone_clear",
            len(violations) == 0,
            "; ".join(violations) if violations else "",
        )

        # 3. Within canvas bounds
        out_of_bounds = []
        for el in elements:
            if el.bbox is None:
                continue
            x, y, x2, y2 = el.bbox
            if x < 0 or y < 0 or x2 > self.canvas_w or y2 > self.canvas_h:
                out_of_bounds.append(
                    f"{el.role}: bbox={el.bbox} exceeds canvas ({self.canvas_w}×{self.canvas_h})"
                )
        report.add(
            "all_within_canvas",
            len(out_of_bounds) == 0,
            "; ".join(out_of_bounds) if out_of_bounds else "",
        )

        # 4. No overlaps
        pairs = self._find_overlapping_pairs(elements)
        overlap_descs = []
        for i, j in pairs:
            a, b = elements[i], elements[j]
            area = self._overlap_area(a.bbox, b.bbox)
            overlap_descs.append(f"{a.role} ∩ {b.role} = {area:.0f}px²")
        report.add(
            "no_overlaps",
            len(pairs) == 0,
            "; ".join(overlap_descs) if overlap_descs else "",
        )

        # 5. Z-order assigned
        missing_z = [e.role for e in elements if not hasattr(e, "z")]
        report.add(
            "z_order_assigned",
            len(missing_z) == 0,
            f"Missing z: {missing_z}" if missing_z else "",
        )

        return report


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class LayoutConstraintError(Exception):
    """Raised when a hard layout constraint is violated (e.g. subtitle zone)."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _estimate_text_size(text: str, font_size: int) -> Tuple[int, int]:
    """
    Estimate the pixel dimensions of a rendered text string.

    This is a heuristic used when no font metrics are available at placement
    time.  The compositor uses actual PIL text rendering, so this only needs
    to be approximately correct for zone-fitting purposes.

    Returns:
        (estimated_width, estimated_height) in pixels
    """
    if not text:
        return (font_size * 4, font_size)
    # Empirical: average character is ~0.55× font_size wide, height ~1.3× font_size
    char_width = font_size * 0.55
    line_height = font_size * 1.3
    lines = text.split("\n")
    max_line_len = max(len(line) for line in lines)
    estimated_w = int(max_line_len * char_width)
    estimated_h = int(len(lines) * line_height)
    return (estimated_w, estimated_h)
