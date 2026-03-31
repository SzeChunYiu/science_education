# Source Archive

This folder holds legacy or superseded source scripts that are no longer part of the main production path.

Current rule:

- keep active production code in `src/pipeline/`, `src/animation/`, and the planner-backed preview tools
- move standalone demos and one-off experiments here when they stop representing the canonical workflow
- do not delete archived scripts until their replacement path is documented

Current archived scripts:

- `storybook_animatic_demo.py`: older standalone demo reel generator, superseded by the planner-backed preview and render workflow
