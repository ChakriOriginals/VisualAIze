from __future__ import annotations
import ast
import logging
import re
from backend.llm_client import llm_call
from backend.models import AnimationCode, PedagogyPlan, SceneInstructionSet
from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = r"""
You are a senior Manim engineer producing broadcast-quality math education videos.
Every line of code you write must be correct, clean, and render without errors.

════════════════════════════════════════════════════════════════
ABSOLUTE SCREEN LAYOUT — NEVER VIOLATE THESE ZONES
════════════════════════════════════════════════════════════════

Screen dimensions: 14.2 units wide × 8 units tall.
Origin (0,0,0) is the exact screen center.

ZONE MAP:
  TITLE ZONE   : y = 3.0 to 3.6  → title.to_edge(UP, buff=0.25), YELLOW, font_size=36
  CONTENT ZONE : y = -1.5 to 2.6 → all shapes, matrices, graphs
  EQUATION ZONE: y = -2.5         → one equation only, font_size=42
  CAPTION ZONE : y = -3.2         → plain English, font_size=24, GREY

RULES:
  title.to_edge(UP, buff=0.25)           — always
  equation.move_to([0, -2.5, 0])         — always
  caption.move_to([0, -3.2, 0])          — always
  Labels: obj.next_to(target, DIR, buff=0.2)  — never same coords
  Max 4 mobjects visible at once
  NEVER put equation above y = -2.0
  NEVER put content below y = -1.8

════════════════════════════════════════════════════════════════
SCENE ISOLATION — MANDATORY
════════════════════════════════════════════════════════════════

Every scene MUST end with these exact two lines:
  self.play(FadeOut(*self.mobjects, run_time=1.0))
  self.wait(0.5)

════════════════════════════════════════════════════════════════
LATEX — CRITICAL RULES
════════════════════════════════════════════════════════════════

ALWAYS use safe_tex() — NEVER raw MathTex().
ALWAYS use raw strings: safe_tex(r"a^2 + b^2 = c^2")
NEVER use \begin{} \end{} inside safe_tex — use Matrix() class instead.
NEVER use \text{} inside safe_tex.

SAFE patterns only:
  safe_tex(r"a^2 + b^2 = c^2", font_size=44)
  safe_tex(r"c_{ij} = \sum_{k=1}^{n} a_{ik} b_{kj}", font_size=38)
  safe_tex(r"A \cdot B = C", font_size=44)
  safe_tex(r"(A \cdot B) \cdot C = A \cdot (B \cdot C)", font_size=36)
  safe_tex(r"A \cdot B \neq B \cdot A", font_size=44)
  safe_tex(r"\frac{-b \pm \sqrt{b^2-4ac}}{2a}", font_size=40)

════════════════════════════════════════════════════════════════
MATRIX DISPLAY — USE Matrix() CLASS ONLY
════════════════════════════════════════════════════════════════

ALWAYS use string elements in Matrix() and Table():
  CORRECT: Matrix([["1","2"],["3","4"]], element_to_mobject_config={"font_size":36})
  WRONG:   Matrix([[1, 2], [3, 4]])   ← integers CRASH Manim

CORRECT matrix pattern:
  mat_A = Matrix([["1","2"],["3","4"]], element_to_mobject_config={"font_size":34})
  mat_A.move_to([-3.5, 0.5, 0])
  label_A = Text("A", font_size=30, color=BLUE).next_to(mat_A, UP, buff=0.2)
  self.play(Write(mat_A, run_time=1.5))
  self.play(Write(label_A, run_time=0.8))
  self.wait(1.0)

NEVER USE Table() class — it is unreliable. Use Matrix() instead.

════════════════════════════════════════════════════════════════
TIMING — MANDATORY MINIMUM WAITS
════════════════════════════════════════════════════════════════

  After Write(title)      → self.wait(1.0)
  After Write(matrix)     → self.wait(1.2)
  After Create(shape)     → self.wait(0.8)
  After Write(equation)   → self.wait(2.0)   ← NEVER skip
  After FadeIn(caption)   → self.wait(1.5)
  End of every scene      → self.wait(2.0) then FadeOut

════════════════════════════════════════════════════════════════
COMPLETE SCENE TEMPLATE
════════════════════════════════════════════════════════════════

  # ══ Scene N: Title ══
  title_N = Text("Scene Title", font_size=36, color=YELLOW)
  title_N.to_edge(UP, buff=0.25)
  self.play(Write(title_N, run_time=1.2))
  self.wait(1.0)

  # Main visual in CONTENT zone
  mat = Matrix([["a","b"],["c","d"]], element_to_mobject_config={"font_size":36})
  mat.move_to([0, 0.5, 0])
  self.play(Write(mat, run_time=1.5))
  self.wait(1.2)

  # Equation at EQUATION zone
  eq = safe_tex(r"A \cdot B = C", font_size=44)
  eq.move_to([0, -2.5, 0])
  self.play(Write(eq, run_time=2.0))
  self.wait(2.0)

  # Caption at CAPTION zone
  cap = Text("Plain English explanation", font_size=24, color=GREY)
  cap.move_to([0, -3.2, 0])
  self.play(FadeIn(cap, run_time=1.0))
  self.wait(1.5)

  # MANDATORY scene end
  self.play(FadeOut(*self.mobjects, run_time=1.0))
  self.wait(0.5)

════════════════════════════════════════════════════════════════
FORBIDDEN — WILL CRASH OR CAUSE ERRORS
════════════════════════════════════════════════════════════════

  Table([[1,2],[3,4]])          → CRASH — use Matrix([["1","2"],["3","4"]])
  Matrix([[1,2],[3,4]])         → CRASH — use string elements
  MathTex(...)                  → use safe_tex(r"...")
  safe_tex("...\sum...")        → CRASH — must be raw: safe_tex(r"...\sum...")
  \begin{pmatrix}               → use Matrix() class
  move_to([x, y])               → always [x, y, 0]
  duration=                     → always run_time=
  ShowCreation(                 → always Create(
  Skip FadeOut at scene end     → MANDATORY
"""

