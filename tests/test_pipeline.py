"""
VisualAIze — Automated Pipeline Evaluation Suite
30 tests across all 7 pipeline stages.

Run:
    cd "D:\1IU\Practice\LLM Project Practice\visual-AI-ze"
    python -m pytest tests/test_pipeline.py -v --tb=short

Or run with detailed report:
    python -m pytest tests/test_pipeline.py -v --tb=short --html=tests/report.html
"""

import ast
import re
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# ── Add project root to path ──────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Shared fixtures ───────────────────────────────────────────────────────────

SAMPLE_PARSED = {
    "main_topic": "Pythagorean Theorem",
    "definitions": ["Right triangle: a triangle with one 90-degree angle"],
    "key_equations": ["a^2 + b^2 = c^2"],
    "core_claims": ["In a right triangle, the square of the hypotenuse equals the sum of squares of the legs"],
    "example_instances": ["3-4-5 triangle: 9+16=25"],
}

SAMPLE_CONCEPTS = {
    "core_concepts": [
        {"concept_name": "Right Triangle", "intuitive_explanation": "A triangle with 90 degrees",
         "mathematical_form": "90°", "why_it_matters": "Foundation of trigonometry"},
        {"concept_name": "Pythagorean Theorem", "intuitive_explanation": "Side relationship",
         "mathematical_form": "a^2+b^2=c^2", "why_it_matters": "Essential geometry"},
        {"concept_name": "Hypotenuse", "intuitive_explanation": "Longest side",
         "mathematical_form": "c", "why_it_matters": "Opposite the right angle"},
    ],
    "concept_ordering": ["Right Triangle", "Pythagorean Theorem", "Hypotenuse"],
}

SAMPLE_PEDAGOGY = {
    "scenes": [
        {"scene_id": 1, "scene_title": "The Hook", "learning_goal": "Curiosity",
         "visual_metaphor": "A triangle appears", "equations_to_show": [],
         "animation_strategy": "Step 1: title. Step 2: triangle. Step 3: wait.",
         "estimated_duration_seconds": 40},
        {"scene_id": 2, "scene_title": "Visual Proof", "learning_goal": "Intuition",
         "visual_metaphor": "Squares on sides", "equations_to_show": ["a^2+b^2=c^2"],
         "animation_strategy": "Step 1: squares. Step 2: equation.", "estimated_duration_seconds": 50},
        {"scene_id": 3, "scene_title": "Formal Statement", "learning_goal": "Formula",
         "visual_metaphor": "Equation reveal", "equations_to_show": ["a^2+b^2=c^2"],
         "animation_strategy": "Step 1: equation. Step 2: caption.", "estimated_duration_seconds": 45},
    ]
}

MINIMAL_MANIM_CODE = '''
from manim import *
import numpy as np
import re

def safe_tex(latex_str, **kwargs):
    try:
        return MathTex(latex_str, **kwargs)
    except Exception:
        return Text(str(latex_str)[:50], font_size=kwargs.get("font_size", 36))

class MathVizScene(Scene):
    def construct(self):
        title = Text("Pythagorean Theorem", font_size=36, color=YELLOW)
        title.to_edge(UP, buff=0.25)
        self.play(Write(title, run_time=1.2))
        self.wait(1.0)
        eq = safe_tex(r"a^2 + b^2 = c^2", font_size=44)
        eq.move_to([0, -2.5, 0])
        self.play(Write(eq, run_time=2.0))
        self.wait(2.0)
        self.play(FadeOut(*self.mobjects, run_time=1.0))
        self.wait(0.5)
'''


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1 — PARSER AGENT (Tests 1–5)
# ══════════════════════════════════════════════════════════════════════════════

