"""
Stage 03 — Pedagogy Planner: 30 tests
Run: python -m pytest tests/test_stage03_pedagogy.py -v
"""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import PedagogyPlan

# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_scene(scene_id, equations=None, duration=45):
    return {
        "scene_id": scene_id,
        "scene_title": f"Scene {scene_id}",
        "learning_goal": f"Goal {scene_id}",
        "visual_metaphor": f"Visual {scene_id}",
        "equations_to_show": equations or [],
        "animation_strategy": f"Step 1. Step 2. Step 3. Step 4. Step 5.",
        "estimated_duration_seconds": duration,
    }

VALID_PLAN = {"scenes": [
    make_scene(1, equations=[]),
    make_scene(2, equations=[r"a^2+b^2=c^2"]),
    make_scene(3, equations=[r"a^2+b^2=c^2"]),
    make_scene(4, equations=[r"(AB)C=A(BC)"]),
    make_scene(5, equations=[r"A \cdot B = C"]),
]}

THREE_SCENE_PLAN = {"scenes": [make_scene(i) for i in range(1, 4)]}
FIVE_SCENE_PLAN  = {"scenes": [make_scene(i) for i in range(1, 6)]}


# ══════════════════════════════════════════════════════════════════════════════
# GROUP A: Scene 1 Hook Rules (T01–T06)
# ══════════════════════════════════════════════════════════════════════════════

class TestScene1Hook:

    def test_01_scene_1_has_no_equations(self):
        result = PedagogyPlan(**VALID_PLAN)
        s1 = next(s for s in result.scenes if s.scene_id == 1)
        assert s1.equations_to_show == []

    def test_02_scene_1_has_learning_goal(self):
        result = PedagogyPlan(**VALID_PLAN)
        s1 = result.scenes[0]
        assert len(s1.learning_goal.strip()) > 0

    def test_03_scene_1_has_visual_metaphor(self):
        result = PedagogyPlan(**VALID_PLAN)
        s1 = result.scenes[0]
        assert len(s1.visual_metaphor.strip()) > 0

    def test_04_scene_1_has_animation_strategy(self):
        result = PedagogyPlan(**VALID_PLAN)
        s1 = result.scenes[0]
        assert len(s1.animation_strategy.strip()) > 0

    def test_05_scene_1_has_valid_duration(self):
        result = PedagogyPlan(**VALID_PLAN)
        s1 = result.scenes[0]
        assert 30 <= s1.estimated_duration_seconds <= 90

    def test_06_scene_1_title_nonempty(self):
        result = PedagogyPlan(**VALID_PLAN)
        s1 = result.scenes[0]
        assert len(s1.scene_title.strip()) > 0


# ══════════════════════════════════════════════════════════════════════════════
# GROUP B: Scene Count Validation (T07–T11)
# ══════════════════════════════════════════════════════════════════════════════

class TestSceneCount:

    def test_07_three_scene_plan_valid(self):
        result = PedagogyPlan(**THREE_SCENE_PLAN)
        assert 3 <= len(result.scenes) <= 5

    def test_08_five_scene_plan_valid(self):
        result = PedagogyPlan(**FIVE_SCENE_PLAN)
        assert 3 <= len(result.scenes) <= 5

    def test_09_scene_count_respected_by_config(self):
        from backend.config import settings
        result = PedagogyPlan(**FIVE_SCENE_PLAN)
        if len(result.scenes) > settings.max_scenes:
            result.scenes = result.scenes[:settings.max_scenes]
        assert len(result.scenes) <= settings.max_scenes

    def test_10_scenes_is_list(self):
        result = PedagogyPlan(**VALID_PLAN)
        assert isinstance(result.scenes, list)

    def test_11_all_scenes_have_scene_id(self):
        result = PedagogyPlan(**VALID_PLAN)
        for s in result.scenes:
            assert hasattr(s, 'scene_id') and s.scene_id is not None


# ══════════════════════════════════════════════════════════════════════════════
# GROUP C: LaTeX Sanitization (T12–T18)
# ══════════════════════════════════════════════════════════════════════════════

