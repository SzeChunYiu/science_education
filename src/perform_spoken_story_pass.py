"""
Apply a spoken-story pass to all long-form episode scripts.

Goal:
    Keep the meaning and physics content intact while reshaping prose into
    shorter, more performable thought units for narration.

What it changes:
    - Splits long essay-like narration lines into shorter spoken chunks.
    - Preserves headings, [Visual: ...] blocks, equations, quotes, bullets,
      and existing pacing tags.
    - Keeps the first chunk under an existing tone tag; subsequent chunks are
      emitted as plain narration lines so the narration renderer can perform
      them as separate beats.

Usage:
    python3 src/perform_spoken_story_pass.py --write
    python3 src/perform_spoken_story_pass.py --check
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = ROOT / "output" / "physics"

TONE_TAG_RE = re.compile(r"^\[(?P<tone>[a-zA-Z ]+)\]\s*(?P<rest>.*)$")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[\"“'(\[]?[A-Z0-9])")
WORD_RE = re.compile(r"\b\w[\w'-]*\b")
PUNCHY_START_RE = re.compile(
    r"^(but|so|now|why|then|instead|except|until|and yet|that means|that is|this is)\b",
    re.IGNORECASE,
)


@dataclass
class PassStats:
    files_seen: int = 0
    files_changed: int = 0
    lines_split: int = 0
    chunks_created: int = 0


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def is_equation_like(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if stripped.startswith("**") and stripped.endswith("**"):
        return True
    if stripped.startswith(">"):
        return True
    if "=" in stripped and word_count(stripped) <= 20:
        return True
    return False


def keep_line_verbatim(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if stripped.startswith("#"):
        return True
    if stripped.startswith("[Visual:"):
        return True
    if stripped == "]":
        return True
    if stripped.startswith("- ") or re.match(r"^\d+\.\s", stripped):
        return True
    if is_equation_like(stripped):
        return True
    return False


def should_stand_alone(sentence: str) -> bool:
    wc = word_count(sentence)
    stripped = sentence.strip()
    if not stripped:
        return True
    if stripped.endswith("?"):
        return True
    if wc <= 7:
        return True
    if wc >= 24:
        return True
    if PUNCHY_START_RE.match(stripped):
        return True
    return False


def split_into_spoken_chunks(text: str) -> list[str]:
    stripped = re.sub(r"\s+", " ", text.strip())
    if not stripped:
        return []

    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(stripped) if s.strip()]
    if len(sentences) <= 1:
        return [stripped]

    chunks: list[str] = []
    i = 0
    while i < len(sentences):
        current = sentences[i]
        if should_stand_alone(current):
            chunks.append(current)
            i += 1
            continue

        if i + 1 < len(sentences):
            nxt = sentences[i + 1]
            combined_wc = word_count(current) + word_count(nxt)
            if (
                not should_stand_alone(nxt)
                and combined_wc <= 28
            ):
                chunks.append(f"{current} {nxt}")
                i += 2
                continue

        chunks.append(current)
        i += 1

    return chunks


def rewrite_line(raw_line: str, stats: PassStats) -> list[str]:
    if keep_line_verbatim(raw_line):
        return [raw_line]

    stripped = raw_line.strip()
    tone_match = TONE_TAG_RE.match(stripped)
    if tone_match:
        tone = tone_match.group("tone").strip()
        rest = tone_match.group("rest").strip()
        if tone.lower() == "pause" and not rest:
            return [raw_line]
        chunks = split_into_spoken_chunks(rest)
        if len(chunks) <= 1:
            return [raw_line]
        stats.lines_split += 1
        stats.chunks_created += len(chunks) - 1
        out = [f"[{tone}] {chunks[0]}"]
        out.extend(chunks[1:])
        return out

    chunks = split_into_spoken_chunks(stripped)
    if len(chunks) <= 1:
        return [raw_line]

    stats.lines_split += 1
    stats.chunks_created += len(chunks) - 1
    return chunks


def rewrite_script(path: Path, stats: PassStats, write: bool) -> bool:
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines()

    out_lines: list[str] = []
    in_visual = False

    for raw_line in lines:
        stripped = raw_line.strip()

        if in_visual:
            out_lines.append(raw_line)
            if stripped.endswith("]") or stripped == "]":
                in_visual = False
            continue

        if stripped.startswith("[Visual:") and not stripped.endswith("]"):
            in_visual = True
            out_lines.append(raw_line)
            continue

        out_lines.extend(rewrite_line(raw_line, stats))

    rewritten = "\n".join(out_lines) + ("\n" if original.endswith("\n") else "")
    changed = rewritten != original
    if changed and write:
        path.write_text(rewritten, encoding="utf-8")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Rewrite files in place.")
    parser.add_argument("--check", action="store_true", help="Report only; do not modify files.")
    args = parser.parse_args()

    write = args.write and not args.check
    stats = PassStats()
    changed_paths: list[Path] = []

    for path in sorted(SCRIPTS_ROOT.rglob("*_youtube_long.md")):
        stats.files_seen += 1
        if rewrite_script(path, stats, write=write):
            stats.files_changed += 1
            changed_paths.append(path)

    print(f"Files scanned   : {stats.files_seen}")
    print(f"Files changed   : {stats.files_changed}")
    print(f"Lines split     : {stats.lines_split}")
    print(f"Chunks created  : {stats.chunks_created}")
    if changed_paths:
        print("Sample changed files:")
        for path in changed_paths[:10]:
            print(path)


if __name__ == "__main__":
    main()