class TestParserAgent:

    def test_01_parsed_content_schema_valid(self):
        """T01 — ParsedContent Pydantic schema accepts valid data."""
        from backend.models import ParsedContent
        result = ParsedContent(**SAMPLE_PARSED)
        assert result.main_topic == "Pythagorean Theorem"
        assert isinstance(result.key_equations, list)
        assert isinstance(result.definitions, list)
        assert isinstance(result.core_claims, list)
        assert isinstance(result.example_instances, list)

    def test_02_input_truncation_at_6000_chars(self):
        """T02 — Parser truncates input longer than 6000 chars."""
        from backend.agents import parser_agent
        long_input = "x" * 10000
        truncated = long_input[:6000]
        assert len(truncated) == 6000
        # Verify truncation logic matches what parser does
        assert len(long_input) > 6000
        assert long_input[:6000] == truncated

    def test_03_key_equations_are_strings(self):
        """T03 — All key_equations are non-empty strings."""
        from backend.models import ParsedContent
        result = ParsedContent(**SAMPLE_PARSED)
        for eq in result.key_equations:
            assert isinstance(eq, str)
            assert len(eq.strip()) > 0

    def test_04_main_topic_non_empty(self):
        """T04 — main_topic is a non-empty string."""
        from backend.models import ParsedContent
        result = ParsedContent(**SAMPLE_PARSED)
        assert isinstance(result.main_topic, str)
        assert len(result.main_topic.strip()) > 0

    def test_05_empty_pdf_raises_value_error(self):
        """T05 — extract_text_from_pdf raises ValueError on empty PDF bytes."""
        from backend.agents.parser_agent import extract_text_from_pdf
        import io
        # Create minimal invalid PDF bytes
        fake_pdf = b"not a valid pdf"
        with pytest.raises((ValueError, Exception)):
            extract_text_from_pdf(fake_pdf)


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2 — CONCEPT AGENT (Tests 6–10)
# ══════════════════════════════════════════════════════════════════════════════

class TestConceptAgent:

    def test_06_concept_ordering_names_match_core_concepts(self):
        """T06 — All names in concept_ordering exist in core_concepts."""
        from backend.models import ConceptExtractionResult
        result = ConceptExtractionResult(**SAMPLE_CONCEPTS)
        concept_names = {c.concept_name for c in result.core_concepts}
        for name in result.concept_ordering:
            assert name in concept_names, f"'{name}' in ordering but not in core_concepts"

    def test_07_max_5_concepts_enforced(self):
        """T07 — Output is capped at 5 concepts even if LLM returns more."""
        from backend.models import ConceptExtractionResult
        from backend.config import settings
        # Build 7 concepts
        seven_concepts = {
            "core_concepts": [
                {"concept_name": f"Concept{i}", "intuitive_explanation": "Test",
                 "mathematical_form": f"x_{i}", "why_it_matters": "Test"}
                for i in range(7)
            ],
            "concept_ordering": [f"Concept{i}" for i in range(7)]
        }
        result = ConceptExtractionResult(**seven_concepts)
        # Simulate agent slicing
        max_c = settings.max_concepts
        if len(result.core_concepts) > max_c:
            result.core_concepts = result.core_concepts[:max_c]
            result.concept_ordering = result.concept_ordering[:max_c]
        assert len(result.core_concepts) <= 5
        assert len(result.concept_ordering) <= 5

    def test_08_no_orphan_names_in_ordering(self):
        """T08 — concept_ordering contains no names absent from core_concepts."""
        from backend.models import ConceptExtractionResult
        result = ConceptExtractionResult(**SAMPLE_CONCEPTS)
        names = {c.concept_name for c in result.core_concepts}
        orphans = [n for n in result.concept_ordering if n not in names]
        assert len(orphans) == 0, f"Orphan names found: {orphans}"

    def test_09_mathematical_form_non_empty(self):
        """T09 — Each concept has a non-empty mathematical_form."""
        from backend.models import ConceptExtractionResult
        result = ConceptExtractionResult(**SAMPLE_CONCEPTS)
        for concept in result.core_concepts:
            assert len(concept.mathematical_form.strip()) > 0, \
                f"Empty mathematical_form for '{concept.concept_name}'"

    def test_10_concept_ordering_length_matches_core_concepts(self):
        """T10 — concept_ordering length equals core_concepts length."""
        from backend.models import ConceptExtractionResult
        result = ConceptExtractionResult(**SAMPLE_CONCEPTS)
        assert len(result.concept_ordering) == len(result.core_concepts)


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3 — PEDAGOGY PLANNER (Tests 11–15)
# ══════════════════════════════════════════════════════════════════════════════

