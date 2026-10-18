"""
Audit long-form episode scripts for listener-pull and spoken-story quality.

Outputs:
  - output/story_audit/story_quality_report.csv
  - output/story_audit/story_quality_summary.md
"""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = ROOT / "output" / "physics"
OUT_DIR = ROOT / "output" / "story_audit"

sys.path.insert(0, str(ROOT))

from src.pipeline.script_parser import parse_script

WORD_RE = re.compile(r"\b\w[\w'-]*\b")
TURN_RE = re.compile(
    r"\b(but|however|instead|until|wrong|contradiction|paradox|fails|failed|problem|question|why|turns out|except|yet)\b",
    re.IGNORECASE,
)
PROBLEM_RE = re.compile(
    r"\b(wrong|mistake|problem|paradox|contradiction|fails?|breaks?|impossible|question)\b",
    re.IGNORECASE,
)
HUMAN_RE = re.compile(
    r"\b(aristotle|galileo|newton|einstein|maxwell|faraday|bohr|planck|heisenberg|schrödinger|schrodinger|euler|lagrange|hamilton|noether|kepler|philoponus|buridan)\b",
    re.IGNORECASE,
)


@dataclass
class AuditRow:
    path: str
    title: str
    words: int
    narration_lines: int
    turns_per_1000: float
    hook_problem: int
    hook_human: int
    avg_line_words: float
    max_line_words: int
    long_line_count: int
    score: float


def wc(text: str) -> int:
    return len(WORD_RE.findall(text))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[AuditRow] = []

    for path in sorted(SCRIPTS_ROOT.rglob("*_youtube_long.md")):
        parsed = parse_script(str(path))
        narration_lines = [
            line.strip()
            for segment in parsed.segments
            for line in segment.narrator_lines
            if line.strip()
        ]
        joined = " ".join(narration_lines)
        words = wc(joined)
        turns = len(TURN_RE.findall(joined))
        first_lines = " ".join(narration_lines[:8])
        avg_line_words = (sum(wc(line) for line in narration_lines) / len(narration_lines)) if narration_lines else 0.0
        max_line_words = max((wc(line) for line in narration_lines), default=0)
        long_line_count = sum(1 for line in narration_lines if wc(line) >= 22)
        turns_per_1000 = (turns / (words / 1000.0)) if words else 0.0
        hook_problem = 1 if PROBLEM_RE.search(first_lines) else 0
        hook_human = 1 if HUMAN_RE.search(first_lines) else 0

        # Higher is better. Heavily reward listener pull, penalize dense spoken lines.
        score = (
            min(turns_per_1000, 18.0) * 3.0
            + hook_problem * 12.0
            + hook_human * 6.0
            + max(0.0, 16.0 - avg_line_words) * 1.4
            - long_line_count * 0.15
        )

        rows.append(
            AuditRow(
                path=str(path.relative_to(ROOT)),
                title=parsed.title,
                words=words,
                narration_lines=len(narration_lines),
                turns_per_1000=round(turns_per_1000, 2),
                hook_problem=hook_problem,
                hook_human=hook_human,
                avg_line_words=round(avg_line_words, 2),
                max_line_words=max_line_words,
                long_line_count=long_line_count,
                score=round(score, 2),
            )
        )

    rows.sort(key=lambda row: row.score)

    csv_path = OUT_DIR / "story_quality_report.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "path",
                "title",
                "words",
                "narration_lines",
                "turns_per_1000",
                "hook_problem",
                "hook_human",
                "avg_line_words",
                "max_line_words",
                "long_line_count",
                "score",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)

    summary_lines = [
        "# Story Quality Summary",
        "",
        f"- Scripts audited: **{len(rows)}**",
        "",
        "## Lowest-Scoring Episodes",
        "",
    ]
    for row in rows[:30]:
        summary_lines.append(
            f"- **{row.title}** — score {row.score}, turns/1000 {row.turns_per_1000}, avg line words {row.avg_line_words}, file `{row.path}`"
        )

    summary_lines.extend(["", "## Highest-Scoring Episodes", ""])
    for row in reversed(rows[-30:]):
        summary_lines.append(
            f"- **{row.title}** — score {row.score}, turns/1000 {row.turns_per_1000}, avg line words {row.avg_line_words}, file `{row.path}`"
        )

    summary_path = OUT_DIR / "story_quality_summary.md"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