RESPONSE_FORMAT = """
Respond with JSON in EXACTLY this format:
{
  "manim_class_name": "MathVizScene",
  "python_code": "<complete python code as single string>"
}
"""

MATHTEX_SAFE_WRAPPER = '''
def safe_tex(latex_str, **kwargs):
    """Safe MathTex wrapper with automatic fallback to plain text."""
    import re as _re
    try:
        obj = MathTex(latex_str, **kwargs)
        return obj
    except Exception:
        clean = _re.sub(r'\\\\[a-zA-Z]+', ' ', latex_str)
        clean = _re.sub(r'[{}^_\\\\]', '', clean).strip()[:80]
        return Text(clean or "equation", font_size=kwargs.get("font_size", 36), color=WHITE)

'''


def _fix_table_and_matrix_integers(code: str) -> str:
    """
    Fix integer elements in Matrix() and Table() calls.
    Matrix([[1,2],[3,4]]) -> Matrix([["1","2"],["3","4"]])
    Also replace Table() with Matrix() entirely since Table is unreliable.
    """

    # First: replace Table(...) calls entirely with Matrix equivalents
    # Find Table( ... ) and convert to Matrix
    def replace_table(m):
        content = m.group(1)
        # Extract the data rows from the table
        # Convert to Matrix format with string elements
        data_match = re.search(r'\[\s*(\[.*?\](?:\s*,\s*\[.*?\])*)\s*\]', content, re.DOTALL)
        if data_match:
            rows_str = data_match.group(1)
            # Stringify all numbers
            rows_str = re.sub(r'\b(\d+(?:\.\d+)?)\b(?!\s*["\'])', r'"\1"', rows_str)
            return f'Matrix([{rows_str}], element_to_mobject_config={{"font_size": 32}}'
        return f'Matrix([["1","2"],["3","4"]], element_to_mobject_config={{"font_size": 32}}'

    code = re.sub(r'Table\((.*?)\)', replace_table, code, flags=re.DOTALL)

    # Second: fix integer elements in Matrix() calls
    def fix_matrix_call(m):
        prefix = m.group(1)  # "Matrix("
        content = m.group(2)  # everything inside outer brackets

        # Convert bare integers/floats to strings
        # But don't touch things already in quotes
        def stringify_number(mm):
            num = mm.group(1)
            # Check if already quoted (look at surrounding context)
            return f'"{num}"'

        # Only convert numbers that are NOT already inside quotes
        # Strategy: split on quoted strings, fix numbers in non-quoted parts
        parts = re.split(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', content)
        fixed_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 0:  # non-quoted part
                part = re.sub(r'\b(\d+(?:\.\d+)?)\b', stringify_number, part)
            fixed_parts.append(part)

        fixed_content = ''.join(fixed_parts)
        return f'{prefix}{fixed_content}'

    # Match Matrix( followed by [[ ... ]]
    code = re.sub(r'(Matrix\s*\(\s*)(\[[\s\S]*?\])\s*(?=[,)])',
                  fix_matrix_call, code)

    return code


def _fix_safe_tex_strings(code: str) -> str:
    def make_raw(m):
        full = m.group(0)
        func = m.group(1)   # safe_tex or MathTex
        quote = m.group(2)  # " or '
        content = m.group(3)  # string content

        # Only add r prefix if contains backslash and not already raw
        if '\\' in content and not full.startswith(f'{func}(r'):
            return f'{func}(r{quote}{content}{quote}'
        return full

    # Fix safe_tex("...") and safe_tex('...')
    code = re.sub(
        r'(safe_tex|MathTex)\(\s*(["\'])((?:(?!\2).)*?)\2',
        make_raw,
        code
    )
    return code


def _fix_common_issues(code: str) -> str:

    # 1. Strip markdown fences
    code = re.sub(r"```python\s*", "", code)
    code = re.sub(r"```\s*", "", code)

    # 2. Ensure correct imports
    if "from manim import" not in code:
        code = "from manim import *\nimport numpy as np\nimport re\nimport os\n\n" + code
    if "import numpy" not in code:
        code = code.replace("from manim import *", "from manim import *\nimport numpy as np")
    if "import re\n" not in code:
        code = code.replace("from manim import *", "from manim import *\nimport re")
    if "import os\n" not in code:
        code = code.replace("from manim import *", "from manim import *\nimport os")

    # 3. Add MiKTeX to PATH at top of file (before class definition)
    miktex_fix = '''
# Auto-add MiKTeX to PATH
import os as _os
_miktex = r"C:\\Users\\saich\\AppData\\Local\\Programs\\MiKTeX\\miktex\\bin\\x64"
if _os.path.exists(_miktex) and _miktex not in _os.environ.get("PATH",""):
    _os.environ["PATH"] = _miktex + ";" + _os.environ.get("PATH","")

'''
    if '_miktex' not in code:
        # Insert after imports, before class
        match = re.search(r'\nclass\s+\w+\s*\(\s*Scene\s*\)', code)
        if match:
            code = code[:match.start()] + '\n' + miktex_fix + code[match.start():]

    # 4. Fix deprecated API
    code = code.replace("ShowCreation(", "Create(")

    # 5. Fix duration= -> run_time=
    code = re.sub(r',\s*duration=([0-9.]+)', r', run_time=\1', code)

    # 6. Fix undefined colors
    color_fixes = {
        'CYAN': 'TEAL', 'MAGENTA': 'PINK', 'BROWN': 'DARK_BROWN',
        'LIGHT_BLUE': 'BLUE_B', 'LIGHT_GREEN': 'GREEN_B', 'LIGHT_RED': 'RED_B',
        'DARK_RED': 'MAROON', 'LIME': 'GREEN_A', 'NAVY': 'DARK_BLUE',
        'VIOLET': 'PURPLE', 'SALMON': 'RED_B', 'INDIGO': 'PURPLE_B',
        'ORANGE_RED': 'RED_B',
    }
    for bad, good in color_fixes.items():
        code = re.sub(rf'\b{bad}\b(?!["\'])', good, code)

    # 7. Fix 2D coordinates -> 3D
    def fix_2d(m):
        prefix, x, y = m.group(1), m.group(2).strip(), m.group(3).strip()
        return f'{prefix}[{x}, {y}, 0]'
    for kw in ['point', 'start', 'end', 'arc_center']:
        code = re.sub(rf'(\b{kw}\s*=\s*)\[([^,\[\]]+),\s*([^,\[\]]+)\]', fix_2d, code)
    code = re.sub(r'(\.move_to\s*\()\[([^,\[\]]+),\s*([^,\[\]]+)\]',
                  lambda m: f'{m.group(1)}[{m.group(2).strip()}, {m.group(3).strip()}, 0]', code)
    code = re.sub(r'(\.shift\s*\()\[([^,\[\]]+),\s*([^,\[\]]+)\]',
                  lambda m: f'{m.group(1)}[{m.group(2).strip()}, {m.group(3).strip()}, 0]', code)

    # 8. Replace MathTex with safe_tex
    code = re.sub(r'\bMathTex\(', 'safe_tex(', code)

    # 9. Fix FadeOut without run_time
    code = re.sub(
        r'self\.play\(FadeOut\(\*self\.mobjects\)\)',
        'self.play(FadeOut(*self.mobjects, run_time=1.0))',
        code
    )

    # 10. Fix safe_tex strings -> raw strings
    def make_raw(m):
        func = m.group(1)
        quote = m.group(2)
        content = m.group(3)
        if '\\' in content:
            return f'{func}(r{quote}{content}{quote}'
        return m.group(0)
    code = re.sub(r'(safe_tex|MathTex)\(\s*(["\'])((?:(?!\2).)*?)\2', make_raw, code)

    # 11. CRITICAL: Fix ALL Matrix() calls to use element_to_mobject=Text
    # This prevents ANY LaTeX rendering inside matrices
    def fix_matrix(m):
        content = m.group(1)
        # Convert integer elements to strings
        def stringify(mm):
            return f'"{mm.group(1)}"'
        # Fix integers not already quoted
        parts = re.split(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', content)
        fixed_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                part = re.sub(r'\b(\d+(?:\.\d+)?)\b', stringify, part)
            fixed_parts.append(part)
        content = ''.join(fixed_parts)

        # Remove any existing element_to_mobject setting
        content = re.sub(r',?\s*element_to_mobject\s*=\s*\w+', '', content)
        content = re.sub(r',?\s*element_to_mobject_config\s*=\s*\{[^}]*\}', '', content)

        # Strip trailing comma/whitespace
        content = content.strip().rstrip(',').strip()

        return f'Matrix({content}, element_to_mobject=Text, element_to_mobject_config={{"font_size": 34}})'

    code = re.sub(r'Matrix\(([\s\S]*?)\)(?=\s*[\n\.,; )])', fix_matrix, code)

    # 12. Replace Table() with Matrix() (Table is unreliable)
    def replace_table(m):
        content = m.group(1)
        data_match = re.search(r'(\[(?:\[.*?\](?:,\s*)?)+\])', content, re.DOTALL)
        if data_match:
            rows = data_match.group(1)
            rows = re.sub(r'\b(\d+(?:\.\d+)?)\b(?!\s*["\'])', r'"\1"', rows)
            return f'Matrix({rows}, element_to_mobject=Text, element_to_mobject_config={{"font_size": 32}}'
        return f'Matrix([["1","2"],["3","4"]], element_to_mobject=Text, element_to_mobject_config={{"font_size": 32}}'
    code = re.sub(r'Table\(([\s\S]*?)\)(?=\s*[\n\.,; )])', replace_table, code)

    # 13. Fix duplicate kwargs
    def dedup_kwargs(line):
        keys_found = []
        def replacer(m):
            key = m.group(1)
            if key in ('True', 'False', 'None') or key[0].isupper():
                return m.group(0)
            if key in keys_found:
                return ''
            keys_found.append(key)
            return m.group(0)
        line = re.sub(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^,=()]+)(?=\s*,|\s*\))', replacer, line)
        line = re.sub(r',\s*,', ',', line)
        line = re.sub(r',\s*\)', ')', line)
        return line
    code = '\n'.join(dedup_kwargs(line) for line in code.split('\n'))

    # 14. Inject safe_tex wrapper before class definition
    if 'def safe_tex' not in code:
        match = re.search(r'class\s+\w+\s*\(\s*Scene\s*\)', code)
        if match:
            code = code[:match.start()] + MATHTEX_SAFE_WRAPPER + code[match.start():]

    # 15. Syntax check — fallback to safe scene if broken
    try:
        ast.parse(code)
    except SyntaxError as e:
        logger.error("Syntax error after all fixes, using fallback: %s", e)
        code = r'''from manim import *
import numpy as np
import re
import os

_miktex = r"C:\Users\saich\AppData\Local\Programs\MiKTeX\miktex\bin\x64"
if os.path.exists(_miktex):
    os.environ["PATH"] = _miktex + ";" + os.environ.get("PATH", "")


def safe_tex(latex_str, **kwargs):
    try:
        return MathTex(latex_str, **kwargs)
    except Exception:
        import re as _re
        clean = _re.sub(r'\\[a-zA-Z]+', '', latex_str)
        clean = _re.sub(r'[{}^_]', '', clean).strip()[:60]
        return Text(clean or "equation", font_size=kwargs.get("font_size", 36))


class MathVizScene(Scene):
    def construct(self):
        title = Text("Math Visualization", font_size=40, color=YELLOW)
        title.to_edge(UP, buff=0.25)
        self.play(Write(title, run_time=1.5))
        self.wait(1.0)
        msg = Text("Animation could not be generated.\nPlease try again.", font_size=32)
        msg.move_to(ORIGIN)
        self.play(FadeIn(msg, run_time=1.0))
        self.wait(3.0)
'''
    return code