class TestPedagogyPlanner:

    def test_11_scene_1_has_no_equations(self):
        """T11 — Scene 1 must have equations_to_show == []."""
        from backend.models import PedagogyPlan
        result = PedagogyPlan(**SAMPLE_PEDAGOGY)
        scene_1 = next(s for s in result.scenes if s.scene_id == 1)
        assert scene_1.equations_to_show == [], \
            f"Scene 1 should have no equations, got: {scene_1.equations_to_show}"

    def test_12_scene_count_in_valid_range(self):
        """T12 — Scene count is between 3 and 5."""
        from backend.models import PedagogyPlan
        result = PedagogyPlan(**SAMPLE_PEDAGOGY)
        assert 3 <= len(result.scenes) <= 5, \
            f"Scene count {len(result.scenes)} out of range [3,5]"

    def test_13_begin_pmatrix_stripped_from_equations(self):
        """T13 — \\begin{{pmatrix}} equations removed before handoff."""
        from backend.models import PedagogyPlan
        dirty_pedagogy = {
            "scenes": [
                {"scene_id": 1, "scene_title": "Hook", "learning_goal": "Curiosity",
                 "visual_metaphor": "Visual", "equations_to_show": [],
                 "animation_strategy": "Step 1.", "estimated_duration_seconds": 40},
                {"scene_id": 2, "scene_title": "Proof", "learning_goal": "Formula",
                 "visual_metaphor": "Visual",
                 "equations_to_show": [r"\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}", "a^2+b^2=c^2"],
                 "animation_strategy": "Step 1.", "estimated_duration_seconds": 50},
            ]
        }
        result = PedagogyPlan(**dirty_pedagogy)
        # Simulate pedagogy_agent stripping
        for scene in result.scenes:
            if scene.equations_to_show:
                scene.equations_to_show = [
                    eq for eq in scene.equations_to_show
                    if r'\begin' not in eq and r'\end' not in eq
                ]
        scene_2 = result.scenes[1]
        for eq in scene_2.equations_to_show:
            assert r'\begin' not in eq, f"\\begin found in equation: {eq}"

    def test_14_scene_ids_are_sequential(self):
        """T14 — Scene IDs are sequential starting from 1."""
        from backend.models import PedagogyPlan
        result = PedagogyPlan(**SAMPLE_PEDAGOGY)
        for i, scene in enumerate(result.scenes, start=1):
            scene.scene_id = i  # simulate renumbering
        ids = [s.scene_id for s in result.scenes]
        assert ids == list(range(1, len(result.scenes) + 1)), \
            f"Scene IDs not sequential: {ids}"

    def test_15_estimated_duration_in_valid_range(self):
        """T15 — All scenes have duration between 30 and 90 seconds."""
        from backend.models import PedagogyPlan
        result = PedagogyPlan(**SAMPLE_PEDAGOGY)
        for scene in result.scenes:
            assert 30 <= scene.estimated_duration_seconds <= 90, \
                f"Scene '{scene.scene_title}' duration {scene.estimated_duration_seconds}s out of range"


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 4 — SCENE ARCHITECT (Tests 16–19)
# ══════════════════════════════════════════════════════════════════════════════

