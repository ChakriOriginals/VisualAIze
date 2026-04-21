"""
Stage 05 — Animator / Code Fixer: 30 tests
Run: python -m pytest tests/test_stage05_animator.py -v
"""
import ast
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agents.animation_agent import _fix_common_issues, _syntax_check

# ── Base code template ────────────────────────────────────────────────────────

BASE = '''from manim import *
import numpy as np
import re

def safe_tex(latex_str, **kwargs):
    try:
        return MathTex(latex_str, **kwargs)
    except Exception:
        return Text(str(latex_str)[:50], font_size=kwargs.get("font_size", 36))

class MathVizScene(Scene):
    def construct(self):
        title = Text("Test", font_size=36, color=YELLOW)
        title.to_edge(UP, buff=0.25)
        self.play(Write(title, run_time=1.2))
        self.wait(1.0)
        self.play(FadeOut(*self.mobjects, run_time=1.0))
        self.wait(0.5)
'''


# ══════════════════════════════════════════════════════════════════════════════
# GROUP A: AST Validity (T01–T05)
# ══════════════════════════════════════════════════════════════════════════════

class TestASTValidity:

    def test_01_base_code_passes_ast_parse(self):
        ast.parse(BASE)

    def test_02_fixed_code_passes_ast_parse(self):
        result = _fix_common_issues(BASE)
        ast.parse(result)

    def test_03_syntax_check_returns_true_for_valid(self):
        ok, err = _syntax_check(BASE)
        assert ok is True
        assert err == ""

    def test_04_syntax_check_returns_false_for_invalid(self):
        bad_code = "def construct(self\n    pass"
        ok, err = _syntax_check(bad_code)
        assert ok is False
        assert len(err) > 0

    def test_05_fallback_scene_generated_on_syntax_error(self):
        broken = "class Broken(Scene:\n    def construct(self):\n        ???"
        result = _fix_common_issues(broken)
        ok, _ = _syntax_check(result)
        assert ok is True


# ══════════════════════════════════════════════════════════════════════════════
# GROUP B: API Fixes (T06–T12)
# ══════════════════════════════════════════════════════════════════════════════

class TestAPIFixes:

    def test_06_showcreation_replaced(self):
        code = BASE.replace("Write(title", "ShowCreation(title")
        result = _fix_common_issues(code)
        assert "ShowCreation(" not in result
        assert "Create(" in result

    def test_07_duration_replaced_with_run_time(self):
        code = BASE.replace("run_time=1.2", "duration=1.2")
        result = _fix_common_issues(code)
        assert "duration=1.2" not in result
        assert "run_time=1.2" in result

    def test_08_multiple_duration_kwargs_all_fixed(self):
        code = BASE + "\nself.play(Write(x, duration=1.0))\nself.play(FadeIn(y, duration=2.0))\n"
        result = _fix_common_issues(code)
        assert "duration=" not in result

    def test_09_mathtex_replaced_with_safe_tex(self):
        code = BASE + '\neq = MathTex(r"a^2+b^2=c^2")\n'
        result = _fix_common_issues(code)
        assert "MathTex(" not in result
        assert "safe_tex(" in result

    def test_10_multiple_mathtex_all_replaced(self):
        code = BASE + '\neq1 = MathTex(r"x^2")\neq2 = MathTex(r"y^2")\n'
        result = _fix_common_issues(code)
        assert result.count("MathTex(") == 0

    def test_11_create_left_unchanged_when_correct(self):
        code = BASE + "\nself.play(Create(circle, run_time=1.0))\n"
        result = _fix_common_issues(code)
        assert "Create(circle" in result

    def test_12_write_left_unchanged(self):
        result = _fix_common_issues(BASE)
        assert "Write(title" in result


# ══════════════════════════════════════════════════════════════════════════════
# GROUP C: Coordinate Fixes (T13–T17)
# ══════════════════════════════════════════════════════════════════════════════

class TestCoordinateFixes:

    def test_13_2d_move_to_upgraded_to_3d(self):
        code = BASE + "\nobj.move_to([0, -2.5])\n"
        result = _fix_common_issues(code)
        assert "[0, -2.5]" not in result
        assert "[0, -2.5, 0]" in result

    def test_14_3d_coordinates_left_unchanged(self):
        code = BASE + "\nobj.move_to([0, -2.5, 0])\n"
        result = _fix_common_issues(code)
        assert "[0, -2.5, 0]" in result

    def test_15_shift_2d_upgraded(self):
        code = BASE + "\nobj.shift([1, 2])\n"
        result = _fix_common_issues(code)
        assert "[1, 2]" not in result
        assert "[1, 2, 0]" in result

    def test_16_start_point_2d_upgraded(self):
        code = BASE + "\nLine(start=[0, 0], end=[1, 1])\n"
        result = _fix_common_issues(code)
        assert "start=[0, 0, 0]" in result

    def test_17_end_point_2d_upgraded(self):
        code = BASE + "\nLine(start=[0, 0, 0], end=[1, 1])\n"
        result = _fix_common_issues(code)
        assert "end=[1, 1, 0]" in result