def _syntax_check(code: str):
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as exc:
        return False, str(exc)


def run(scene_instructions: SceneInstructionSet, plan: PedagogyPlan) -> AnimationCode:

    # RAG: retrieve relevant Manim code examples
    manim_context = ""
    try:
        from backend.rag.manim_retriever import retrieve_for_scene, format_manim_context, ingest_manim_examples
        ingest_manim_examples()
        topic = plan.scenes[0].scene_title if plan.scenes else "math"
        scene_titles = [s.scene_title for s in plan.scenes]
        docs = retrieve_for_scene(scene_titles, topic, n_results=5)
        manim_context = format_manim_context(docs, max_chars=1500)
        logger.info("Manim RAG: retrieved %d examples", len(docs))
    except Exception as e:
        logger.warning("Manim RAG failed, continuing without: %s", e)

    # Build scene context
    context_parts = []
    for instr in scene_instructions.scene_instructions:
        plan_scene = next((s for s in plan.scenes if s.scene_id == instr.scene_id), None)
        title = plan_scene.scene_title if plan_scene else f"Scene {instr.scene_id}"
        goal = plan_scene.learning_goal if plan_scene else ""
        visual_metaphor = plan_scene.visual_metaphor if plan_scene else ""
        animation_strategy = plan_scene.animation_strategy if plan_scene else ""
        equations = plan_scene.equations_to_show if plan_scene else []
        duration = plan_scene.estimated_duration_seconds if plan_scene else 40

        objects_desc = "\n".join(
            f"  - {o.obj_id} ({o.obj_type}): {o.properties}"
            for o in instr.objects
        )
        anims_desc = "\n".join(
            f"  - {a.action}({a.target}, run_time={a.duration})"
            for a in instr.animations
        )

        # Clean equations: remove \begin{} patterns
        clean_equations = []
        for eq in equations:
            if r'\begin' in eq:
                clean_equations.append("NOTE: Use Matrix() class — NOT LaTeX environments")
            else:
                clean_equations.append(eq)
        eq_str = "\n".join(f"  - {e}" for e in clean_equations) if clean_equations else "  (none)"

        context_parts.append(
            f"═══ Scene {instr.scene_id}: {title} ═══\n"
            f"Goal: {goal}\n"
            f"Visual: {visual_metaphor}\n"
            f"Strategy: {animation_strategy[:150]}\n"
            f"Equations (raw strings, NO \\begin{{}}): \n{eq_str}\n"
            f"Duration: ~{duration}s\n"
            f"Objects:\n{objects_desc}\n"
            f"Animations:\n{anims_desc}"
        )

    rag_section = (
        f"\n\nMANIM CODE EXAMPLES (adapt — do not copy blindly):\n{manim_context}\n"
        if manim_context else ""
    )

    user_prompt = (
        "Generate a SIMPLE, SHORT Manim animation. Max 100 lines of code total.\n"
        "Max 3 objects per scene. Keep animations fast (run_time under 2.0).\n"
        "CRITICAL — these will CRASH if wrong:\n"
        "1. Every scene ends with: self.play(FadeOut(*self.mobjects, run_time=1.0)); self.wait(0.5)\n"
        "2. Matrix elements MUST be strings with element_to_mobject=Text\n"
        "3. safe_tex MUST use raw strings: safe_tex(r\"equation\")\n"
        "4. NEVER use Table() — use Matrix() only\n"
        "5. All equations at move_to([0, -2.5, 0])\n"
        "6. Max 2.0 run_time per animation\n"
        f"{rag_section}"
        "\n\nSCENES:\n\n"
        + "\n\n".join(context_parts)
    )

    result = llm_call(
        system_prompt=SYSTEM_PROMPT + RESPONSE_FORMAT,
        user_prompt=user_prompt,
        response_model=AnimationCode,
        max_retries=2,
        max_tokens=2000
    )

    result.python_code = _fix_common_issues(result.python_code)

    valid, err = _syntax_check(result.python_code)
    if not valid:
        raise ValueError(f"Generated Manim code has a syntax error: {err}")

    lines = len(result.python_code.strip().splitlines())
    logger.info("Animation code generated: class=%s, lines=%d", result.manim_class_name, lines)
    return result