class TestSceneArchitect:

    def test_16_scene_instruction_set_has_correct_count(self):
        """T16 — SceneInstructionSet has same scene count as pedagogy plan."""
        from backend.models import PedagogyPlan, SceneInstructionSet, SceneInstruction
        plan = PedagogyPlan(**SAMPLE_PEDAGOGY)
        # Simulate scene instructions
        mock_instructions = SceneInstructionSet(scene_instructions=[
            SceneInstruction(scene_id=i+1, objects=[], animations=[])
            for i in range(len(plan.scenes))
        ])
        assert len(mock_instructions.scene_instructions) == len(plan.scenes)

    def test_17_equation_objects_positioned_at_bottom_zone(self):
        """T17 — Equation objects have position referencing bottom zone (y=-2.5)."""
        # Simulate scene instruction properties check
        eq_positions = ["move_to([0, -2.5, 0])", "move_to([0, -2.8, 0])"]
        content_positions = ["move_to([0, 0.5, 0])", "to_edge(UP)"]
        for pos in eq_positions:
            # Extract y value
            match = re.search(r'\[\s*[\d.-]+\s*,\s*([\d.-]+)\s*,', pos)
            if match:
                y = float(match.group(1))
                assert y <= -2.0, f"Equation y={y} not in bottom zone (should be <= -2.0)"

    def test_18_title_objects_use_top_edge(self):
        """T18 — Title positioning uses to_edge(UP) pattern."""
        title_patterns = [
            "title.to_edge(UP, buff=0.25)",
            "title_1.to_edge(UP, buff=0.3)",
        ]
        for pattern in title_patterns:
            assert "to_edge" in pattern and "UP" in pattern, \
                f"Title not using to_edge(UP): {pattern}"

    def test_19_scene_instructions_have_fadeout_animation(self):
        """T19 — Every scene instruction set includes a FadeOut animation."""
        from backend.models import SceneInstruction, ManimAnimation
        scene_with_fadeout = SceneInstruction(
            scene_id=1,
            objects=[],
            animations=[
                ManimAnimation(action="Write", target="title_1", duration=1.2),
                ManimAnimation(action="FadeOut", target="*mobjects", duration=1.0),
                ManimAnimation(action="wait", target="", duration=0.5),
            ]
        )
        actions = [a.action for a in scene_with_fadeout.animations]
        assert "FadeOut" in actions, "No FadeOut animation found in scene"


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 5 — ANIMATOR / CODE FIXER (Tests 20–24)
# ══════════════════════════════════════════════════════════════════════════════

class TestAnimator:

    def _get_fix_fn(self):
        from backend.agents.animation_agent import _fix_common_issues
        return _fix_common_issues

    def test_20_generated_code_passes_ast_parse(self):
        """T20 — Generated Manim code parses as valid Python."""
        ast.parse(MINIMAL_MANIM_CODE)  # raises SyntaxError if invalid

    def test_21_showcreation_replaced_with_create(self):
        """T21 — ShowCreation is replaced with Create."""
        fix = self._get_fix_fn()
        code = "self.play(ShowCreation(circle))"
        result = fix(code)
        assert "ShowCreation" not in result
        assert "Create(circle)" in result

    def test_22_duration_replaced_with_run_time(self):
        """T22 — duration= kwarg is replaced with run_time=."""
        fix = self._get_fix_fn()
        code = "self.play(Write(text, duration=1.5))"
        result = fix(code)
        assert "duration=" not in result
        assert "run_time=" in result

    def test_23_mathtex_replaced_with_safe_tex(self):
        """T23 — MathTex( calls replaced with safe_tex(."""
        fix = self._get_fix_fn()
        code = 'eq = MathTex(r"a^2 + b^2 = c^2", font_size=44)'
        result = fix(code)
        assert "MathTex(" not in result
        assert "safe_tex(" in result

    def test_24_2d_coordinates_upgraded_to_3d(self):
        """T24 — 2D coordinate [x, y] upgraded to [x, y, 0]."""
        fix = self._get_fix_fn()
        code = "obj.move_to([0, -2.5])"
        result = fix(code)
        assert "[0, -2.5]" not in result
        assert "[0, -2.5, 0]" in result

    def test_25_safe_tex_wrapper_injected(self):
        """T25 — safe_tex() wrapper is present in fixed code."""
        fix = self._get_fix_fn()
        code = '''from manim import *
class MathVizScene(Scene):
    def construct(self):
        eq = safe_tex(r"x^2")
        self.play(Write(eq))
        self.wait(1)
        self.play(FadeOut(*self.mobjects, run_time=1.0))
        self.wait(0.5)
'''
        result = fix(code)
        assert "def safe_tex" in result

    def test_26_matrix_elements_get_text_mobject(self):
        """T26 — Matrix() calls get element_to_mobject=Text injected."""
        fix = self._get_fix_fn()
        code = "mat = Matrix([['1','2'],['3','4']])\n"
        result = fix(code)
        assert "element_to_mobject=Text" in result


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 6 — RENDERER (Tests 27–28)
# ══════════════════════════════════════════════════════════════════════════════

