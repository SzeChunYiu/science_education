"""
script_parser.py — Converts episode markdown scripts into structured ParsedScript objects.

The parser handles the "YouTube long-form" markdown format produced by the content
writing stage.  A script consists of:

  - A top-level title line:  # Episode N — ...
  - A ## Title: "..." metadata line
  - One or more segments, each introduced by a ## heading that contains a timestamp
    in the form (MM:SS - MM:SS) or (MM:SS – MM:SS)  (en-dash variant)
  - Within each segment:
    - Narrator lines: plain text, optionally prefixed by a tone tag such as
      [normal], [with energy], [slower], [pause], [with intensity], [with reverence], etc.
    - Visual cue lines: [Visual: ...]  (may span multiple lines if continuation
      lines appear before the next structural element)
    - Emphasis: **bold text** marks equations or key terms
    - Block-quotes (>) may contain inline equations

Design decisions
----------------
* The parser is deliberately lenient.  If a timestamp is missing or malformed
  the segment still appears in the output with start_time=end_time=None.
* Bold items are split into "equations" (contain =, math operators, or known
  math keywords) and "key_terms" (everything else).
* Multi-line Visual blocks are joined with a space.
* The description section at the bottom of each script (after "## Description")
  is intentionally skipped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Compiled regular expressions
# ---------------------------------------------------------------------------

# Segment heading: ## Some Title (MM:SS - MM:SS) or (MM:SS – MM:SS)
_RE_SEGMENT_HEADING = re.compile(
    r"^#{1,3}\s+(?P<title>.+?)"               # heading text (greedy, but stops at optional timestamp)
    r"(?:\s+\((?P<start>\d+:\d+)\s*[–-]\s*(?P<end>\d+:\d+)\))?"  # optional (MM:SS - MM:SS)
    r"\s*$"
)

# Visual cue opening: [Visual: ...]
_RE_VISUAL_START = re.compile(r"^\[Visual:\s*(?P<content>.*)$", re.IGNORECASE)
# A line that is entirely a closing bracket (marks end of multi-line visual)
_RE_CLOSING_BRACKET = re.compile(r"^\s*\]\s*$")

# Narrator tone prefix: [word], [words with spaces] at start of line
_RE_TONE_TAG = re.compile(r"^\[(?P<tone>[a-zA-Z ]+)\]\s*")

# Bold emphasis: **...**
_RE_BOLD = re.compile(r"\*\*(.+?)\*\*")

# Inline / block-quote equation detection: contains =, common math ops, or keywords
_RE_EQUATION_HINT = re.compile(
    r"[=+\-×÷/^√∫∑∏∂Δδ]|"
    r"\b(?:mv|kg|m/s|dp|dt|F\s*=|p\s*=|v\s*=|KE|PE|vis viva|v²|v\^2)\b",
    re.IGNORECASE,
)

# Block-quote equation lines: > equation
_RE_BLOCKQUOTE = re.compile(r"^>\s*(?P<content>.+)$")

# Bare inline equation: line containing something like "p = mv" without bold
_RE_BARE_EQUATION_LINE = re.compile(
    r"^[A-Za-z_][A-Za-z_0-9]*\s*=\s*[^\n]+"
)

# Timestamp MM:SS → float (seconds)
def _ts_to_seconds(ts: str) -> float:
    """Convert 'MM:SS' timestamp string to total seconds as a float."""
    parts = ts.strip().split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    raise ValueError(f"Cannot parse timestamp: {ts!r}")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ScriptSegment:
    """
    One time-stamped section of a script, e.g. "Part 2: Every Symbol Explained".

    Attributes
    ----------
    title : str
        The heading text, stripped of leading ##/### markers.
    start_time : float or None
        Start time in seconds.  None if the heading contained no timestamp.
    end_time : float or None
        End time in seconds.  None if the heading contained no timestamp.
    duration : float
        end_time - start_time, or 0.0 when timestamps are absent.
    narrator_lines : list[str]
        All spoken narrator lines, tone prefixes stripped.
    visual_cues : list[str]
        Contents of every [Visual: ...] block, with multi-line values joined.
    equations : list[str]
        Bold **...** items and bare equation lines that look like equations.
    key_terms : list[str]
        Bold **...** items that do not look like equations (concepts, names).
    tone_tags : list[str]
        All unique tone tags found in this segment, e.g. ['normal', 'with energy'].
    """

    title: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: float = 0.0
    narrator_lines: list[str] = field(default_factory=list)
    visual_cues: list[str] = field(default_factory=list)
    equations: list[str] = field(default_factory=list)
    key_terms: list[str] = field(default_factory=list)
    tone_tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.start_time is not None and self.end_time is not None:
            self.duration = self.end_time - self.start_time


@dataclass
class ParsedScript:
    """
    Fully parsed representation of a YouTube long-form episode script.

    Attributes
    ----------
    episode_id : str
        Derived from the filename stem, e.g. 'ep04_youtube_long'.
    title : str
        The episode title extracted from the ## Title: "..." line.
    series_subtitle : str
        Series name / subtitle line, e.g. "Newton's Laws: The Story Behind the Equations"
    total_duration : float
        Sum of all segment durations in seconds.
    segments : list[ScriptSegment]
        All parsed segments in order.  The description section is excluded.
    """

    episode_id: str
    title: str
    series_subtitle: str = ""
    total_duration: float = 0.0
    segments: list[ScriptSegment] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.total_duration = sum(s.duration for s in self.segments)


# ---------------------------------------------------------------------------
# Internal parsing helpers
# ---------------------------------------------------------------------------

def _is_equation(text: str) -> bool:
    """Return True if *text* looks like a math equation rather than a plain term."""
    return bool(_RE_EQUATION_HINT.search(text))


def _extract_bold_items(text: str) -> tuple[list[str], list[str]]:
    """
    Extract **bold** items from *text* and split them into equations and key_terms.

    Returns
    -------
    equations : list[str]
    key_terms : list[str]
    """
    equations: list[str] = []
    key_terms: list[str] = []
    for match in _RE_BOLD.finditer(text):
        item = match.group(1).strip()
        if _is_equation(item):
            equations.append(item)
        else:
            key_terms.append(item)
    return equations, key_terms


def _parse_segment_lines(lines: list[str]) -> ScriptSegment:
    """
    Parse the heading line (lines[0]) and body lines (lines[1:]) of one segment
    into a ScriptSegment.
    """
    # --- Parse heading ---
    heading = lines[0] if lines else ""
    m = _RE_SEGMENT_HEADING.match(heading)
    if m:
        title = m.group("title").strip().lstrip("#").strip()
        start_raw = m.group("start")
        end_raw = m.group("end")
        try:
            start_time = _ts_to_seconds(start_raw) if start_raw else None
            end_time = _ts_to_seconds(end_raw) if end_raw else None
        except ValueError:
            start_time = end_time = None
    else:
        title = heading.lstrip("#").strip()
        start_time = end_time = None

    seg = ScriptSegment(title=title, start_time=start_time, end_time=end_time)

    # --- Parse body ---
    tone_tags_seen: list[str] = []
    i = 0
    body_lines = lines[1:]

    while i < len(body_lines):
        raw = body_lines[i]
        stripped = raw.strip()

        # Skip blank lines, horizontal rules, and the --- separator
        if not stripped or stripped == "---":
            i += 1
            continue

        # ---- Visual cue start: [Visual: ...]  ----
        vm = _RE_VISUAL_START.match(stripped)
        if vm:
            cue_parts = [vm.group("content").rstrip("]").strip()]
            # Check if the cue continues on the next lines (not yet closed)
            if not stripped.rstrip().endswith("]"):
                i += 1
                while i < len(body_lines):
                    next_line = body_lines[i].strip()
                    if not next_line:
                        # Blank line ends multi-line visual
                        break
                    if _RE_CLOSING_BRACKET.match(next_line):
                        i += 1
                        break
                    # Another [Visual: or heading means the previous visual ended
                    if _RE_VISUAL_START.match(next_line) or next_line.startswith("#"):
                        break
                    cue_parts.append(next_line.rstrip("]").strip())
                    i += 1
            cue = " ".join(p for p in cue_parts if p)
            if cue:
                seg.visual_cues.append(cue)
            i += 1
            continue

        # ---- Tone / pacing tag only line: [pause], [slower], etc. ----
        tone_match = _RE_TONE_TAG.match(stripped)
        if tone_match:
            tone = tone_match.group("tone").strip().lower()
            remaining = stripped[tone_match.end():].strip()
            if tone not in tone_tags_seen:
                tone_tags_seen.append(tone)
            if remaining:
                # There's spoken content after the tag
                eq, kt = _extract_bold_items(remaining)
                seg.equations.extend(eq)
                seg.key_terms.extend(kt)
                seg.narrator_lines.append(remaining)
            i += 1
            continue

        # ---- Block-quote lines: > Q = mv ----
        bqm = _RE_BLOCKQUOTE.match(stripped)
        if bqm:
            content = bqm.group("content").strip()
            if _is_equation(content):
                if content not in seg.equations:
                    seg.equations.append(content)
            else:
                seg.narrator_lines.append(content)
            i += 1
            continue

        # ---- Skip metadata-style lines (** Title: ** pattern at top) ----
        if stripped.startswith("**") and stripped.endswith("**") and ":" in stripped:
            i += 1
            continue

        # ---- General content line ----
        # Check for bold items
        eq, kt = _extract_bold_items(stripped)
        seg.equations.extend(eq)
        seg.key_terms.extend(kt)

        # Bare equation lines (e.g. "p = mv = 1 × 5 = 5 kg⋅m/s")
        if _RE_BARE_EQUATION_LINE.match(stripped) and _is_equation(stripped):
            # Store as narrator line too — it's read aloud as math
            seg.narrator_lines.append(stripped)
            i += 1
            continue

        # Regular narrator / body text (strip italic markers but keep text)
        cleaned = re.sub(r"\*+", "", stripped)          # remove bold/italic markers
        cleaned = re.sub(r"^#+\s*", "", cleaned)        # remove any stray # prefixes
        cleaned = cleaned.strip()
        if cleaned:
            seg.narrator_lines.append(cleaned)

        i += 1

    # Deduplicate while preserving order
    seg.equations = _dedup(seg.equations)
    seg.key_terms = _dedup(seg.key_terms)
    seg.tone_tags = tone_tags_seen

    return seg


def _dedup(lst: list[str]) -> list[str]:
    """Return *lst* with duplicates removed, preserving first-occurrence order."""
    seen: set[str] = set()
    out: list[str] = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_script(script_path: str) -> ParsedScript:
    """
    Parse a YouTube long-form markdown script into a :class:`ParsedScript`.

    Parameters
    ----------
    script_path : str
        Absolute or relative path to the markdown file.

    Returns
    -------
    ParsedScript
        Structured representation with all segments, visual cues, equations,
        key terms, and narrator lines extracted.

    Notes
    -----
    * The function never raises on a well-formed (or moderately malformed) script
      — missing timestamps result in None values rather than exceptions.
    * The trailing "## Description" section is stripped before parsing.
    """
    path = Path(script_path)
    raw_text = path.read_text(encoding="utf-8")

    # --- Strip description section ---
    desc_idx = re.search(r"^##\s+Description\s*$", raw_text, re.MULTILINE)
    if desc_idx:
        raw_text = raw_text[: desc_idx.start()]

    lines = raw_text.splitlines()

    # --- Extract top-level metadata ---
    episode_id = path.stem  # e.g. "ep04_youtube_long"
    title = ""
    series_subtitle = ""

    for line in lines[:10]:
        stripped = line.strip()
        # ## Title: "..."
        m = re.match(r"^##\s+Title:\s*[\"\u201c]?(.+?)[\"\u201d]?\s*$", stripped)
        if m:
            title = m.group(1).strip().strip('"').strip("\u201c\u201d")
        # ## Subtitle: ...
        m2 = re.match(r"^##\s+Subtitle:\s*(.+)$", stripped)
        if m2:
            series_subtitle = m2.group(1).strip()
        # # Episode N — fallback title
        if not title:
            m3 = re.match(r"^#\s+Episode\s+\d+\s+[—–-]\s+(.+)$", stripped)
            if m3:
                title = m3.group(1).strip()

    if not title:
        title = episode_id.replace("_", " ").title()

    # --- Split into segment blocks ---
    # Each ## heading that is NOT the top-level metadata starts a new segment.
    # Metadata headings: "# Episode...", "## Title:", "## Subtitle:"
    _META_PATTERNS = re.compile(
        r"^(#\s+Episode|##\s+Title:|##\s+Subtitle:)", re.IGNORECASE
    )

    segment_start_indices: list[int] = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"^#{1,3}\s+\S", stripped):
            if not _META_PATTERNS.match(stripped):
                segment_start_indices.append(idx)

    # Build raw segment blocks
    raw_segments: list[list[str]] = []
    for i, start in enumerate(segment_start_indices):
        end = segment_start_indices[i + 1] if i + 1 < len(segment_start_indices) else len(lines)
        raw_segments.append(lines[start:end])

    # Parse each block
    segments: list[ScriptSegment] = []
    for block in raw_segments:
        if block:
            seg = _parse_segment_lines(block)
            segments.append(seg)

    return ParsedScript(
        episode_id=episode_id,
        title=title,
        series_subtitle=series_subtitle,
        segments=segments,
    )