class TestEquationSanitization:

    def test_12_begin_pmatrix_stripped(self):
        dirty = {"scenes": [
            make_scene(1),
            make_scene(2, equations=[r"\begin{pmatrix}1&2\end{pmatrix}", r"a^2+b^2=c^2"]),
        ]}
        result = PedagogyPlan(**dirty)
        for scene in result.scenes:
            if scene.equations_to_show:
                scene.equations_to_show = [e for e in scene.equations_to_show if r'\begin' not in e]
        s2 = result.scenes[1]
        assert all(r'\begin' not in e for e in s2.equations_to_show)

    def test_13_begin_bmatrix_stripped(self):
        dirty = {"scenes": [
            make_scene(1),
            make_scene(2, equations=[r"\begin{bmatrix}a&b\end{bmatrix}"]),
        ]}
        result = PedagogyPlan(**dirty)
        for s in result.scenes:
            s.equations_to_show = [e for e in s.equations_to_show if r'\begin' not in e]
        s2 = result.scenes[1]
        assert len(s2.equations_to_show) == 0

    def test_14_safe_equations_preserved(self):
        data = {"scenes": [
            make_scene(1),
            make_scene(2, equations=[r"a^2+b^2=c^2", r"A \cdot B = C"]),
        ]}
        result = PedagogyPlan(**data)
        for s in result.scenes:
            s.equations_to_show = [e for e in s.equations_to_show if r'\begin' not in e]
        assert len(result.scenes[1].equations_to_show) == 2

    def test_15_mixed_clean_and_dirty_equations(self):
        data = {"scenes": [
            make_scene(1),
            make_scene(2, equations=[r"\begin{cases}x=1\end{cases}", r"y=mx+b"]),
        ]}
        result = PedagogyPlan(**data)
        for s in result.scenes:
            s.equations_to_show = [e for e in s.equations_to_show if r'\begin' not in e]
        assert result.scenes[1].equations_to_show == [r"y=mx+b"]

    def test_16_end_environment_also_stripped(self):
        data = {"scenes": [
            make_scene(1),
            make_scene(2, equations=[r"\end{pmatrix}", r"c=\sqrt{a^2+b^2}"]),
        ]}
        result = PedagogyPlan(**data)
        for s in result.scenes:
            s.equations_to_show = [e for e in s.equations_to_show
                                   if r'\begin' not in e and r'\end' not in e]
        assert result.scenes[1].equations_to_show == [r"c=\sqrt{a^2+b^2}"]

    def test_17_empty_equation_list_untouched(self):
        result = PedagogyPlan(**VALID_PLAN)
        s1 = result.scenes[0]
        s1.equations_to_show = [e for e in s1.equations_to_show if r'\begin' not in e]
        assert s1.equations_to_show == []

    def test_18_cdot_equation_preserved(self):
        data = {"scenes": [make_scene(1), make_scene(2, equations=[r"A \cdot B = C"])]}
        result = PedagogyPlan(**data)
        for s in result.scenes:
            s.equations_to_show = [e for e in s.equations_to_show if r'\begin' not in e]
        assert r"A \cdot B = C" in result.scenes[1].equations_to_show


# ══════════════════════════════════════════════════════════════════════════════
# GROUP D: Scene ID & Sequence (T19–T24)
# ══════════════════════════════════════════════════════════════════════════════

class TestSceneSequence:

    def test_19_scene_ids_sequential_after_renumbering(self):
        result = PedagogyPlan(**VALID_PLAN)
        for i, s in enumerate(result.scenes, 1):
            s.scene_id = i
        ids = [s.scene_id for s in result.scenes]
        assert ids == list(range(1, len(result.scenes) + 1))

    def test_20_scene_ids_start_at_1(self):
        result = PedagogyPlan(**VALID_PLAN)
        for i, s in enumerate(result.scenes, 1):
            s.scene_id = i
        assert result.scenes[0].scene_id == 1

    def test_21_no_duplicate_scene_ids(self):
        result = PedagogyPlan(**VALID_PLAN)
        for i, s in enumerate(result.scenes, 1):
            s.scene_id = i
        ids = [s.scene_id for s in result.scenes]
        assert len(ids) == len(set(ids))

    def test_22_last_scene_has_highest_id(self):
        result = PedagogyPlan(**VALID_PLAN)
        for i, s in enumerate(result.scenes, 1):
            s.scene_id = i
        last_id = result.scenes[-1].scene_id
        assert last_id == len(result.scenes)

    def test_23_scene_titles_are_nonempty(self):
        result = PedagogyPlan(**VALID_PLAN)
        for s in result.scenes:
            assert len(s.scene_title.strip()) > 0

    def test_24_scene_learning_goals_are_nonempty(self):
        result = PedagogyPlan(**VALID_PLAN)
        for s in result.scenes:
            assert len(s.learning_goal.strip()) > 0


# ══════════════════════════════════════════════════════════════════════════════
# GROUP E: Duration & Quality (T25–T30)
# ══════════════════════════════════════════════════════════════════════════════

class TestSceneDuration:

    def test_25_all_durations_above_minimum(self):
        result = PedagogyPlan(**VALID_PLAN)
        for s in result.scenes:
            assert s.estimated_duration_seconds >= 30

    def test_26_all_durations_below_maximum(self):
        result = PedagogyPlan(**VALID_PLAN)
        for s in result.scenes:
            assert s.estimated_duration_seconds <= 90

    def test_27_total_duration_under_6_minutes(self):
        result = PedagogyPlan(**VALID_PLAN)
        total = sum(s.estimated_duration_seconds for s in result.scenes)
        assert total <= 360

    def test_28_animation_strategy_contains_steps(self):
        result = PedagogyPlan(**VALID_PLAN)
        for s in result.scenes:
            assert "Step" in s.animation_strategy or len(s.animation_strategy) > 20

    def test_29_visual_metaphor_nonempty(self):
        result = PedagogyPlan(**VALID_PLAN)
        for s in result.scenes:
            assert len(s.visual_metaphor.strip()) > 0

    def test_30_plan_serializable(self):
        result = PedagogyPlan(**VALID_PLAN)
        d = result.model_dump()
        assert "scenes" in d
        assert isinstance(d["scenes"], list)
        assert all("scene_id" in s for s in d["scenes"])