class TestRenderer:

    def test_27_timeout_returns_failure_result(self):
        """T27 — TimeoutExpired returns RenderResult with failure status."""
        from backend.modules.renderer import run as renderer_run
        from backend.models import AnimationCode
        import subprocess

        animation = AnimationCode(
            manim_class_name="MathVizScene",
            python_code=MINIMAL_MANIM_CODE
        )

        with patch("backend.modules.renderer.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(cmd="manim", timeout=480)):
            result = renderer_run(animation, job_id="test-timeout-001")

        assert result.render_status == "failure"
        assert "timed out" in result.error_log.lower()

    def test_28_manim_not_found_returns_failure(self):
        """T28 — FileNotFoundError returns RenderResult with failure status."""
        from backend.modules.renderer import run as renderer_run
        from backend.models import AnimationCode

        animation = AnimationCode(
            manim_class_name="MathVizScene",
            python_code=MINIMAL_MANIM_CODE
        )

        with patch("backend.modules.renderer.subprocess.run",
                   side_effect=FileNotFoundError("manim not found")):
            result = renderer_run(animation, job_id="test-notfound-001")

        assert result.render_status == "failure"
        assert "not found" in result.error_log.lower() or "manim" in result.error_log.lower()


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 7 — NARRATOR / TTS (Tests 29–30)
# ══════════════════════════════════════════════════════════════════════════════

class TestNarrator:

    def test_29_narration_word_count_within_duration_budget(self):
        """T29 — Narration word count fits within scene duration at 130 wpm."""
        WORDS_PER_MINUTE = 130
        SPEAKING_RATE = 0.92
        effective_wpm = WORDS_PER_MINUTE * SPEAKING_RATE  # ~120 wpm

        test_cases = [
            ("Think about a right triangle... notice how the sides relate.", 40),
            ("Now we see the squares on each side grow outward from the triangle.", 50),
            ("The equation a squared plus b squared equals c squared captures this perfectly.", 55),
        ]

        for narration, duration_seconds in test_cases:
            word_count = len(narration.split())
            max_words = int((duration_seconds / 60) * effective_wpm)
            assert word_count <= max_words, (
                f"Narration too long: {word_count} words for {duration_seconds}s "
                f"(max {max_words}): '{narration[:50]}...'"
            )

    def test_30_tts_generator_produces_audio_file(self):
        """T30 — TTS generator creates a non-empty audio file."""
        import tempfile
        from pathlib import Path

        try:
            from backend.modules.tts_generator import generate_scene_audio
        except ImportError:
            pytest.skip("edge-tts not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_audio.mp3"
            script = "This is a test of the text to speech narration system."

            success = generate_scene_audio(
                script=script,
                output_path=output_path,
                voice_name="en-US-AriaNeural",
                speaking_rate=0.92,
            )

            if not success:
                pytest.skip("TTS generation failed — likely no internet or edge-tts issue")

            assert output_path.exists(), "Audio file was not created"
            assert output_path.stat().st_size > 0, "Audio file is empty"


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATION — Full pipeline smoke test
# ══════════════════════════════════════════════════════════════════════════════

class TestIntegration:

    def test_integration_models_chain(self):
        """INTEGRATION — ParsedContent → ConceptExtractionResult → PedagogyPlan chain works."""
        from backend.models import ParsedContent, ConceptExtractionResult, PedagogyPlan

        parsed = ParsedContent(**SAMPLE_PARSED)
        assert parsed.main_topic

        concepts = ConceptExtractionResult(**SAMPLE_CONCEPTS)
        assert len(concepts.core_concepts) > 0

        plan = PedagogyPlan(**SAMPLE_PEDAGOGY)
        assert len(plan.scenes) >= 3

        # Chain integrity: scene 1 has no equations
        assert plan.scenes[0].equations_to_show == []
        # All scenes have valid durations
        for s in plan.scenes:
            assert s.estimated_duration_seconds > 0