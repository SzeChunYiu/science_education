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

__all__ = [
    # Parsing
    "ParsedScript",
    "ScriptSegment",
    "parse_script",
    # Mapping
    "SceneMapper",
    "map_script_to_scenes",
]
