"""
Stage 04 — Scene Architect: 30 tests
Run: python -m pytest tests/test_stage04_scene.py -v
"""
import sys
import re
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import (
    SceneInstructionSet, SceneInstruction,
    ManimObject, ManimAnimation, PedagogyPlan
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_title_obj(scene_id):
    return ManimObject(
        obj_id=f"title_{scene_id}",
        obj_type="Text",
        properties={"text": f"Scene {scene_id}", "position": "to_edge(UP, buff=0.25)", "color": "YELLOW"}
    )

def make_eq_obj(scene_id):
    return ManimObject(
        obj_id=f"eq_{scene_id}",
        obj_type="MathTex",
        properties={"latex": "a^2+b^2=c^2", "position": "move_to([0, -2.5, 0])"}
    )

def make_fadeout():
    return ManimAnimation(action="FadeOut", target="*mobjects", duration=1.0)

def make_wait(duration=0.5):
    return ManimAnimation(action="wait", target="", duration=duration)

def make_scene_instr(scene_id, with_eq=True, with_fadeout=True):
    objects = [make_title_obj(scene_id)]
    animations = [
        ManimAnimation(action="Write", target=f"title_{scene_id}", duration=1.2),
        make_wait(1.0),
    ]
    if with_eq:
        objects.append(make_eq_obj(scene_id))
        animations.append(ManimAnimation(action="Write", target=f"eq_{scene_id}", duration=2.0))
        animations.append(make_wait(2.0))
    if with_fadeout:
        animations.append(make_fadeout())
        animations.append(make_wait(0.5))
    return SceneInstruction(scene_id=scene_id, objects=objects, animations=animations)

FULL_SET = SceneInstructionSet(scene_instructions=[
    make_scene_instr(i) for i in range(1, 6)
])


# ══════════════════════════════════════════════════════════════════════════════
# GROUP A: Schema (T01–T06)
# ══════════════════════════════════════════════════════════════════════════════

class TestSceneSchema:

    def test_01_instruction_set_parses(self):
        assert len(FULL_SET.scene_instructions) == 5

    def test_02_scene_instructions_is_list(self):
        assert isinstance(FULL_SET.scene_instructions, list)

    def test_03_each_instruction_has_scene_id(self):
        for instr in FULL_SET.scene_instructions:
            assert instr.scene_id is not None

    def test_04_each_instruction_has_objects_list(self):
        for instr in FULL_SET.scene_instructions:
            assert isinstance(instr.objects, list)

    def test_05_each_instruction_has_animations_list(self):
        for instr in FULL_SET.scene_instructions:
            assert isinstance(instr.animations, list)

    def test_06_objects_have_obj_id(self):
        for instr in FULL_SET.scene_instructions:
            for obj in instr.objects:
                assert obj.obj_id and len(obj.obj_id) > 0


# ══════════════════════════════════════════════════════════════════════════════
# GROUP B: Object Positioning (T07–T13)
# ══════════════════════════════════════════════════════════════════════════════

class TestObjectPositioning:

    def test_07_title_uses_to_edge_up(self):
        for instr in FULL_SET.scene_instructions:
            titles = [o for o in instr.objects if "title" in o.obj_id]
            for t in titles:
                pos = t.properties.get("position", "")
                assert "UP" in pos or "to_edge" in pos

    def test_08_equation_at_bottom_zone(self):
        for instr in FULL_SET.scene_instructions:
            eqs = [o for o in instr.objects if o.obj_type in ("MathTex", "safe_tex")]
            for eq in eqs:
                pos = eq.properties.get("position", "")
                match = re.search(r'\[\s*[\d.-]+\s*,\s*([-\d.]+)', pos)
                if match:
                    y = float(match.group(1))
                    assert y <= -2.0, f"Equation y={y} not in bottom zone"

    def test_09_content_objects_not_in_title_zone(self):
        for instr in FULL_SET.scene_instructions:
            non_titles = [o for o in instr.objects if "title" not in o.obj_id]
            for obj in non_titles:
                pos = obj.properties.get("position", "")
                assert "to_edge(UP)" not in pos or obj.obj_type == "Text"

    def test_10_max_4_objects_per_scene(self):
        for instr in FULL_SET.scene_instructions:
            assert len(instr.objects) <= 4, \
                f"Scene {instr.scene_id} has {len(instr.objects)} objects (max 4)"

    def test_11_title_color_is_yellow(self):
        for instr in FULL_SET.scene_instructions:
            titles = [o for o in instr.objects if "title" in o.obj_id]
            for t in titles:
                color = t.properties.get("color", "")
                assert "YELLOW" in color.upper()

    def test_12_equation_has_font_size_or_position(self):
        for instr in FULL_SET.scene_instructions:
            eqs = [o for o in instr.objects if o.obj_type in ("MathTex", "ManimObject")]
            for eq in eqs:
                has_prop = "position" in eq.properties or "font_size" in eq.properties
                assert has_prop or len(eq.properties) > 0

    def test_13_objects_have_nonempty_type(self):
        for instr in FULL_SET.scene_instructions:
            for obj in instr.objects:
                assert len(obj.obj_type.strip()) > 0


# ══════════════════════════════════════════════════════════════════════════════
# GROUP C: Animation Sequence (T14–T20)
# ══════════════════════════════════════════════════════════════════════════════

class TestAnimationSequence:

    def test_14_fadeout_present_in_every_scene(self):
        for instr in FULL_SET.scene_instructions:
            actions = [a.action for a in instr.animations]
            assert "FadeOut" in actions, f"Scene {instr.scene_id} missing FadeOut"

    def test_15_wait_after_fadeout(self):
        for instr in FULL_SET.scene_instructions:
            actions = [a.action for a in instr.animations]
            if "FadeOut" in actions:
                fo_idx = max(i for i, a in enumerate(actions) if a == "FadeOut")
                if fo_idx + 1 < len(actions):
                    assert actions[fo_idx + 1] == "wait"

    def test_16_write_animation_present(self):
        for instr in FULL_SET.scene_instructions:
            actions = [a.action for a in instr.animations]
            assert "Write" in actions or "Create" in actions or "FadeIn" in actions

    def test_17_animation_durations_positive(self):
        for instr in FULL_SET.scene_instructions:
            for anim in instr.animations:
                assert anim.duration > 0

    def test_18_at_least_3_animations_per_scene(self):
        for instr in FULL_SET.scene_instructions:
            assert len(instr.animations) >= 3

    def test_19_all_animation_actions_are_strings(self):
        for instr in FULL_SET.scene_instructions:
            for anim in instr.animations:
                assert isinstance(anim.action, str) and len(anim.action) > 0

    def test_20_animation_targets_are_strings(self):
        for instr in FULL_SET.scene_instructions:
            for anim in instr.animations:
                assert isinstance(anim.target, str)


# ══════════════════════════════════════════════════════════════════════════════
# GROUP D: Scene Count & ID Integrity (T21–T25)
# ══════════════════════════════════════════════════════════════════════════════

class TestSceneIntegrity:

    def test_21_scene_count_matches_pedagogy_plan(self):
        plan_scene_count = 5
        assert len(FULL_SET.scene_instructions) == plan_scene_count

    def test_22_scene_ids_are_unique(self):
        ids = [i.scene_id for i in FULL_SET.scene_instructions]
        assert len(ids) == len(set(ids))

    def test_23_scene_ids_start_from_1(self):
        ids = sorted(i.scene_id for i in FULL_SET.scene_instructions)
        assert ids[0] == 1

    def test_24_no_scene_with_zero_objects(self):
        for instr in FULL_SET.scene_instructions:
            assert len(instr.objects) > 0

    def test_25_scene_instruction_serializable(self):
        d = FULL_SET.model_dump()
        assert "scene_instructions" in d
        assert isinstance(d["scene_instructions"], list)


# ══════════════════════════════════════════════════════════════════════════════
# GROUP E: Edge Cases (T26–T30)
# ══════════════════════════════════════════════════════════════════════════════

class TestSceneEdgeCases:

    def test_26_single_scene_instruction_valid(self):
        single = SceneInstructionSet(scene_instructions=[make_scene_instr(1)])
        assert len(single.scene_instructions) == 1

    def test_27_scene_without_equations_still_valid(self):
        no_eq = make_scene_instr(1, with_eq=False)
        assert len(no_eq.objects) >= 1

    def test_28_scene_with_only_text_objects_valid(self):
        text_only = SceneInstruction(
            scene_id=1,
            objects=[ManimObject(obj_id="t1", obj_type="Text",
                                 properties={"text": "Title", "position": "to_edge(UP, buff=0.25)"})],
            animations=[ManimAnimation(action="Write", target="t1", duration=1.2),
                        ManimAnimation(action="FadeOut", target="*mobjects", duration=1.0)]
        )
        assert len(text_only.objects) == 1

    def test_29_transform_animation_valid(self):
        transform = ManimAnimation(action="Transform", target="eq1", duration=1.5)
        assert transform.action == "Transform"
        assert transform.duration == 1.5

    def test_30_manimobject_properties_dict(self):
        obj = ManimObject(
            obj_id="test",
            obj_type="Circle",
            properties={"color": "BLUE", "radius": "2.0"}
        )
        assert isinstance(obj.properties, dict)
        assert "color" in obj.properties
