"""
src/pipeline — Script-to-scene-descriptor pipeline.

Public API
----------
Parsing
~~~~~~~
.. autofunction:: script_parser.parse_script
.. autoclass:: script_parser.ParsedScript
.. autoclass:: script_parser.ScriptSegment

Mapping
~~~~~~~
.. autofunction:: scene_mapper.map_script_to_scenes
.. autoclass:: scene_mapper.SceneMapper

Validation
~~~~~~~~~~
.. autofunction:: scene_validator.validate_scene_sequence
.. autoclass:: scene_validator.ValidationReport
.. autoclass:: scene_validator.ValidationIssue

Batch processing
~~~~~~~~~~~~~~~~
.. autofunction:: batch_processor.process_episode
.. autofunction:: batch_processor.process_all_episodes
"""

from .script_parser import (
    ParsedScript,
    ScriptSegment,
    parse_script,
)

from .scene_mapper import (
    SceneMapper,
    map_script_to_scenes,
)

from .scene_validator import (
    ValidationReport,
    ValidationIssue,
    validate_scene_sequence,
)

from .batch_processor import (
    process_episode,
    process_all_episodes,
)

__all__ = [
    # Parsing
    "ParsedScript",
    "ScriptSegment",
    "parse_script",
    # Mapping
    "SceneMapper",
    "map_script_to_scenes",
    # Validation
    "ValidationReport",
    "ValidationIssue",
    "validate_scene_sequence",
    # Batch
    "process_episode",
    "process_all_episodes",
]