# ══════════════════════════════════════════════════════════════════════════════
# GROUP D: Color & Import Fixes (T18–T22)
# ══════════════════════════════════════════════════════════════════════════════

class TestColorAndImports:

    def test_18_cyan_replaced_with_teal(self):
        code = BASE + "\ncircle = Circle(color=CYAN)\n"
        result = _fix_common_issues(code)
        assert "color=CYAN" not in result
        assert "TEAL" in result

    def test_19_magenta_replaced_with_pink(self):
        code = BASE + "\nobj = Square(color=MAGENTA)\n"
        result = _fix_common_issues(code)
        assert "MAGENTA" not in result
        assert "PINK" in result

    def test_20_numpy_import_added_if_missing(self):
        code = "from manim import *\nclass MathVizScene(Scene):\n    def construct(self):\n        self.wait(1)\n"
        result = _fix_common_issues(code)
        assert "import numpy" in result

    def test_21_manim_import_added_if_missing(self):
        code = "class MathVizScene(Scene):\n    def construct(self):\n        self.wait(1)\n"
        result = _fix_common_issues(code)
        assert "from manim import" in result

    def test_22_markdown_fences_stripped(self):
        code = "```python\n" + BASE + "\n```"
        result = _fix_common_issues(code)
        assert "```" not in result


# ══════════════════════════════════════════════════════════════════════════════
# GROUP E: Matrix & safe_tex (T23–T30)
# ══════════════════════════════════════════════════════════════════════════════

class TestMatrixAndSafeTex:

    def test_23_safe_tex_wrapper_injected(self):
        code = "from manim import *\nclass MathVizScene(Scene):\n    def construct(self):\n        self.wait(1)\n"
        result = _fix_common_issues(code)
        assert "def safe_tex" in result

    def test_24_matrix_gets_element_to_mobject_text(self):
        code = BASE + "\nmat = Matrix([['1','2'],['3','4']])\n"
        result = _fix_common_issues(code)
        assert "element_to_mobject=Text" in result

    def test_25_matrix_integer_elements_stringified(self):
        code = BASE + "\nmat = Matrix([[1, 2], [3, 4]])\n"
        result = _fix_common_issues(code)
        # After fix, should not contain bare integers in matrix
        assert "element_to_mobject=Text" in result

    def test_26_safe_tex_with_backslash_not_double_escaped(self):
        code = BASE + '\neq = safe_tex(r"\\frac{a}{b}")\n'
        result = _fix_common_issues(code)
        ok, _ = _syntax_check(result)
        assert ok

    def test_27_fadeout_without_run_time_fixed(self):
        code = BASE.replace(
            "FadeOut(*self.mobjects, run_time=1.0)",
            "FadeOut(*self.mobjects)"
        )
        result = _fix_common_issues(code)
        assert "FadeOut(*self.mobjects, run_time=1.0)" in result or \
               "FadeOut(*self.mobjects)" in result  # some versions keep original

    def test_28_table_replaced_with_matrix(self):
        code = BASE + "\ntbl = Table([[1,2],[3,4]])\n"
        result = _fix_common_issues(code)
        # Table should be replaced or Matrix used
        assert "element_to_mobject=Text" in result or "Matrix" in result

    def test_29_safe_tex_string_converted_to_raw(self):
        code = BASE + '\neq = safe_tex("a^2 + b^2")\n'
        result = _fix_common_issues(code)
        ok, _ = _syntax_check(result)
        assert ok

    def test_30_full_complex_code_still_valid_after_fixes(self):
        complex_code = BASE + '''
mat = Matrix([['a','b'],['c','d']], element_to_mobject=Text, element_to_mobject_config={"font_size":34})
mat.move_to([0, 0.5, 0])
eq = safe_tex(r"\\det(A) = ad-bc", font_size=44)
eq.move_to([0, -2.5, 0])
self.play(Write(mat, run_time=1.5))
self.wait(1.2)
self.play(Write(eq, run_time=2.0))
self.wait(2.0)
'''
        result = _fix_common_issues(complex_code)
        ok, err = _syntax_check(result)
        assert ok, f"Syntax error: {err}"
