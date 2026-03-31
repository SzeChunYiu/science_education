"""
slide_planner.py — automatic PowerPoint-style layout planning for scene dicts.

The planner chooses a slide archetype and rect geometry before the scene
factory renders animated output. This keeps layout selection automatic and
consistent across previews and real episode renders.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional

from src.layout import constants


Rect = tuple[int, int, int, int]


def plan_scene_layout(scene_dict: dict[str, Any], aspect_ratio: str = "16:9") -> dict[str, Any]:
    """
    Return a layout plan with an archetype label and named rects.
    """
    template = scene_dict.get("template", "narration_with_caption")
    canvas = constants.ASPECT_TO_CANVAS.get(aspect_ratio, constants.YOUTUBE_LONG)
    elements = scene_dict.get("elements", [])

    planners = {
        "equation_reveal": _plan_equation_reveal,
        "derivation_step": _plan_derivation_step,
        "character_scene": _plan_character_scene,
        "historical_moment": _plan_historical_moment,
        "two_character_debate": _plan_two_character_debate,
        "two_element_comparison": _plan_comparison_scene,
        "diagram_explanation": _plan_visual_explainer,
        "animation_scene": _plan_animation_scene,
        "object_demo": _plan_object_demo,
        "timeline_sequence": _plan_timeline_sequence,
        "narration_with_caption": _plan_hook_scene,
        "limits_breakdown": _plan_limits_breakdown,
        "worked_example": _plan_worked_example,
        "outro_bridge": _plan_outro_bridge,
    }
    planner = planners.get(template, _plan_hook_scene)
    plan = planner(canvas, aspect_ratio, elements)
    return {
        "archetype": plan["archetype"],
        "rects": plan["rects"],
    }


def apply_layout_plan(scene_dict: dict[str, Any], aspect_ratio: str = "16:9") -> dict[str, Any]:
    """
    Ensure a scene dict has an automatic layout plan.

    Existing plans are preserved. Matching element roles also receive direct
    x/y/w/h overrides so downstream consumers can honor them.
    """
    scene = deepcopy(scene_dict)
    if scene.get("layout_plan"):
        return scene

    plan = plan_scene_layout(scene, aspect_ratio=aspect_ratio)
    scene["layout_plan"] = plan
    _apply_role_rects(scene.get("elements", []), plan.get("rects", {}))
    return scene


def _apply_role_rects(elements: list[dict[str, Any]], rects: dict[str, Rect]) -> None:
    role_map = {
        "equation": "equation_center",
        "caption": "caption",
        "headline": "headline",
        "title": "headline",
        "subtitle": "body_text",
        "character": "character_center",
        "metadata": "lower_third",
        "diagram": "diagram",
        "object": "diagram",
        "left_title": "character_left",
        "right_title": "character_right",
        "left_name": "lower_third",
        "right_name": "lower_third",
        "left_speech": "caption",
        "right_speech": "caption",
        "previous": "headline",
        "derivation": "timeline",
        "timeline": "timeline",
        "intro": "headline",
        "annotation": "caption",
        "warning": "headline",
        "limit": "caption",
        "setup": "headline",
        "explanation": "caption",
        "callout": "lower_third",
        "accent": "accent",
        "substitution": "caption",
        "result": "lower_third",
        "takeaway": "body_text",
        "next": "caption",
        "hero": "diagram",
        "label": "headline",
    }
    assigned: set[tuple[str, int]] = set()
    for rect_key, role in role_map.items():
        rect = rects.get(rect_key)
        if rect is None:
            continue
        for idx, el in enumerate(elements):
            if el.get("role") != role or (role, idx) in assigned:
                continue
            x, y, w, h = rect
            el["x"], el["y"], el["w"], el["h"] = x, y, w, h
            assigned.add((role, idx))
            break


def _plan_equation_reveal(canvas: tuple[int, int], aspect_ratio: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    eq_text = _text(_get_el(elements, "equation_center"))
    cap_text = _text(_get_el(elements, "caption"))
    eq_len = len(eq_text)
    cap_len = len(cap_text)
    if aspect_ratio == "9:16":
        eq_w = 0.86 if eq_len > 24 else 0.78
        cap_h = 0.14 if cap_len > 70 else 0.11
        rects = {
            "equation": _frac(canvas, 0.07, 0.43, eq_w, 0.15),
            "caption": _frac(canvas, 0.10, 0.62, 0.80, cap_h),
        }
    else:
        eq_w = 0.68 if eq_len > 24 else 0.60
        cap_h = 0.12 if cap_len > 70 else 0.10
        rects = {
            "equation": _frac(canvas, 0.16, 0.45, eq_w, 0.14),
            "caption": _frac(canvas, 0.18, 0.61, 0.64, cap_h),
        }
    return {"archetype": "equation_focus", "rects": rects}


def _plan_derivation_step(canvas: tuple[int, int], aspect_ratio: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    rects = {
        "previous": _frac(canvas, 0.16, 0.16, 0.68, 0.10) if aspect_ratio == "16:9" else _frac(canvas, 0.10, 0.12, 0.80, 0.10),
        "derivation": _frac(canvas, 0.16, 0.35, 0.68, 0.14) if aspect_ratio == "16:9" else _frac(canvas, 0.08, 0.32, 0.84, 0.14),
        "annotation": _frac(canvas, 0.18, 0.58, 0.64, 0.10) if aspect_ratio == "16:9" else _frac(canvas, 0.10, 0.58, 0.80, 0.12),
    }
    return {"archetype": "derivation_build", "rects": rects}


def _plan_character_scene(canvas: tuple[int, int], aspect_ratio: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    label_text = _text(_get_el(elements, "lower_third"))
    has_long_quote = len(label_text) > 36
    if aspect_ratio == "9:16":
        rects = {
            "character": _frac(canvas, 0.18, 0.26, 0.64, 0.40),
            "name": _frac(canvas, 0.18, 0.69, 0.64, 0.06),
            "year": _frac(canvas, 0.18, 0.75, 0.64, 0.04),
            "quote": _frac(canvas, 0.12, 0.81, 0.76, 0.11 if has_long_quote else 0.09),
        }
    else:
        rects = {
            "character": _frac(canvas, 0.08, 0.16, 0.26, 0.60),
            "name": _frac(canvas, 0.08, 0.73, 0.26, 0.06),
            "year": _frac(canvas, 0.08, 0.79, 0.26, 0.04),
            "quote": _frac(canvas, 0.42, 0.38, 0.34, 0.16 if has_long_quote else 0.12),
        }
    return {"archetype": "profile_quote", "rects": rects}


def _plan_historical_moment(canvas: tuple[int, int], aspect_ratio: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    caption = _text(_get_el(elements, "caption"))
    cap_h = 0.14 if len(caption) > 72 else 0.11
    if aspect_ratio == "9:16":
        rects = {
            "character": _frac(canvas, 0.18, 0.28, 0.64, 0.38),
            "metadata": _frac(canvas, 0.16, 0.70, 0.68, 0.06),
            "caption": _frac(canvas, 0.12, 0.80, 0.76, cap_h),
        }
    else:
        rects = {
            "character": _frac(canvas, 0.10, 0.16, 0.26, 0.60),
            "metadata": _frac(canvas, 0.08, 0.78, 0.28, 0.06),
            "caption": _frac(canvas, 0.44, 0.54, 0.38, cap_h),
        }
    return {"archetype": "historical_profile", "rects": rects}


def _plan_two_character_debate(canvas: tuple[int, int], aspect_ratio: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    if aspect_ratio == "9:16":
        rects = {
            "left_character": _frac(canvas, 0.10, 0.38, 0.34, 0.26),
            "right_character": _frac(canvas, 0.56, 0.38, 0.34, 0.26),
            "left_speech": _frac(canvas, 0.08, 0.16, 0.38, 0.12),
            "right_speech": _frac(canvas, 0.54, 0.16, 0.38, 0.12),
            "left_name": _frac(canvas, 0.08, 0.65, 0.36, 0.07),
            "right_name": _frac(canvas, 0.56, 0.65, 0.36, 0.07),
        }
    else:
        rects = {
            "left_character": _frac(canvas, 0.08, 0.22, 0.22, 0.54),
            "right_character": _frac(canvas, 0.70, 0.22, 0.22, 0.54),
            "left_speech": _frac(canvas, 0.22, 0.16, 0.22, 0.14),
            "right_speech": _frac(canvas, 0.56, 0.16, 0.22, 0.14),
            "left_name": _frac(canvas, 0.06, 0.76, 0.28, 0.08),
            "right_name": _frac(canvas, 0.66, 0.76, 0.28, 0.08),
        }
    return {"archetype": "dual_dialogue", "rects": rects}


def _plan_comparison_scene(canvas: tuple[int, int], aspect_ratio: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    left_text = _text(_get_el(elements, "character_left"))
    right_text = _text(_get_el(elements, "character_right"))
    long_side = max(len(left_text), len(right_text))
    cap_h = 0.12 if long_side > 36 else 0.10
    if aspect_ratio == "9:16":
        rects = {
            "left_panel": _frac(canvas, 0.10, 0.15, 0.80, 0.28),
            "right_panel": _frac(canvas, 0.10, 0.53, 0.80, 0.28),
            "left_title": _frac(canvas, 0.12, 0.17, 0.76, 0.08),
            "right_title": _frac(canvas, 0.12, 0.55, 0.76, 0.08),
            "left_asset": _frac(canvas, 0.28, 0.25, 0.44, 0.12),
            "right_asset": _frac(canvas, 0.28, 0.63, 0.44, 0.12),
            "left_caption": _frac(canvas, 0.16, 0.34, 0.68, cap_h),
            "right_caption": _frac(canvas, 0.16, 0.72, 0.68, cap_h),
            "vs": _frac(canvas, 0.40, 0.45, 0.20, 0.07),
            "bridge": _frac(canvas, 0.20, 0.87, 0.60, 0.06),
        }
    else:
        rects = {
            "left_panel": _frac(canvas, 0.08, 0.20, 0.34, 0.44),
            "right_panel": _frac(canvas, 0.58, 0.20, 0.34, 0.44),
            "left_title": _frac(canvas, 0.10, 0.20, 0.30, 0.09),
            "right_title": _frac(canvas, 0.60, 0.20, 0.30, 0.09),
            "left_asset": _frac(canvas, 0.16, 0.32, 0.18, 0.14),
            "right_asset": _frac(canvas, 0.64, 0.32, 0.22, 0.12),
            "left_caption": _frac(canvas, 0.10, 0.49, 0.30, cap_h),
            "right_caption": _frac(canvas, 0.60, 0.49, 0.30, cap_h),
            "vs": _frac(canvas, 0.46, 0.38, 0.08, 0.10),
            "bridge": _frac(canvas, 0.31, 0.72, 0.38, 0.08),
        }
    return {"archetype": "split_comparison", "rects": rects}


def _plan_visual_explainer(canvas: tuple[int, int], aspect_ratio: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    caption = _text(_get_el(elements, "caption"))
    cap_h = 0.11 if len(caption) > 80 else 0.08
    if aspect_ratio == "9:16":
        rects = {
            "headline": _frac(canvas, 0.10, 0.08, 0.80, 0.10),
            "diagram": _frac(canvas, 0.16, 0.25, 0.68, 0.32),
            "caption": _frac(canvas, 0.12, 0.68, 0.76, cap_h),
        }
    else:
        rects = {
            "headline": _frac(canvas, 0.10, 0.08, 0.80, 0.10),
            "diagram": _frac(canvas, 0.30, 0.22, 0.40, 0.42),
            "caption": _frac(canvas, 0.18, 0.69, 0.64, cap_h),
        }
    return {"archetype": "title_visual_caption", "rects": rects}


def _plan_animation_scene(canvas: tuple[int, int], aspect_ratio: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    plan = _plan_visual_explainer(canvas, aspect_ratio, elements)
    rects = dict(plan["rects"])
    if aspect_ratio == "9:16":
        rects["accent"] = _frac(canvas, 0.10, 0.24, 0.80, 0.34)
    else:
        rects["accent"] = _frac(canvas, 0.18, 0.22, 0.64, 0.42)
    return {"archetype": "motion_annotated_visual", "rects": rects}


def _plan_object_demo(canvas: tuple[int, int], aspect_ratio: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    if aspect_ratio == "9:16":
        rects = {
            "title": _frac(canvas, 0.10, 0.08, 0.80, 0.10),
            "object": _frac(canvas, 0.12, 0.20, 0.76, 0.32),
            "explanation": _frac(canvas, 0.12, 0.58, 0.76, 0.09),
            "callout": _frac(canvas, 0.28, 0.76, 0.44, 0.05),
            "accent": _frac(canvas, 0.70, 0.33, 0.14, 0.08),
        }
    else:
        rects = {
            "title": _frac(canvas, 0.18, 0.10, 0.64, 0.08),
            "object": _frac(canvas, 0.24, 0.22, 0.52, 0.30),
            "explanation": _frac(canvas, 0.18, 0.57, 0.64, 0.08),
            "callout": _frac(canvas, 0.36, 0.70, 0.28, 0.05),
            "accent": _frac(canvas, 0.68, 0.33, 0.14, 0.10),
        }
    return {"archetype": "object_focus_callout", "rects": rects}


def _plan_timeline_sequence(canvas: tuple[int, int], aspect_ratio: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    if aspect_ratio == "9:16":
        rects = {
            "intro": _frac(canvas, 0.14, 0.07, 0.72, 0.09),
            "timeline": _frac(canvas, 0.18, 0.50, 0.64, 0.018),
            "stages_region": _frac(canvas, 0.14, 0.18, 0.72, 0.58),
        }
    else:
        rects = {
            "intro": _frac(canvas, 0.14, 0.07, 0.72, 0.09),
            "timeline": _frac(canvas, 0.10, 0.50, 0.80, 0.012),
            "stages_region": _frac(canvas, 0.11, 0.32, 0.78, 0.35),
        }
    return {"archetype": "timeline_milestones", "rects": rects}


def _plan_hook_scene(canvas: tuple[int, int], aspect_ratio: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    title = _text(_get_el(elements, "headline"))
    subtitle = _text(_get_el(elements, "body_text")) or _text(_get_el(elements, "caption"))
    long_title = len(title) > 40
    long_subtitle = len(subtitle) > 85
    if aspect_ratio == "9:16":
        rects = {
            "title": _frac(canvas, 0.08, 0.08, 0.84, 0.14 if long_title else 0.12),
            "subtitle": _frac(canvas, 0.10, 0.28, 0.80, 0.16 if long_subtitle else 0.12),
            "hero": _frac(canvas, 0.20, 0.52, 0.60, 0.24),
            "badge": _frac(canvas, 0.24, 0.82, 0.52, 0.06),
        }
    else:
        rects = {
            "title": _frac(canvas, 0.12, 0.10, 0.76, 0.12 if long_title else 0.10),
            "subtitle": _frac(canvas, 0.12, 0.38, 0.46 if not long_subtitle else 0.54, 0.14 if long_subtitle else 0.11),
            "hero": _frac(canvas, 0.68, 0.20, 0.20, 0.48),
            "badge": _frac(canvas, 0.70, 0.72, 0.18, 0.06),
        }
    return {"archetype": "hook_title_visual", "rects": rects}


def _plan_limits_breakdown(canvas: tuple[int, int], aspect_ratio: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    if aspect_ratio == "9:16":
        rects = {
            "warning": _frac(canvas, 0.12, 0.10, 0.76, 0.08),
            "equation": _frac(canvas, 0.08, 0.30, 0.84, 0.20),
            "limit": _frac(canvas, 0.12, 0.64, 0.76, 0.10),
        }
    else:
        rects = {
            "warning": _frac(canvas, 0.20, 0.10, 0.60, 0.08),
            "equation": _frac(canvas, 0.14, 0.30, 0.72, 0.20),
            "limit": _frac(canvas, 0.22, 0.66, 0.56, 0.08),
        }
    return {"archetype": "equation_warning", "rects": rects}


def _plan_worked_example(canvas: tuple[int, int], aspect_ratio: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    if aspect_ratio == "9:16":
        rects = {
            "setup": _frac(canvas, 0.10, 0.10, 0.80, 0.12),
            "equation": _frac(canvas, 0.12, 0.30, 0.76, 0.16),
            "substitution": _frac(canvas, 0.14, 0.52, 0.72, 0.12),
            "result": _frac(canvas, 0.16, 0.72, 0.68, 0.10),
        }
    else:
        rects = {
            "setup": _frac(canvas, 0.12, 0.10, 0.76, 0.10),
            "equation": _frac(canvas, 0.20, 0.28, 0.60, 0.16),
            "substitution": _frac(canvas, 0.22, 0.52, 0.56, 0.12),
            "result": _frac(canvas, 0.24, 0.70, 0.52, 0.10),
        }
    return {"archetype": "worked_example_stack", "rects": rects}


def _plan_outro_bridge(canvas: tuple[int, int], aspect_ratio: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    if aspect_ratio == "9:16":
        rects = {
            "label": _frac(canvas, 0.22, 0.08, 0.56, 0.08),
            "takeaway": _frac(canvas, 0.10, 0.18, 0.80, 0.22),
            "next": _frac(canvas, 0.14, 0.50, 0.72, 0.16),
            "hero": _frac(canvas, 0.26, 0.72, 0.48, 0.12),
        }
    else:
        rects = {
            "label": _frac(canvas, 0.08, 0.09, 0.28, 0.06),
            "takeaway": _frac(canvas, 0.08, 0.22, 0.34, 0.18),
            "next": _frac(canvas, 0.08, 0.50, 0.30, 0.08),
            "hero": _frac(canvas, 0.58, 0.18, 0.30, 0.56),
        }
    return {"archetype": "outro_takeaway", "rects": rects}


def _get_el(elements: list[dict[str, Any]], role: str) -> Optional[dict[str, Any]]:
    for el in elements:
        if el.get("role") == role:
            return el
    return None


def _text(el: Optional[dict[str, Any]]) -> str:
    if el is None:
        return ""
    return str(el.get("text") or "").strip()


def _frac(canvas: tuple[int, int], x: float, y: float, w: float, h: float) -> Rect:
    cw, ch = canvas
    return (int(cw * x), int(ch * y), int(cw * w), int(ch * h))
